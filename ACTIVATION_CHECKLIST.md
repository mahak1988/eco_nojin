### Voice AI (Whisper API) — Activation Checklist

| Step | Action | Command |
|------|--------|---------|
| 1 | Install Whisper | `pip install openai` or `pip install openai-whisper` |
| 2 | Set env | `export STT_PROVIDER=whisper` |
| 3 | Set API key | `export WHISPER_API_KEY=your-key` |
| 4 | Restart API | `uvicorn services.api_gateway.main:app` |
| 5 | Test STT | `curl /api/v1/voice/providers` |
| 6 | Test TTS | `export TTS_PROVIDER=coqui && pip install TTS` |
| 7 | Set Twilio | `pip install twilio && export TWILIO_ACCOUNT_SID=...` |

### IoT Integration — Activation Checklist

| Step | Action | Command |
|------|--------|---------|
| 1 | Start MQTT broker | `mosquitto -v` or Docker |
| 2 | Install paho-mqtt | `pip install paho-mqtt` |
| 3 | Set broker config | In DeviceConnector constructor |
| 4 | Register device | `POST /api/v1/iot/devices` |
| 5 | Send reading | Publish to `hydroma/+/reading` |
| 6 | Verify | `GET /api/v1/iot/devices/{id}/readings` |

### Regional Expansion — Activation Checklist

| Step | Action | Status |
|------|--------|--------|
| 1 | Backend i18n (14 langs) | ✅ Complete |
| 2 | Frontend Lang type | ✅ Extended to ur/ps |
| 3 | ur/ps overlay | ✅ Created in regionalOverlay.ts |
| 4 | LanguageContext | ✅ Supports 4 langs |
| 5 | RegionalSettingsPage | ✅ Created |
| 6 | Full ur/ps content | 🔲 Ongoing (1600 lines) |

### Multi-Tenant SaaS — Activation Checklist

| Step | Action | Status |
|------|--------|--------|
| 1 | User.platform_id | ✅ Added |
| 2 | Organization model | ✅ Exists |
| 3 | Membership model | ✅ Exists |
| 4 | TenantMiddleware | ✅ Created |
| 5 | Orgs API | ✅ 6 endpoints |
| 6 | Tenant isolation | ✅ platform_id on key models |
| 7 | Org management UI | ✅ Created |
