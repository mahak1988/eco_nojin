# 🎙️ Voice AI Setup Guide — Phase 5.3

This guide covers activating the real Voice AI providers (Whisper, Coqui, Twilio).

## Step 1: STT (Speech-to-Text) — Whisper

### Option A: OpenAI Whisper API (recommended)
```bash
pip install openai
export WHISPER_API_KEY="your-openai-api-key"
export STT_PROVIDER="whisper"
```

### Option B: Local Whisper
```bash
pip install openai-whisper
export STT_PROVIDER="whisper"
# Model will auto-download on first use
```

### Option C: Keep mock (default)
```bash
export STT_PROVIDER="mock"
```

## Step 2: TTS (Text-to-Speech) — Coqui

```bash
pip install TTS
export TTS_PROVIDER="coqui"
# Models will auto-download on first use (~2GB)
```

For Persian/Arabic voices specifically:
```bash
pip install TTS
# Coqui auto-selects fa/ar voice configs
```

### Option: Keep mock
```bash
export TTS_PROVIDER="mock"
```

## Step 3: IVR Telephony — Twilio

```bash
pip install twilio
export TWILIO_ACCOUNT_SID="your-account-sid"
export TWILIO_AUTH_TOKEN="your-auth-token"
export TWILIO_PHONE_NUMBER="+989123456789"
```

## Step 4: Verify

```bash
curl http://localhost:8000/api/v1/voice/providers
curl http://localhost:8000/api/v1/voice/diagnostics
curl http://localhost:8000/api/v1/voice/health
```

## Step 5: Test Endpoints

```bash
# STT test (base64 encode audio file)
AUDIO=$(base64 -i sample.wav)
curl -X POST http://localhost:8000/api/v1/voice/stt \
  -H "Content-Type: application/json" \
  -d '{"audio_base64": "'"$AUDIO"'", "language": "fa"}'

# TTS test
curl -X POST http://localhost:8000/api/v1/voice/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "سلام به اکو نوژین", "language": "fa"}'

# IVR test
curl -X POST http://localhost:8000/api/v1/voice/ivr/call \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+989123456789"}'

# SMS test
curl -X POST http://localhost:8000/api/v1/voice/ivr/sms \
  -H "Content-Type: application/json" \
  -d '{"to": "+989123456789", "body": "Your soil moisture is 45%"}'
```

## Configuration Reference

| Environment Variable | Required For | Default |
|---|---|---|
| `STT_PROVIDER` | STT provider selection | `mock` |
| `WHISPER_API_KEY` | OpenAI Whisper API | — |
| `OPENAI_API_KEY` | OpenAI Whisper API (fallback) | — |
| `WHISPER_MODEL_SIZE` | Whisper model size | `base` |
| `TTS_PROVIDER` | TTS provider selection | `mock` |
| `COQUI_MODEL_NAME` | Coqui model name | `auto` |
| `TWILIO_ACCOUNT_SID` | Twilio account | — |
| `TWILIO_AUTH_TOKEN` | Twilio auth token | — |
| `TWILIO_PHONE_NUMBER` | Twilio phone number | — |

## Architecture

```
┌──────────────────────────────────────────────────┐
│              Voice API Router                     │
│  /api/v1/voice/{ivr,tts,stt,ask,providers,...}   │
├──────────────────────────────────────────────────┤
│  STT Factory ──→ WhisperSTTProvider (real/mock)  │
│  TTS Factory ──→ CoquiTTSProvider (real/mock)    │
│  IVR Factory ──→ TwilioIVR (real/mock)           │
├──────────────────────────────────────────────────┤
│  All providers gracefully fall back to mock      │
│  when dependencies/credentials are absent        │
└──────────────────────────────────────────────────┘
```

## Troubleshooting

| Issue | Solution |
|---|---|
| `Whisper: All init methods failed` | Install `openai` or `openai-whisper` package |
| `Coqui TTS init failed` | Install `TTS` package, check GPU availability |
| `Twilio not configured` | Set Twilio env variables |
| `STT/TTS returning mock` | Check env variable spelling |
| Model download slow | Pre-download models, check network |

## Performance Notes

- **Whisper API**: ~3-5s per minute of audio (network latency)
- **Whisper Local**: ~1-2s per minute (GPU), ~10-30s (CPU)
- **Coqui TTS**: ~1-2s per sentence (GPU), ~5-10s (CPU)
- **Twilio**: ~1-3s per call/SMS initiation
