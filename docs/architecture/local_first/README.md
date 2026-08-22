# Local-First Hybrid Architecture

## Overview

معماری Local-First Hybrid برای پلتفرم EcoNojin:
- همه داده‌های کاربر روی دستگاه خودش ذخیره می‌شود
- سرور فقط auth + encrypted sync blobs
- هزینه سرور ~$20-50/ماه (به جای $1500-7000)
- حریم خصوصی zero-knowledge
- کارکرد آفلاین

## Files

| # | File | Description |
|---|------|-------------|
| 01 | `CLIENT_SCHEMA.sql` | Schema دیتابیس دستگاه کاربر |
| 02 | `SERVER_SCHEMA.sql` | Schema دیتابیس سرور (minimal) |
| 03 | `PWA_MANIFEST.json` | PWA manifest |
| 04 | `SERVICE_WORKER.js` | Offline capability |
| 05 | `INDEXEDDB_CLIENT.js` | Client storage |
| 06 | `SYNC_PROTOCOL.md` | Encrypted sync |
| 07 | `SERVER_ENDPOINT.py` | Minimal FastAPI |
| 08 | `COST_ANALYSIS.md` | Economic analysis |

## References

- Linear's local-first: https://linear.app/blog/local-first
- Signal protocol: https://signal.org/docs/
- CRDTs: https://crdt.tech/
- NIST PBKDF2: NIST SP 800-132

## Stack

- **Client**: IndexedDB + WebAssembly + Service Workers
- **Sync**: AES-256-GCM encrypted deltas + CRDTs
- **Server**: Supabase Free Tier + Cloudflare Workers
- **No Docker Required**: 100% cloud-native managed services
