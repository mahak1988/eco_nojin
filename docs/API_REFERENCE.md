# API Reference

**Base URL**: `http://127.0.0.1:8000`
**Interactive Docs**: `http://127.0.0.1:8000/docs` (Swagger UI)
**ReDoc**: `http://127.0.0.1:8000/redoc`
**Version**: 1.4.0

## Endpoint Summary

| Category | Endpoints | Prefix |
|----------|-----------|--------|
| System | 2 | `/api/v1/` |
| Soil | 3 | `/api/v1/soil/` |
| Materials | 1 | `/api/v1/materials/` |
| AI Assistant | 2 | `/api/v1/ai/` |
| Satellite | 2 | `/api/v1/satellite/` |
| Scenarios | 5 | `/api/v1/scenarios/` |
| Marketplace | 8 | `/api/v1/marketplace/` |
| Carbon | 6 | `/api/v1/carbon/` |
| Watershed | 2 | `/api/v1/watershed/` |
| Benchmark | 2 | `/api/v1/benchmark/` |
| Sync | 3 | `/api/v1/sync/` |
| Realtime | 2 | `/api/v1/realtime/` |
| USSD/SMS | 6 | `/api/v1/ussd/` |
| Voice | 8 | `/api/v1/voice/` |
| Blockchain | 15 | `/api/v1/blockchain/` |

---

## System Endpoints

### GET /api/v1/health

System health check with comprehensive status.

**Response:**
```json
{
  "status": "operational",
  "engine": "HyDroMa",
  "version": "1.4.0",
  "modules": ["soil", "materials", "ai_assistant", "satellite", ...],
  "inclusive_access": { "web_app": true, "ussd_feature_phone": true, ... },
  "mobile_features": { "pwa": true, "offline_sync": true, ... },
  "blockchain": { "enabled": true, "carbon_registry": true, ... }
}
```

### GET /api/v1/version

Detailed version information.

---

## Carbon Registry (Blockchain)

### POST /api/v1/blockchain/carbon/projects

Register a new carbon project.

**Request:**
```json
{
  "owner": "0x123...",
  "project_type": "afforestation",
  "area_ha": 100.0,
  "duration_years": 10
}
```

### POST /api/v1/blockchain/carbon/projects/{id}/verify

Verify a carbon project.

### POST /api/v1/blockchain/carbon/projects/{id}/issue

Issue carbon credits for a verified project.

### POST /api/v1/blockchain/carbon/credits/transfer

Transfer carbon credits between owners.

### POST /api/v1/blockchain/carbon/credits/{id}/retire

Retire carbon credits (permanent carbon offset).

---

## Supply Chain (Blockchain)

### POST /api/v1/blockchain/supply-chain/products

Register a new product in supply chain.

### GET /api/v1/blockchain/supply-chain/products/{id}

Get product with full trace history.

### POST /api/v1/blockchain/supply-chain/products/{id}/events

Add a trace event (harvested, processed, shipped, delivered).

---

## Voice AI / IVR

### POST /api/v1/voice/ivr/start

Start a new IVR session.

### POST /api/v1/voice/tts

Convert text to speech.

### POST /api/v1/voice/stt

Convert speech to text.

### POST /api/v1/voice/ask

Ask a question and get voice response (RAG-powered).

---

## USSD/SMS Gateway

### POST /api/v1/ussd/ussd

Process USSD request (supports `*384*73#` menu).

### POST /api/v1/ussd/sms

Process SMS command (e.g., `SOIL 36.8 54.4`, `PRICE wheat`).

---

## Satellite Analysis

### POST /api/v1/satellite/analyze

Analyze a geographic point with satellite data.

**Request:**
```json
{
  "lat": 36.8,
  "lon": 54.4,
  "analysis_date": "2025-01-15"
}
```

**Response:**
```json
{
  "ndvi": 0.542,
  "evi": 0.387,
  "savi": 0.451,
  "vegetation_status": { "class": "dense" },
  "recommendation": "Excellent vegetation health"
}
```

---

## AI Assistant (RAG)

### POST /api/v1/ai/chat

Ask the AI assistant (RAG-based with citations).

---

## Error Responses

All errors follow this format:
```json
{
  "detail": "Error message here"
}
```

**Common HTTP status codes:**
- `200` - Success
- `400` - Bad request
- `404` - Not found
- `422` - Validation error
- `500` - Internal server error
- `503` - Service unavailable (feature disabled or dependency down)

---

## Sync Endpoints (Local-First Cloud Synchronization)

The sync endpoints implement the outbox pattern for reliable local-first data synchronization with Supabase cloud.

### GET /api/v1/sync/status

Get synchronization status including Supabase connectivity and pending events.

**Response:**
```json
{
  "status": "ok",
  "mode": "local-first",
  "cloud": "supabase",
  "local_pending_events": 0,
  "supabase_connected": false,
  "supabase_error": "[Errno 11001] getaddrinfo failed",
  "note": "Local-first sync with Supabase cloud. Offline data syncs when connection restored."
}
```

**Feature Flag:** `ENABLE_SUPABASE_SYNC` (default: true)

---

### POST /api/v1/sync/trigger

Manually trigger synchronization of pending outbox events to Supabase.

**Response (success):**
```json
{
  "ok": true,
  "synced": 0,
  "failed": 0,
  "total_pending": 0
}
```

**Response (Supabase unavailable):**
```json
{
  "detail": "Supabase not available"
}
```

**Status Codes:**
- `200` - Sync completed
- `503` - Supabase unavailable or feature disabled

---

### GET /api/v1/sync/pending

List pending outbox events awaiting synchronization.

**Response:**
```json
{
  "ok": true,
  "count": 0,
  "events": []
}
```

**Event object:**
```json
{
  "id": 1,
  "event_type": "landscape_created",
  "aggregate_id": "uuid-string",
  "payload": { "key": "value" },
  "retry_count": 0,
  "created_at": "2026-01-15T10:30:00Z"
}
```

---

## Realtime Endpoints (Server-Sent Events)

Real-time event streaming via Server-Sent Events (SSE) for live dashboard updates.

### GET /api/v1/realtime/health

Health check for realtime service.

**Response:**
```json
{
  "status": "ok",
  "service": "realtime-sse",
  "enabled": true
}
```

**Feature Flag:** `ENABLE_REALTIME_SSE` (default: true)

---

### GET /api/v1/realtime/stream

Server-Sent Events stream for real-time updates.

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `user_key` | string | Yes | - | Anonymous user key (8-64 chars, alphanumeric + `_` `-`) |
| `events` | string | No | `model_runs,sync_status` | Comma-separated: `model_runs`, `sync_status` |
| `interval` | float | No | `2.0` | Polling interval in seconds |

**Example:**
```
GET /api/v1/realtime/stream?user_key=testuser123&events=model_runs,sync_status&interval=2.0
```

**Response (SSE stream):**
```
data: {"type": "model_run", "data": {"id": 1, "model_id": "hydroma-v1", "title": "Soil Analysis", "shared": false, "created_at": "2026-01-15T10:30:00Z"}}

data: {"type": "sync_status", "data": {"pending_count": 3}}

: heartbeat

data: {"type": "error", "data": {"message": "Connection error"}}
```

**Event Types:**
| Type | Description |
|------|-------------|
| `model_run` | New model run created for user |
| `sync_status` | Pending sync count changed |
| `error` | Stream error |
| `heartbeat` | Keep-alive (every interval) |

**Status Codes:**
- `200` - Stream started
- `400` - Invalid user key format
- `503` - Realtime feature disabled

**Headers:**
```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
X-Accel-Buffering: no
```