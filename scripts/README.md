# Windows Service Management Scripts

These scripts manage the Eco Nojin API Gateway as a Windows Service.

## Local development (no Docker required)

The default development profile uses SQLite and a native Python environment.
From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-local-api.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m uvicorn services.api_gateway.main:app --reload --port 8000
```

Set `DATABASE_URL`, `REDIS_URL`, or `NATS_URL` to managed endpoints only when
testing integrations. Install `requirements-optional.txt` before enabling Redis
or other optional integrations. To run the optional PostgreSQL/Redis/n8n stack locally,
install Podman Desktop and run `podman compose -f deploy/docker-compose.yml up -d`.

## Prerequisites

- Python 3.12 installed at `C:\Users\hp\AppData\Local\Programs\Python\Python312\python.exe`
- Project venv activated: `.\.venv\Scripts\Activate.ps1`
- Dependencies installed: `.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-local-api.txt`

## Quick Start

```powershell
# 1. Activate venv
.\.venv\Scripts\Activate.ps1

# 2. Install the service (one-time setup)
.\scripts\install-service.ps1

# 3. Start the service
.\scripts\start-service.ps1

# 4. Check status
.\scripts\service-status.ps1

# 5. View logs
.\scripts\service-logs.ps1

# 6. Stop the service
.\scripts\stop-service.ps1
```

## Scripts

| Script | Description |
|--------|-------------|
| `install-service.ps1` | Install API Gateway as Windows Service (one-time) |
| `start-service.ps1` | Start the service |
| `stop-service.ps1` | Stop the service |
| `service-status.ps1` | Check service status |
| `service-logs.ps1` | Tail live logs |

## Manual Run (without service)

If you just want to run the API without installing as a service:

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn services.api_gateway.main:app --host 0.0.0.0 --port 8000
```

## Troubleshooting

1. **Port already in use**: Change port in `install-service.ps1` or kill the process using port 8000
2. **Permission denied**: Run PowerShell as Administrator
3. **Module not found**: Ensure venv is activated and dependencies are installed
