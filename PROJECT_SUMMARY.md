# Eco Nojin - Project Summary

## Intelligent Platform for Ecosystem Restoration and Smart Agriculture

**Report Date**: August 14, 2026
**Version**: 1.4.0 (MVP Complete)
**Status**: Production-Ready Research Prototype

---

## Executive Summary

Eco Nojin is a comprehensive scientific platform designed to democratize access to
ecosystem restoration tools and sustainable agriculture knowledge. Built on the HyDroMa
(Hydrology & Drought Monitoring) engine, the platform combines cutting-edge AI, satellite
imagery, climate modeling, and blockchain technology with an unwavering commitment to
**digital inclusion**.

The platform currently serves users through **5 distinct access channels** (Web, PWA, USSD,
SMS, Voice IVR) in **14 languages**, ensuring that even the most marginalized communities
can benefit from advanced agricultural science.

---

## Key Metrics

| Metric | Value |
|--------|-------|
| Total Modules | 14 |
| Total Automated Tests | 169 (100% passing) |
| API Endpoints | 60+ |
| Supported Languages | 14 |
| Access Channels | 5 (Web, PWA, USSD, SMS, Voice) |
| Scientific References | FAO, IPCC, CMIP6, AquaCrop |
| Performance (vs NumPy) | 8x faster (Numba JIT) |
| Backend Framework | FastAPI + Python 3.11 |
| Frontend Framework | Next.js 15.1.6 + React 19 |

---

## Problem Statement

### The Digital Divide in Agriculture

Over 2.5 billion people worldwide rely on agriculture for their livelihood, yet:
- **70%** of smallholder farmers lack access to digital agricultural tools
- **80%** of existing AgTech platforms require smartphones and reliable internet
- **90%** of advanced agricultural research never reaches the farmers who need it most
- **Language barriers** exclude 60% of the world's farmers from English-centric platforms

### Climate Change Impact

- Agricultural productivity projected to decline **25% by 2050** without adaptation
- Smallholder farmers bear **disproportionate burden** of climate impacts
- Lack of accessible tools for climate-resilient farming

---

## Our Solution

### 1. Inclusive Access (5 Channels)

| Channel | Target User | Key Feature |
|---------|-------------|-------------|
| **Web App** | Desktop/Tablet users | Full interactive dashboard |
| **PWA** | Mobile users | Offline-capable, installable |
| **USSD** (`*384*73#`) | Feature phones | Menu-based, no internet required |
| **SMS** | Basic phones | Command-based (`SOIL 36.8 54.4`) |
| **Voice IVR** | Low-literacy users | Voice menu, spoken answers |

### 2. Scientific Foundation

- **Satellite Analysis**: Sentinel-2 NDVI/EVI/SAVI/NDWI/NBR indices
- **Climate Scenarios**: CMIP6 SSP projections (2030/2050/2100)
- **Crop Modeling**: AquaCrop-inspired yield simulation for 8+ crops
- **Carbon Accounting**: IPCC methodology for 8 project types
- **Watershed Engineering**: Check dams, contour trenches, half-moons

### 3. AI-Powered Intelligence

- **RAG-based Q&A**: Scientific answers with source citations
- **Knowledge Base**: 10+ FAO/IPCC peer-reviewed documents
- **Multi-language Responses**: Answers in user's native language

### 4. Blockchain Transparency

- **Immutable Carbon Credit Registry**: Transparent verification
- **Supply Chain Traceability**: From farm to consumer
- **Smart Contract Ready**: Automated payments on delivery

---

## Module Architecture

### Core Scientific Modules (1-7)

1. **Data Models**: Soil profiles, plant species, materials
2. **Scientific Computations**: Hargreaves-Samani ET0, C/N ratio compost
3. **API Gateway**: RESTful FastAPI with OpenAPI docs
4. **AI Assistant (RAG)**: TF-IDF retrieval over scientific corpus
5. **Satellite Integration**: Sentinel-2 via STAC API (no key needed)
6. **Numba Core**: JIT-compiled NDVI, flood routing (8x speedup)
7. **Scenario Engine**: CMIP6 projections, Monte Carlo uncertainty

### Market & Finance Modules (8-10)

8. **Marketplace**: Products, orders, traceability (QR codes)
9. **Carbon Credits**: IPCC methodology for 8 project types
10. **Watershed Structures**: Engineering design + cost estimation

### Access Channel Modules (11-14)

11. **Mobile Features**: PWA, offline sync, geolocation, camera
12. **USSD/SMS Gateway**: Feature phone access (`*384*73#`)
13. **Voice AI / IVR**: Voice menu + RAG Q&A integration
14. **Blockchain Ledger**: Immutable carbon registry + supply chain

---

## Target Users

### Primary
- **Smallholder Farmers** (1-5 hectares)
- **Pastoralists and Nomadic Communities**
- **Rural Cooperatives**

### Secondary
- **Agricultural Extension Officers**
- **NGOs working on food security**
- **Impact Investors**
- **Policy Makers and Government Agencies**

### Tertiary
- **Carbon Project Developers**
- **Academic Researchers**
- **AgTech Companies**

---

## Market Opportunity

### Total Addressable Market (TAM)
- Global AgTech market: **$43B by 2030**
- Carbon credit market: **$50B by 2030**
- Agricultural extension services: **$10B+ annually**

### Serviceable Addressable Market (SAM)
- Smallholder farmers in MENA + South Asia: **250M farmers**
- With focus on climate-resilient practices: **100M farmers**

### Serviceable Obtainable Market (SOM)
- Initial target: **1M farmers** in Iran, Pakistan, Afghanistan
- 5-year target: **10M farmers** across MENA region

---

## Competitive Advantages

| Feature | Eco Nojin | Competitors |
|---------|-----------|-------------|
| Offline/USSD access | Yes | Rare |
| Multi-language (14) | Yes | 2-3 typical |
| Scientific citations | Yes | Rare |
| Blockchain verification | Yes | Rare |
| Voice IVR | Yes | Very rare |
| Open-source core | Yes | Mostly proprietary |

---

## Business Model

### Freemium Model
- **Free Tier**: Basic access via USSD/SMS/Voice (for smallholders)
- **Professional Tier**: Advanced analytics ($10/month) for cooperatives
- **Enterprise Tier**: API access, white-label ($500+/month)

### Revenue Streams
1. **Carbon Credit Verification Fees**: 5-10% of credit value
2. **Marketplace Commissions**: 2-5% per transaction
3. **Enterprise API Licenses**: B2B SaaS model
4. **Government/NGO Contracts**: Large-scale deployments
5. **Data Insights**: Anonymized analytics for research

---

## Current Status

- MVP complete with 14 modules
- 169 automated tests passing
- Ready for pilot deployment
- Seeking: Seed funding, pilot partners, telco partnerships

---

## Next Steps

### Immediate (0-3 months)
1. Pilot deployment with 1,000 farmers (Iran)
2. Telco partnership for USSD code allocation
3. CVE-2025-66478 fix + production deployment

### Medium-term (3-12 months)
1. Module 15: Finance & Micro-credit
2. Module 16: Index-based Insurance
3. Regional expansion (Pakistan, Afghanistan)

### Long-term (1-3 years)
1. 10M farmer reach across MENA
2. Integration with national carbon registries
3. White-label solutions for governments

---

## Contact

**Eco Nojin Team**
Email: info@econojin.org
Website: https://econojin.org
Repository: https://github.com/econojin/eco-nojin

---

*Built with care for a sustainable and inclusive future*