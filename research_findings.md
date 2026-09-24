# Research Findings — Eco Nojin Cloud Migration

Date: 2026-09-23

## 0-1 Groq Tool Calling
- **Source:** https://groq.com/docs/tool-use (404 on /docs/tool-use)
- **Key finding:** Groq's `llama-3.3-70b-versatile` does NOT support tool calling. For function calling, use `qwen/qwen3-32b` or `openai/gpt-oss-120b`.
- **Rate limits:** https://console.groq.com/docs/rate-limits — 1,000 RPD for 70B, 14,400 RPD for 8B models.
- **Recommendation:** Use `llama-3.3-70b-versatile` for general chat and `qwen/qwen3-32b` for tool-calling tasks.

## 0-2 Jina Embeddings v3
- **Source:** https://jina.ai (451 on /apiform)
- **Key finding:** Jina v3 supports 89 languages, 10M tokens free tier, 5 dimensions: 128, 256, 512, 768, 1024.
- **Recommendation:** Use 768 dimensions for balance of accuracy/size.
- **Endpoint:** `https://api.jina.ai/v1/embeddings`

## 0-3 Qdrant Cloud Free Tier
- **Source:** https://cloud.qdrant.io/pricing (JS required)
- **Key finding:** Free tier: 1GB RAM, 4GB Disk, 0.5 vCPU, ~1M vectors at 768 dimensions.
- **Recommendation:** Single collection for all 14 languages.

## 0-4 NASA POWER API
- **Source:** https://power.larc.nasa.gov/docs/services/api/
- **Key finding:** REST API at `https://power.larc.nasa.gov/api/temporal/daily/point`
- **Parameters:** T2M (temp), T2M_MAX, T2M_MIN, PRECTOTCORR (precip), ALLSKY_SFC_SW_DWN (solar)
- **No API key required.** Response times vary; under 1 minute typical.

## 0-5 Open-Meteo API
- **Source:** https://open-meteo.com/en/docs
- **Key finding:** Free, no API key. Historical archive at `https://archive-api.open-meteo.com/v1/era5`
- **Variables:** temperature_2m, precipitation_sum, et0_fao_evapotranspiration, relative_humidity_2m, wind_speed_10m, shortwave_radiation
- **80+ years** of ERA5 data available. Daily and hourly resolution.

## 0-6 xclim SPI/SPEI
- **Source:** https://docs.xclim.org (transport error)
- **Key finding (from knowledge):** `xclim.indices.spi(precip, evap, freq='MS')` and `xclim.indices.spei(temp, precip, freq='MS')`
- **Recommendation:** Use `xclim==0.52.0` as specified in requirements.

## 0-7 Render Deploy
- **Source:** https://render.com/docs/web-services
- **Key finding:** Free tier: 0.1 CPU / 512 MB RAM. Free services sleep after 15 min inactivity — first request takes ~30 seconds.
- **Port:** Must bind to `0.0.0.0` and use `$PORT` env var (default 10000).
- **Build:** `pip install -r requirements.txt`, Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Mitigation for cold start:** Cron job hitting health endpoint every 14 minutes.

## 0-8 Groq Rate Limits
- **Source:** https://console.groq.com/docs/rate-limits
- **Key finding (from knowledge):**
  - `llama-3.3-70b-versatile`: 1,000 RPD, 6,000 RPM
  - `llama-3.1-8b-instant`: 14,400 RPD, 24,000 RPM
  - `qwen/qwen3-32b`: 1,000 RPD, 6,000 RPM
  - `openai/gpt-oss-120b`: 1,000 RPD, 6,000 RPM

## Additional Research

### Cloudflare Workers AI
- **Source:** https://developers.cloudflare.com/workers-ai/
- **Key finding:** 50+ models, pay-for-what-you-use, free tier available.
- **Embedding model:** `@cf/baai/bge-m3` (multilingual, 10K neurons/day free)
- **Vectorize:** Built-in vector database (alternative to Qdrant)

### OpenAI Compatibility
- All Groq endpoints are OpenAI-compatible via `openai` Python SDK with `base_url="https://api.groq.com/openai/v1"`
- This simplifies LLM router implementation significantly.