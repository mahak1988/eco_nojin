# Roadmap

## Completed (MVP - v1.4.0)

- [x] 14 core modules
- [x] 169 automated tests (100% passing)
- [x] 5 access channels (Web, PWA, USSD, SMS, Voice)
- [x] 14 languages with RTL/LTR support
- [x] Scientific foundation (FAO, IPCC, CMIP6)
- [x] Blockchain carbon registry + supply chain
- [x] AI assistant with RAG
- [x] Offline-first mobile architecture

---


## Phase 0 — Stabilization (started 2026-08-21)

- [x] Confirm repository write access and establish a main-branch baseline
- [x] Add the Persian execution plan in docs/DEVELOPMENT_PLAN_FA.md
- [x] Remove wildcard CORS fallback when credentials are enabled
- [ ] Run the clean-environment backend and frontend test suites
- [ ] Pin Python dependencies and add a lockfile
- [ ] Complete auth/write-path authorization review
- [ ] Add CI checks for tests, type checking, encoding, and dependency security
- [ ] Verify satellite provenance and keep simulated data clearly labeled

Phase 0 is intentionally focused on reliability and traceability before new
financial, insurance, blockchain, or ML capabilities are expanded.

## Near-Term (0-3 months)

### Module 15: Finance & Micro-credit
- [ ] Alternative credit scoring (based on agricultural data)
- [ ] Micro-loans for smallholder farmers
- [ ] Mobile payment integration (USSD/SMS)
- [ ] Loan repayment tracking

### Module 16: Index-Based Insurance
- [ ] Weather index insurance
- [ ] Satellite-based crop failure detection
- [ ] Automated claim verification
- [ ] Payout triggers via smart contracts

### Production Deployment
- [ ] Fix CVE-2025-66478 (Next.js upgrade)
- [ ] PostgreSQL migration
- [ ] Docker containerization
- [ ] Nginx + SSL setup
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Monitoring (Sentry, ELK stack)

### Pilot Deployment
- [ ] 1,000 farmers in Iran (pilot)
- [ ] Partnership with agricultural cooperatives
- [ ] Telco partnership for USSD code
- [ ] User feedback collection

---

## Medium-Term (3-12 months)

### Module 17: Multi-Tenant SaaS
- [ ] Organization management
- [ ] Role-based access control
- [ ] Data isolation per tenant
- [ ] White-label solutions

### Module 18: IoT Integration
- [ ] Soil moisture sensors
- [ ] Weather stations
- [ ] Drones for precision agriculture
- [ ] MQTT integration

### Regional Expansion
- [ ] Pakistan launch
- [ ] Afghanistan launch
- [ ] Local partnerships
- [ ] Localization refinement

### Real Blockchain Integration
- [ ] Ethereum mainnet integration
- [ ] OR Hyperledger Fabric setup
- [ ] Carbon credit tokenization (ERC-20/721)
- [ ] Integration with Verra/Gold Standard

### Voice AI Enhancement
- [ ] Real Whisper integration (OpenAI)
- [ ] Coqui TTS for Persian/Arabic
- [ ] Dialect support (regional variations)
- [ ] Twilio integration for IVR

---

## Long-Term (1-3 years)

### Scale & Impact
- [ ] 10M farmer reach across MENA
- [ ] Integration with national carbon registries
- [ ] Partnership with FAO, World Bank
- [ ] UN SDG alignment reporting

### Advanced Features
- [ ] Machine learning for yield prediction
- [ ] Computer vision for pest detection
- [ ] Federated learning across regions
- [ ] Digital twin for farm simulation

### Ecosystem Expansion
- [ ] Mobile app stores (Play Store, App Store)
- [ ] Government white-label solutions
- [ ] Enterprise API for AgTech companies
- [ ] Research collaboration platform

---

## Moonshots (Vision)

- **Global Agricultural Knowledge Graph**: Connecting all agricultural research
- **Decentralized Carbon Exchange**: Peer-to-peer carbon trading
- **Climate-Resilient Crop Breeding**: AI-guided crop development
- **Farmer-to-Farmer Knowledge Network**: Decentralized extension

---

## Contributing to the Roadmap

We welcome contributions! See [DEVELOPER.md](DEVELOPER.md) for:
- Development setup
- Code style guidelines
- Testing strategy
- PR process

---

**Roadmap last updated**: August 21, 2026