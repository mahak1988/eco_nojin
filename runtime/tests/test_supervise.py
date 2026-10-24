"""Tests for the Docker-free runtime supervisor.

These tests are fast and deterministic. The one scenario that really needs a
server (``uvicorn``) is bounded by a 20 s wait and skipped, with a clear reason,
when ``uvicorn`` is not importable.
"""

from __future__ import annotations

import importlib.util
import socket
import sys
import time
from pathlib import Path

import pytest
import yaml

from runtime import supervise

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:  # keep `import services.*` working under pytest
    sys.path.insert(0, str(REPO_ROOT))

REAL_CONFIG = supervise.DEFAULT_CONFIG_PATH
REQUIRED_KEYS = ("name", "app", "port")
STUB_SOURCE = '''
"""Minimal ASGI app used to exercise the supervisor without a real service."""


async def app(scope, receive, send):
    assert scope["type"] == "http"
    await send(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": [(b"content-type", b"text/plain")],
        }
    )
    await send({"type": "http.response.body", "body": b"ok"})
'''


def _free_port() -> int:
    """A port that can actually be bound twice, avoiding Windows' reserved ranges.

    ``bind(0)`` hands out an ephemeral port which may sit inside Hyper-V's
    excluded range — binding such a port succeeds once and then fails with
    WinError 10013/10048, which is what made this test flaky. So each candidate
    is released and immediately re-bound before it is accepted.
    """
    for _ in range(32):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.bind(("127.0.0.1", 0))
            candidate = int(probe.getsockname()[1])
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as again:
                again.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                again.bind(("127.0.0.1", candidate))
            return candidate
        except OSError:
            continue
    pytest.skip("no re-bindable loopback port available on this host")


def _write_config(tmp_path: Path, port: int, name: str = "stub") -> Path:
    (tmp_path / "stub_app.py").write_text(STUB_SOURCE, encoding="utf-8")
    config = tmp_path / "services.yaml"
    config.write_text(
        yaml.safe_dump(
            {
                "services": [
                    {
                        "name": name,
                        "app": "stub_app:app",
                        "host": "127.0.0.1",
                        "port": port,
                        "workers": 1,
                        "health_path": "/healthz",
                        "depends_on": [],
                        "enabled": True,
                    }
                ]
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return config


@pytest.fixture
def stub_runtime(tmp_path: Path):
    """A supervisor pointed at a stub ASGI app on a free port (real uvicorn)."""
    if importlib.util.find_spec("uvicorn") is None:
        pytest.skip("uvicorn is not installed; the live-service scenario needs it")
    port = _free_port()
    config = _write_config(tmp_path, port)
    supervisor = supervise.Supervisor(
        config_path=config,
        log_dir=tmp_path / "logs",
        cwd=tmp_path,
    )
    started = time.monotonic()
    supervisor.up()
    healthy_at = None
    deadline = started + 20.0
    try:
        while time.monotonic() < deadline:
            row = supervisor.status()[0]
            if row["health"] == "healthy":
                healthy_at = time.monotonic()
                break
            time.sleep(0.1)
        yield supervisor, port, tmp_path, started, healthy_at
    finally:
        supervisor.down()


def test_services_yaml_is_valid() -> None:
    """The shipped service map is valid and every enabled app really exists."""
    document = yaml.safe_load(REAL_CONFIG.read_text(encoding="utf-8"))
    entries = document["services"]
    assert entries, "the runtime service map must not be empty"

    ports: list[int] = []
    for entry in entries:
        if not entry.get("enabled", True):
            continue
        missing = [key for key in REQUIRED_KEYS if entry.get(key) is None]
        assert not missing, f"{entry.get('name', '?')} is missing {missing}"
        assert isinstance(entry["name"], str) and entry["name"].strip()
        assert entry["app"].count(":") == 1, entry["app"]
        assert isinstance(entry["port"], int), entry["port"]
        ports.append(entry["port"])

    assert len(ports) == len(set(ports)), f"duplicate ports in {REAL_CONFIG}: {ports}"

    for entry in entries:
        module = entry["app"].split(":")[0]
        assert importlib.util.find_spec(module) is not None, f"module not found: {module}"

    services = supervise.load_services(REAL_CONFIG)
    assert [service["name"] for service in services] == [entry["name"] for entry in entries]


def test_supervisor_up_down_status_with_stub_service(
    stub_runtime,
) -> None:
    """A stub ASGI app is started by ``up()`` and reported healthy by ``status()``."""
    supervisor, port, _tmp_path, started, healthy_at = stub_runtime
    assert healthy_at is not None, f"port {port} did not become healthy within 20 s"
    assert healthy_at - started < 20.0

    rows = supervisor.status()
    assert len(rows) == 1
    assert rows[0]["name"] == "stub"
    assert rows[0]["port"] == port
    assert rows[0]["health"] == "healthy"
    assert rows[0]["pid"] is not None


def test_port_conflict_fails_fast(tmp_path: Path) -> None:
    """``up()`` refuses to start a service whose port is already bound."""
    if importlib.util.find_spec("uvicorn") is None:
        pytest.skip("uvicorn is not installed; the live-service scenario needs it")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as taken:
        taken.bind(("127.0.0.1", 0))
        taken.listen(1)
        port = int(taken.getsockname()[1])
        config = _write_config(tmp_path, port)
        supervisor = supervise.Supervisor(config_path=config, log_dir=tmp_path / "logs")
        with pytest.raises(ValueError, match=f"port {port}"):
            supervisor.up()
        assert supervisor.status()[0]["health"] == "stopped"


def test_down_is_graceful_and_kills(stub_runtime) -> None:
    """``down()`` stops the child process well within the graceful timeout."""
    supervisor, _port, _tmp_path, _started, healthy_at = stub_runtime
    assert healthy_at is not None
    process = supervisor._processes["stub"]
    assert process.poll() is None

    supervisor.down()
    assert process.poll() is not None, "subprocess still running after down()"
    assert process.returncode is not None
    assert supervisor.status()[0]["health"] == "stopped"
    assert "stub" not in supervisor._processes


def test_yaml_validation_rejects_bad_schema(tmp_path: Path) -> None:
    """Duplicate ports, missing keys and malformed values are rejected."""
    duplicate = tmp_path / "duplicate.yaml"
    duplicate.write_text(
        yaml.safe_dump(
            {
                "services": [
                    {"name": "a", "app": "stub_app:app", "port": 8150},
                    {"name": "b", "app": "stub_app:app", "port": 8150},
                ]
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="duplicate port 8150"):
        supervise.load_services(duplicate)

    missing = tmp_path / "missing.yaml"
    missing.write_text(
        yaml.safe_dump({"services": [{"name": "a", "app": "stub_app:app"}]}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="missing required key"):
        supervise.load_services(missing)

    bad_port = tmp_path / "bad_port.yaml"
    bad_port.write_text(
        yaml.safe_dump({"services": [{"name": "a", "app": "stub_app:app", "port": 70000}]}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="outside the range"):
        supervise.load_services(bad_port)

    bad_app = tmp_path / "bad_app.yaml"
    bad_app.write_text(
        yaml.safe_dump({"services": [{"name": "a", "app": "stub_app", "port": 8150}]}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="module:attribute"):
        supervise.load_services(bad_app)

    empty = tmp_path / "empty.yaml"
    empty.write_text("services: []\n", encoding="utf-8")
    with pytest.raises(ValueError, match="non-empty"):
        supervise.load_services(empty)

    unknown_dependency = tmp_path / "unknown_dep.yaml"
    unknown_dependency.write_text(
        yaml.safe_dump(
            {
                "services": [
                    {"name": "a", "app": "stub_app:app", "port": 8150, "depends_on": ["ghost"]}
                ]
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="unknown service 'ghost'"):
        supervise.load_services(unknown_dependency)


def test_cli_exit_codes(stub_runtime, capsys) -> None:
    """``status`` exits 0 when healthy, 1 when the service is down, 2 on bad usage.

    The CLI invocations share the fixture's log directory so the state file
    written by ``up`` is the one the CLI reads.
    """
    supervisor, _port, tmp_path, _started, healthy_at = stub_runtime
    assert healthy_at is not None
    config = str(supervisor.config_path)
    log_dir = str(supervisor.log_dir)

    def cli(args: list[str]) -> int:
        return supervise.main([*args, "--config", config, "--log-dir", log_dir])

    assert cli(["status"]) == supervise.EXIT_OK
    assert "healthy" in capsys.readouterr().out

    assert cli(["down"]) == supervise.EXIT_OK
    capsys.readouterr()

    assert cli(["status"]) == 1
    assert "stopped" in capsys.readouterr().out

    assert cli(["restart", "ghost"]) == 1
    assert "unknown service" in capsys.readouterr().out

    assert supervise.main(["definitely-not-a-command"]) == 2
    assert supervise.main([]) == 2


def test_restart_replaces_the_process(stub_runtime) -> None:
    """``restart(name)`` stops the old child and starts a new one on the same port."""
    supervisor, port, _tmp_path, _started, healthy_at = stub_runtime
    assert healthy_at is not None
    first_pid = supervisor._processes["stub"].pid

    supervisor.restart("stub")
    second_pid = supervisor._processes["stub"].pid
    assert second_pid is not None and second_pid != first_pid

    deadline = time.monotonic() + 20.0
    while time.monotonic() < deadline:
        if supervisor.status()[0]["health"] == "healthy":
            break
        time.sleep(0.1)
    else:  # pragma: no cover - defensive
        pytest.fail(f"port {port} did not become healthy after restart within 20 s")

    supervisor.down()
    assert supervisor.status()[0]["health"] == "stopped"
