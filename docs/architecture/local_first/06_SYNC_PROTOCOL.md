# Sync Protocol: Zero-Knowledge Encrypted Deltas

## Overview

Client و سرور فقط deltas (تغییرات) را به صورت end-to-end encrypted 
مبادله می‌کنند. سرور نمی‌تواند محتویات را بخواند.

## Flow: Client to Server (Sync Up)

Client:
  1. Collect unsynced changes from sync_queue
  2. Encrypt each change with user's master key (AES-256-GCM)
  3. POST /api/v1/sync/push
     Body: {
       "changes": [
         {
           "id": "...",
           "table": "analyses",
           "operation": "insert",
           "encrypted_payload": "...",
           "iv": "...",
           "lamport_clock": 42
         }
       ]
     }

Server:
  1. Validate auth
  2. Store encrypted blobs (opaque storage)
  3. Update vector clock
  4. Return: { "accepted": [...], "conflicts": [...] }

## Flow: Server to Client (Sync Down)

Client:
  1. GET /api/v1/sync/pull?since=<last_sync_timestamp>

Server:
  1. Return all encrypted blobs updated since timestamp
  2. Include vector clock for conflict resolution

Client:
  1. Decrypt each blob with master key
  2. Apply to local DB
  3. Resolve conflicts using Lamport clocks
  4. Update last_sync_at

## Conflict Resolution: Lamport Clocks

Example:
  A: lamport=5, value=X
  B: lamport=7, value=Y
  Result: B wins (higher clock = newer)

If equal: use deterministic tiebreaker (record_id hash)

## Bandwidth Efficiency

| Operation | Data Sent |
|-----------|-----------|
| New analysis | ~5 KB (encrypted) |
| Update | ~1 KB (delta only) |
| Delete | ~100 bytes |

For 1000 users x 10 analyses/day = 50 MB/day total (negligible)
