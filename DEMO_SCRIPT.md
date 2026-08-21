# Demo Script

**Last Updated**: August 14, 2026
**Presenter**: [Your Name]
**Audience**: Investors, Partners, Users

---

## Pre-Demo Checklist

### Environment Setup
- [ ] Backend running: `http://127.0.0.1:8000`
- [ ] Frontend running: `http://localhost:3000`
- [ ] Swagger UI accessible: `http://127.0.0.1:8000/docs`
- [ ] USSD/SMS simulator ready (or real telco connection)
- [ ] Voice IVR system ready (or mock)
- [ ] Stable internet connection
- [ ] Backup slides/screenshots in case of issues

### Demo Flow Options
- **5-minute demo**: Focus on key differentiators
- **15-minute demo**: Full feature tour
- **30-minute demo**: Deep technical dive

---

## 5-Minute Demo (Key Differentiators)

### [0:00-0:30] Opening Hook

**Script**:
> "Imagine a farmer in rural Iran with a $10 feature phone.
> No internet, no smartphone, can't read English.
> How can they access the same agricultural science that a Silicon Valley AgTech startup uses?
> That's the problem Eco Nojin solves."

**Show**: Title slide with tagline

### [0:30-1:30] The Problem

**Script**:
> "2.5 billion farmers worldwide lack access to modern agricultural tools.
> 70% have no digital AgTech.
> 80% of platforms require smartphones and internet.
> And climate change is projected to reduce agricultural productivity by 25% by 2050.
> These farmers need help now, not in 20 years."

**Show**: Problem slide with statistics

### [1:30-2:30] The Solution

**Script**:
> "Eco Nojin is a scientific platform that reaches EVERY farmer.
> Through web, mobile apps, USSD codes, SMS, and even voice calls.
> 14 languages. 5 access channels. Scientific rigor.
> Let me show you how it works."

**Show**: Solution overview slide

### [2:30-4:00] Live Demo: USSD + Web

**Step 1: USSD Demo (Feature Phone)**

**Script**:
> "Let's start with a farmer who has a basic feature phone.
> They dial *384*73#"

**Action**: Show USSD menu (simulator or real phone)
- Show main menu
- Select '1' for soil analysis
- Enter coordinates: 36.8,54.4
- Show result: "Soil analysis: NDVI 0.49, Status: Stressed, Advice: Add compost"

**Script**:
> "No internet needed. No smartphone. Just a basic phone.
> And they get scientific soil analysis in seconds."

**Step 2: Web App Demo (Full Platform)**

**Script**:
> "Now let's see the full platform on web."

**Action**: Navigate to `http://localhost:3000`
- Show satellite analysis panel
- Enter coordinates, run analysis
- Show NDVI, EVI, SAVI results
- Show AI assistant, ask: "How to make good compost?"
- Show RAG response with FAO citation

**Script**:
> "Same science, accessible through any channel.
> And every answer includes citations to peer-reviewed research."

### [4:00-4:30] Business Model

**Script**:
> "We monetize through:
> - Carbon credit verification fees (5-10%)
> - Marketplace commissions (2-5%)
> - Enterprise API licenses ($500+/month)
> - Government contracts
> Our TAM is $43B by 2030."

**Show**: Business model slide

### [4:30-5:00] The Ask

**Script**:
> "We're raising $500K seed to:
> - Deploy to 1,000 farmers in pilot
> - Expand engineering team
> - Secure telco partnerships
> Join us in building a sustainable, inclusive agricultural future."

**Show**: Ask slide with contact info

---

## 15-Minute Demo (Full Feature Tour)

### [0:00-2:00] Opening + Problem

Same as 5-minute demo opening.

### [2:00-5:00] Web App Tour

**Action**: Navigate through all 9 panels

**Panel 1: Soil Dashboard**
- Show registered soil profiles
- Click on one, show details
- Explain: "Farmers can track their soil health over time"

**Panel 2: Satellite Analysis**
- Enter coordinates (e.g., 36.8, 54.4)
- Click 'Analyze Field'
- Show NDVI, EVI, SAVI results
- Explain: "Real-time satellite imagery from Sentinel-2"

**Panel 3: Crop Planner**
- Select wheat, enter water/temp
- Run simulation
- Show yield prediction, revenue
- Explain: "AquaCrop-inspired modeling for 8+ crops"

**Panel 4: Scenario Analysis**
- Select SSP2-4.5, year 2050
- Run climate transition analysis
- Show impact on yields
- Explain: "CMIP6 climate scenarios for long-term planning"

**Panel 5: Carbon Credits**
- Select afforestation, 100 ha, 10 years
- Calculate carbon sequestration
- Show: 800 tonnes CO2, estimated revenue
- Explain: "IPCC methodology, blockchain-verified"

**Panel 6: Watershed Structures**
- Select check dam, enter slope/area
- Calculate design
- Show dimensions, cost
- Explain: "Engineering design for water conservation"

**Panel 7: Marketplace**
- Show products, filters
- Show traceability QR codes
- Explain: "Farm-to-consumer transparency"

**Panel 8: Performance Benchmark**
- Run NDVI benchmark
- Show: NumPy 85ms vs Numba 10ms (8x faster)
- Explain: "Scientific computing at scale"

**Panel 9: AI Assistant**
- Ask: "What crops grow well in arid regions?"
- Show RAG response with citations
- Explain: "AI-powered Q&A with peer-reviewed sources"

### [5:00-8:00] Access Channels Demo

**USSD Demo** (2 min)
- Dial *384*73#
- Navigate: Main menu → Crop advice → North → Get recommendation
- Show: "Best crops: Rice, Wheat. Plant Oct-Nov."

**SMS Demo** (1 min)
- Send: `PRICE wheat`
- Receive: `Wheat: $0.35/kg (trend: stable)`
- Send: `LANG fa`
- Send: `قیمت گندم` (Persian)
- Receive: Persian response

**Voice IVR Demo** (1 min)
- Call hotline
- Listen to menu
- Press '5' for expert questions
- Ask: "How to make compost?"
- Get spoken answer

### [8:00-11:00] Blockchain Demo

**Action**: Navigate to blockchain endpoints in Swagger UI

**Step 1: Register Carbon Project**
```json
POST /api/v1/blockchain/carbon/projects
{
  "owner": "0x123...",
  "project_type": "afforestation",
  "area_ha": 100,
  "duration_years": 10
}
```
Show: Returns project_id, tx_hash

**Step 2: Verify Project**
```json
POST /api/v1/blockchain/carbon/projects/{id}/verify
{
  "verifier": "Verra"
}
```
Show: Status changes to 'verified'

**Step 3: Issue Credits**
```json
POST /api/v1/blockchain/carbon/projects/{id}/issue
{
  "amount": 800,
  "owner": "0x123..."
}
```
Show: Returns credit_id, tx_hash

**Step 4: Transfer Credits**
```json
POST /api/v1/blockchain/carbon/credits/transfer
{
  "credit_id": "cred_xxx",
  "from_owner": "0x123...",
  "to_owner": "0x456..."
}
```
Show: Ownership transferred

**Step 5: Retire Credits**
```json
POST /api/v1/blockchain/carbon/credits/{id}/retire
{
  "owner": "0x456..."
}
```
Show: Credits retired (permanent offset)

**Script**:
> "Every step is recorded on the blockchain.
> Immutable, transparent, verifiable.
> This is how we build trust in carbon markets."

### [11:00-13:00] Technical Deep-Dive

**Show**: Architecture slide

**Script**:
> "Let me show you under the hood.
> 14 modules, 169 tests, 60+ API endpoints.
> Built with Python, FastAPI, Next.js.
> Numba JIT gives us 8x performance.
> Scientific foundation: FAO, IPCC, CMIP6.
> Open-source core for transparency."

**Action**: Show test output
```bash
pytest tests/ -v
# 169 passed
```

### [13:00-15:00] Business + Ask

Same as 5-minute demo closing.

---

## Handling Q&A

### Common Questions

**Q: Why USSD/SMS? Isn't that outdated?**

A: "For 2.5 billion farmers with feature phones, it's their only option.
> We meet users where they are.
> As they upgrade to smartphones, they migrate to our PWA/web app.
> It's an inclusion strategy, not a technology choice."

**Q: How do you compete with established AgTech platforms?**

A: "We don't compete directly. We serve a market they ignore.
> Existing platforms target large commercial farms with smartphones.
> We target smallholders with basic phones.
> Different market, different channel, different business model."

**Q: How do you ensure scientific accuracy?**

A: "Three layers:
> 1. Peer-reviewed sources (FAO, IPCC, CMIP6)
> 2. Every answer includes citations
> 3. Open-source code for transparency
> Scientists can verify our algorithms."

**Q: What's your user acquisition strategy?**

A: "Three phases:
> 1. Pilot with agricultural cooperatives (1,000 farmers)
> 2. Telco partnerships for USSD distribution
> 3. Government contracts for large-scale deployment
> Low CAC because we use existing channels (USSD, SMS)."

**Q: How do you monetize free users?**

A: "Free users are the base of the pyramid.
> They generate data insights (anonymized) that we sell to researchers.
> They become carbon credit producers (we take 5-10% verification fee).
> They use our marketplace (we take 2-5% commission).
> Freemium works when you have multiple revenue streams."

**Q: What's your technical moat?**

A: "Three layers:
> 1. Scientific algorithms (peer-reviewed, hard to replicate)
> 2. Multi-channel architecture (complex to build)
> 3. Network effects (more farmers = more data = better AI)
> First-mover advantage in inclusive AgTech."

**Q: How do you handle data privacy?**

A: "Principles:
> 1. User owns their data
> 2. Anonymization before any analytics
> 3. GDPR-compliant architecture
> 4. Blockchain for transparency (user can verify what's stored)
> Trust is our most valuable asset."

---

## Demo Troubleshooting

### If Backend Fails
- Show pre-recorded video of demo
- Explain: "Technical issues happen. Let me show you what it looks like when it works."

### If USSD/SMS Fails
- Show screenshots of real USSD session
- Explain: "Telco integration requires live connection. Here's what users see."

### If Blockchain Demo Fails
- Show Swagger UI with example responses
- Explain: "Blockchain transactions are deterministic. Here's the API contract."

### If Voice IVR Fails
- Show audio recording of voice session
- Explain: "Voice systems require telephony integration. Here's a recording."

---

## Post-Demo Follow-Up

### Immediate (Within 24 Hours)
- [ ] Send thank-you email with:
  - PROJECT_SUMMARY.md (attached)
  - Link to demo recording (if available)
  - Link to live demo (if deployed)
  - Calendar link for follow-up call

### Short-Term (1 Week)
- [ ] Follow-up call to answer questions
- [ ] Provide access to test environment
- [ ] Share technical documentation

### Medium-Term (1 Month)
- [ ] Share pilot results (if applicable)
- [ ] Update on milestones
- [ ] Discuss partnership opportunities

---

## Demo Environment Commands

### Start Backend
```bash
cd D:\eco_nojin
.venv/Scripts/python.exe -m uvicorn services.api_gateway.main:app --reload --port 8000
```

### Start Frontend
```bash
cd D:\eco_nojin\frontend
pnpm dev
```

### Run Tests (Show During Demo)
```bash
cd D:\eco_nojin
.venv/Scripts/python.exe -m pytest tests/ -v
```

### Access Points
- **Web App**: http://localhost:3000
- **API Docs**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc
- **Health Check**: http://127.0.0.1:8000/api/v1/health

---

## Key Talking Points

### Differentiators to Emphasize
1. **Inclusion**: 5 access channels (unique in market)
2. **Science**: Peer-reviewed, transparent (trust)
3. **Scale**: 8x performance, 14 languages
4. **Transparency**: Blockchain verification
5. **Market**: $43B TAM, underserved segment

### Numbers to Remember
- **2.5B** farmers worldwide
- **70%** lack digital AgTech
- **25%** productivity decline by 2050
- **14** modules
- **169** tests passing
- **60+** API endpoints
- **8x** performance boost
- **$43B** TAM by 2030

---

## Success Metrics for Demo

### Did the Audience...
- [ ] Understand the problem clearly?
- [ ] See the unique value proposition?
- [ ] Ask relevant questions?
- [ ] Request follow-up meeting?
- [ ] Express interest in partnership/investment?

### Demo Quality Checklist
- [ ] All features worked as expected
- [ ] No major technical issues
- [ ] Stayed within time limit
- [ ] Addressed all questions
- [ ] Clear call-to-action

---

*Demo script last updated: August 14, 2026*