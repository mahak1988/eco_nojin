"""Internal, Docker-free supervisor for the Eco Nojin / HyDroMA runtime.

This module is the DP-2 replacement for Docker / container orchestration:

* no containers, no images, no registry and no compose files;
* the service map is plain data in ``runtime/services.yaml``;
* every service runs as a child process of this interpreter:
  ``python -m uvicorn <app> --host <host> --port <port> --workers <workers>``;
* per-service stdout/stderr is appended to ``data/logs/<name>.log``.

Storage tier
------------
The storage backend is selected through the ``HYDROMA_STORAGE_TIER`` environment
variable. That contract is documented here and enforced nowhere: the services
read the variable themselves, so the supervisor stays storage-agnostic and never
rewrites it.

CLI
---
    python -m runtime.supervise up
    python -m runtime.supervise status
    python -m runtime.supervise restart <name>
    python -m runtime.supervise down

Exit codes: 0 success, 1 runtime failure, 2 usage error.
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, TextIO

import yaml

DEFAULT_CONFIG_PATH: Path = Path(__file__).with_name("services.yaml")
DEFAULT_LOG_DIR: Path = Path(__file__).resolve().parent.parent / "data" / "logs"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_HEALTH_PATH = "/healthz"
DEFAULT_WORKERS = 1

#: Keys every entry must declare; everything else is defaulted (see ``_normalise``).
REQUIRED_KEYS: tuple[str, ...] = ("name", "app", "port")

HEALTH_TIMEOUT = 2.0
GRACEFUL_SHUTDOWN_TIMEOUT = 10.0
KILL_TIMEOUT = 5.0
#: How long a stopped child's port may keep answering before ``status``
#: reports the externally observed truth.
PORT_RELEASE_TIMEOUT = 5.0
#: A restarted service retries its bind while the OS finishes releasing the port.
START_RETRIES = 3
START_BACKOFF_SECONDS = 1.0
STATE_FILE_NAME = "runtime-state.json"


def _pid_alive(pid: int) -> bool:
    """Best-effort cross-platform liveness check (stdlib only)."""
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:  # exists, owned by someone else
        return True
    except OSError:
        pass
    try:  # Windows: os.kill cannot signal foreign processes
        result = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return str(pid) in result.stdout
    except (OSError, subprocess.SubprocessError):
        return False


def _kill_process_tree(pid: int) -> None:
    """Terminate a process tree; Windows needs taskkill for foreign PIDs."""
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return
    try:
        os.kill(pid, 15)
    except OSError:
        pass

EXIT_OK = 0
EXIT_FAILURE = 1
EXIT_USAGE = 2


def load_services(path: Path | str = DEFAULT_CONFIG_PATH) -> list[dict[str, Any]]:
    """Load and validate the service map.

    Returns normalised entries: every entry carries all keys with defaults
    filled in (``host``, ``workers``, ``health_path``, ``depends_on``,
    ``enabled``). Raises :class:`ValueError` with a message naming the file and
    the offending entry on any schema violation.
    """
    config_path = Path(path)
    if not config_path.is_file():
        raise ValueError(f"service map not found: {config_path}")
    try:
        document = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValueError(f"service map is not valid YAML ({config_path}): {exc}") from exc
    if not isinstance(document, dict):
        raise ValueError(f"service map must be a mapping with a 'services' list ({config_path})")
    raw_entries = document.get("services")
    if not isinstance(raw_entries, list) or not raw_entries:
        raise ValueError(f"service map must declare a non-empty 'services' list ({config_path})")

    services = [_normalise_entry(entry, index) for index, entry in enumerate(raw_entries)]
    _check_unique(services)
    for entry in services:
        _check_depends_on(entry, services)
    return services


def _normalise_entry(entry: Any, index: int) -> dict[str, Any]:
    """Validate one raw YAML entry and fill in the defaults."""
    label = f"services[{index}] in the runtime service map"
    if not isinstance(entry, dict):
        raise ValueError(f"{label} must be a mapping, got {type(entry).__name__}")
    missing = [key for key in REQUIRED_KEYS if entry.get(key) is None]
    if missing:
        raise ValueError(f"{label} is missing required key(s): {', '.join(missing)}")

    name = entry["name"]
    if not isinstance(name, str) or not name.strip():
        raise ValueError(f"{label}: 'name' must be a non-empty string")
    label = f"service '{name}'"

    app = entry["app"]
    if not isinstance(app, str) or app.count(":") != 1:
        raise ValueError(f"{label}: 'app' must be a 'module:attribute' import path, got {app!r}")
    module, attribute = app.split(":")
    if not module.strip() or not attribute.strip():
        raise ValueError(f"{label}: 'app' must be a 'module:attribute' import path, got {app!r}")

    port = entry["port"]
    if isinstance(port, bool) or not isinstance(port, int):
        raise ValueError(f"{label}: 'port' must be an integer, got {port!r}")
    if not 1 <= port <= 65535:
        raise ValueError(f"{label}: 'port' {port} is outside the range 1-65535")

    host = entry.get("host", DEFAULT_HOST)
    if not isinstance(host, str) or not host.strip():
        raise ValueError(f"{label}: 'host' must be a non-empty string, got {host!r}")

    workers = entry.get("workers", DEFAULT_WORKERS)
    if isinstance(workers, bool) or not isinstance(workers, int) or workers < 1:
        raise ValueError(f"{label}: 'workers' must be an integer >= 1, got {workers!r}")

    health_path = entry.get("health_path", DEFAULT_HEALTH_PATH)
    if not isinstance(health_path, str) or not health_path.startswith("/"):
        raise ValueError(f"{label}: 'health_path' must start with '/', got {health_path!r}")

    enabled = entry.get("enabled", True)
    if not isinstance(enabled, bool):
        raise ValueError(f"{label}: 'enabled' must be a boolean, got {enabled!r}")

    depends_on = entry.get("depends_on", [])
    if depends_on is None:
        depends_on = []
    if not isinstance(depends_on, list) or not all(
        isinstance(item, str) and item.strip() for item in depends_on
    ):
        raise ValueError(f"{label}: 'depends_on' must be a list of service names")

    return {
        "name": name,
        "app": app,
        "host": host,
        "port": port,
        "workers": workers,
        "health_path": health_path,
        "depends_on": list(depends_on),
        "enabled": enabled,
    }


def _check_unique(services: list[dict[str, Any]]) -> None:
    names: set[str] = set()
    ports: dict[int, str] = {}
    for entry in services:
        name = entry["name"]
        if name in names:
            raise ValueError(f"duplicate service name in the service map: {name}")
        names.add(name)
        port = entry["port"]
        if port in ports:
            raise ValueError(
                f"duplicate port {port} in the service map: "
                f"used by both '{ports[port]}' and '{name}'"
            )
        ports[port] = name


def _check_depends_on(entry: dict[str, Any], services: list[dict[str, Any]]) -> None:
    known = {item["name"] for item in services}
    for dep in entry["depends_on"]:
        if dep not in known:
            raise ValueError(
                f"service '{entry['name']}' depends on unknown service '{dep}' "
                f"(known: {', '.join(sorted(known))})"
            )


def order_services(services: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return the services start-ordered so ``depends_on`` targets come first."""
    by_name = {entry["name"]: entry for entry in services}
    ordered: list[dict[str, Any]] = []
    state: dict[str, int] = {}

    def visit(entry: dict[str, Any]) -> None:
        name = entry["name"]
        mark = state.get(name, 0)
        if mark == 2:
            return
        if mark == 1:
            raise ValueError(f"service '{name}' takes part in a circular depends_on chain")
        state[name] = 1
        for dep in entry["depends_on"]:
            visit(by_name[dep])
        state[name] = 2
        ordered.append(entry)

    for entry in services:
        visit(entry)
    return ordered


def _is_healthy(host: str, port: int, health_path: str, timeout: float = HEALTH_TIMEOUT) -> bool:
    """GET the health endpoint; any 2xx/3xx answer counts as healthy."""
    url = f"http://{host}:{port}{health_path}"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            status = response.getcode()
            response.read(64)
    except urllib.error.HTTPError as exc:
        status = exc.code
    except (urllib.error.URLError, OSError, ValueError):
        return False
    return 200 <= status < 400


class Supervisor:
    """Start, watch and stop the services declared in a runtime service map.

    ``status()`` returns one row per enabled service as a list of mappings with
    the ``name`` / ``pid`` / ``port`` / ``health`` columns, where ``health`` is
    ``healthy``, ``unhealthy`` or ``stopped``; :func:`render_status` prints that
    table.
    """

    def __init__(
        self,
        config_path: Path | str = DEFAULT_CONFIG_PATH,
        log_dir: Path | str | None = None,
        env: dict[str, str] | None = None,
        cwd: Path | str | None = None,
    ) -> None:
        self.config_path = Path(config_path)
        self.log_dir = Path(log_dir) if log_dir is not None else DEFAULT_LOG_DIR
        self.env = env
        self.cwd = Path(cwd) if cwd is not None else None
        self.services: list[dict[str, Any]] = load_services(self.config_path)
        self._processes: dict[str, subprocess.Popen] = {}
        self._log_files: dict[str, TextIO] = {}

    def up(self) -> list[str]:
        """Start every enabled service; returns the enabled service names.

        A service already running is left alone, so ``up`` is idempotent. A
        start that fails on a port still being released by the previous
        occupant (Windows keeps a stopped socket reachable briefly) is retried
        with a short backoff before giving up. Raises :class:`ValueError` on
        the first unrecoverable failure, naming the service and the port.
        """
        for entry in order_services(self.services):
            if not entry["enabled"]:
                continue
            running = self._processes.get(entry["name"])
            if running is not None and running.poll() is None:
                continue
            self._start_with_retry(entry)
        self._write_state()
        return [entry["name"] for entry in self.services if entry["enabled"]]

    def _start_with_retry(self, entry: dict[str, Any]) -> None:
        """Start one service, retrying while the port is being released."""
        last_error: ValueError | None = None
        for attempt in range(START_RETRIES + 1):
            try:
                self._assert_port_free(entry)
                self._start(entry)
                return
            except ValueError as exc:
                last_error = exc
                if attempt == START_RETRIES:
                    break
                time.sleep(START_BACKOFF_SECONDS)
        raise last_error  # type: ignore[misc]

    def restart(self, name: str) -> None:
        """Stop one service and start it again (no-op when it is disabled)."""
        entry = self.entry(name)
        self._stop(name)
        if entry["enabled"]:
            self._start_with_retry(entry)
            self._write_state()

    def entry(self, name: str) -> dict[str, Any]:
        """Return the (normalised) service map entry for ``name``."""
        for entry in self.services:
            if entry["name"] == name:
                return entry
        known = ", ".join(item["name"] for item in self.services)
        raise ValueError(f"unknown service '{name}' (known: {known})")

    def status(self) -> list[dict[str, Any]]:
        """Return the health table: one row per enabled service.

        Three sources, in order of authority: this process's child handles; then
        the state file written by an ``up`` in another process (whose PIDs are
        probed for liveness); then the port itself. ``managed`` says whether this
        process owns the child, ``external_pid`` whether another process does.
        """
        external = {row["name"]: row for row in self._read_state()}
        rows = []
        for entry in self.services:
            if not entry["enabled"]:
                continue
            process = self._processes.get(entry["name"])
            managed = process is not None and process.poll() is None
            external_pid = None
            if process is not None and process.poll() is not None:
                health = "stopped"
            elif managed:
                health = "healthy" if self._probe(entry) else "unhealthy"
            else:
                adopted = external.get(entry["name"])
                if adopted is not None and _pid_alive(int(adopted["pid"])):
                    external_pid = int(adopted["pid"])
                    health = "healthy" if self._probe(entry) else "unhealthy"
                elif self._probe(entry):
                    health = "healthy"
                else:
                    health = "stopped"
            rows.append(
                {
                    "name": entry["name"],
                    "pid": process.pid if managed else external_pid,
                    "port": entry["port"],
                    "health": health,
                    "managed": managed,
                }
            )
        return rows

    @staticmethod
    def _probe(entry: dict[str, Any]) -> bool:
        return _is_healthy(entry["host"], entry["port"], entry["health_path"])

    def _state_path(self) -> Path:
        return Path(self.log_dir) / STATE_FILE_NAME

    def _read_state(self) -> list[dict[str, Any]]:
        """Live entries from the state file (dead PIDs are dropped)."""
        path = self._state_path()
        if not path.is_file():
            return []
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        rows = []
        for row in payload.get("services", []):
            if _pid_alive(int(row.get("pid", 0))):
                rows.append(row)
        return rows

    def _write_state(self) -> None:
        path = self._state_path()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            services = []
            for entry in self.services:
                process = self._processes.get(entry["name"])
                if process is not None and process.poll() is None:
                    services.append(
                        {
                            "name": entry["name"],
                            "pid": int(process.pid),
                            "port": int(entry["port"]),
                            "host": entry["host"],
                        }
                    )
            path.write_text(
                json.dumps({"pid": os.getpid(), "services": services}, indent=2) + "\n",
                encoding="utf-8",
            )
        except OSError:  # a read-only log dir must not break the supervisor
            pass

    def down(self, force: bool = True) -> None:
        """Stop every running service: this process's children first, then the
        PIDs recorded in the state file by an earlier ``up`` in this or another
        process. The state file is cleared only when nothing is left running.
        """
        for entry in order_services(self.services):
            self._stop(entry["name"])
        for adopted in self._read_state():
            if self._processes.get(adopted["name"]) is not None:
                continue
            entry = self.entry(adopted["name"])
            _kill_process_tree(int(adopted["pid"]))
            deadline = time.monotonic() + PORT_RELEASE_TIMEOUT
            while time.monotonic() < deadline:
                if not self._probe(entry):
                    break
                time.sleep(0.05)
        if not any(
            self._processes.get(entry["name"]) is not None for entry in self.services
        ):
            try:
                self._state_path().unlink(missing_ok=True)
            except OSError:
                pass

    def _assert_port_free(self, entry: dict[str, Any]) -> None:
        """Fail fast, with the port named, when the bind address is taken.

        ``SO_REUSEADDR`` is set on the probe so closing it does not leave the
        address reserved: without it Windows keeps the port out of the child's
        reach and a legitimate restart fails with WinError 10048. A port that
        another socket is *listening* on is still reported as taken.
        """
        host = entry["host"]
        port = entry["port"]
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                probe.bind((host, port))
            except OSError as exc:
                raise ValueError(
                    f"service '{entry['name']}' cannot start: port {port} on {host} is "
                    f"already in use ({exc})"
                ) from exc

    def _start(self, entry: dict[str, Any]) -> None:
        name = entry["name"]
        command = [
            sys.executable,
            "-m",
            "uvicorn",
            entry["app"],
            "--host",
            entry["host"],
            "--port",
            str(entry["port"]),
            "--workers",
            str(entry["workers"]),
        ]
        self.log_dir.mkdir(parents=True, exist_ok=True)
        log_file = (self.log_dir / f"{name}.log").open("a", encoding="utf-8")
        try:
            process = subprocess.Popen(
                command,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                env=self.env,
                cwd=self.cwd,
            )
        except OSError as exc:
            log_file.close()
            raise ValueError(f"service '{name}' could not be started: {exc}") from exc
        self._processes[name] = process
        self._log_files[name] = log_file

    def _stop(self, name: str) -> None:
        """Stop one child and wait until its port stops answering.

        Terminating the process is not the same as the service being gone: the
        OS keeps the listening socket reachable for a moment afterwards, so a
        ``down`` immediately followed by a ``status`` (or a restart) would see
        the port still alive. After the process exits, the port is polled
        until it stops answering, bounded by :data:`PORT_RELEASE_TIMEOUT`.
        """
        entry = self.entry(name) if self._knows(name) else None
        process = self._processes.get(name)
        if process is None:
            self._release(name)
            return
        if process.poll() is None:
            process.terminate()
            try:
                # Graceful window: uvicorn drains its connections and exits.
                process.wait(timeout=GRACEFUL_SHUTDOWN_TIMEOUT)
            except subprocess.TimeoutExpired:
                process.kill()
                try:
                    process.wait(timeout=KILL_TIMEOUT)
                except subprocess.TimeoutExpired:
                    pass
        if entry is not None:
            deadline = time.monotonic() + PORT_RELEASE_TIMEOUT
            while time.monotonic() < deadline:
                if not self._probe(entry):
                    break
                time.sleep(0.05)
        self._release(name)

    def _knows(self, name: str) -> bool:
        return any(entry["name"] == name for entry in self.services)

    def _release(self, name: str) -> None:
        self._processes.pop(name, None)
        handle = self._log_files.pop(name, None)
        if handle is not None and not handle.closed:
            handle.close()


def render_status(rows: list[dict[str, Any]]) -> str:
    """Render :meth:`Supervisor.status` rows as a plain text table."""
    header = ("NAME", "PID", "PORT", "HEALTH")
    body = [
        (str(row["name"]), str(row["pid"]), str(row["port"]), str(row["health"]))
        for row in rows
    ]
    widths = []
    for column in range(len(header)):
        widest = len(header[column])
        for row in body:
            widest = max(widest, len(row[column]))
        widths.append(widest)

    def line(values: tuple[str, ...]) -> str:
        joined = "  ".join(
            values[column].ljust(widths[column]) for column in range(len(header))
        )
        return joined.rstrip()

    lines = [line(header)]
    lines.extend(line(row) for row in body)
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG_PATH),
        help="service map YAML (default: %(default)s)",
    )
    common.add_argument(
        "--log-dir",
        default=None,
        help="directory for per-service logs (default: data/logs)",
    )

    parser = argparse.ArgumentParser(
        prog="python -m runtime.supervise",
        description="Docker-free supervisor for the Eco Nojin / HyDroMA runtime.",
        parents=[common],
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("up", parents=[common], help="start every enabled service")
    subparsers.add_parser("down", parents=[common], help="stop every running service")
    subparsers.add_parser("status", parents=[common], help="print the health table")
    restart = subparsers.add_parser("restart", parents=[common], help="restart one service")
    restart.add_argument("name", help="service name from the service map")
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point; returns 0, 1 or 2 (see the module docstring)."""
    try:
        args = _build_parser().parse_args(argv)
    except SystemExit as exc:  # argparse usage errors exit with 2
        return EXIT_USAGE if exc.code is None else int(exc.code)

    try:
        supervisor = Supervisor(config_path=args.config, log_dir=args.log_dir)
    except ValueError as exc:
        print(f"error: {exc}")
        return EXIT_FAILURE

    try:
        if args.command == "up":
            names = supervisor.up()
            print(f"up: {len(names)} service(s) -> {', '.join(names) if names else 'none enabled'}")
            return EXIT_OK
        if args.command == "down":
            total = len(supervisor.status())
            supervisor.down()
            print(f"down: stopped {total} service(s)")
            return EXIT_OK
        if args.command == "restart":
            supervisor.restart(args.name)
            print(f"restart: {args.name}")
            return EXIT_OK
        rows = supervisor.status()
        print(render_status(rows))
        if not rows:
            print(f"error: no enabled services in {args.config}")
            return EXIT_USAGE
        unhealthy = [row["name"] for row in rows if row["health"] != "healthy"]
        if unhealthy:
            print(f"status: {len(unhealthy)} service(s) not healthy: {', '.join(unhealthy)}")
            return EXIT_FAILURE
        print(f"status: {len(rows)} service(s) healthy")
        return EXIT_OK
    except ValueError as exc:
        print(f"error: {exc}")
        return EXIT_FAILURE


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
