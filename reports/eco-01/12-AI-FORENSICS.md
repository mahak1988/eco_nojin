# ECO-01 AI Forensics

**Document ID:** ECO-01-12-AI-FORENSICS  
**Scope:** engine/hydroma/ + services/ AI/ML components  
**Purpose:** Analyze what AI exists, what it does, and its coupling to scientific computation

---

## 1. Executive Summary

AI components in HyDroMA are limited and mostly in early/experimental stages. The main AI layer is in `engine/hydoma/generative_ai/`. No AI system currently influences core scientific calculations.

---

## 2. AI Component Inventory

### 2.1 Generative AI Layer

**Location:** engine/hydoma/generative_ai/

| File | Purpose | Status |
|------|---------|--------|
| `engine/hydoma/generative_ai/__init__.py` | Package init | EXPERIMENTAL |
| `engine/hydoma/generative_ai/assistant.py` | LLM-based assistant | EXPERIMENTAL |
| `engine/hydoma/generative_ai/prompt_engine.py` | Prompt management | EXPERIMENTAL |
| `engine/hydoma/generative_ai/report_generator.py` | Report generation from analysis | EXPERIMENTAL |

### 2.2 Machine Learning Components

| Component | Purpose | Location | Status |
|-----------|---------|----------|--------|
| Anomaly Detection | Detect anomalous climate readings | engine/hydroma/ml/anomaly.py | EXPERIMENTAL |
| Interpolation ML | Spatial interpolation via ML | engine/hydoma/ml/interpolation.py | EXPERIMENTAL |
| Forecasting | Time series forecasting | engine/hydoma/ml/forecasting.py | EXPERIMENTAL |

### 2.3 AI Service Integrations

| Service | Purpose | Location | API |
|---------|---------|----------|-----|
| OpenAI Client | LLM access | services/ai/providers/openai.py | GPT-4o, GPT-3.5 |
| Anthropic Client | LLM access | services/ai/providers/anthropic.py | Claude 3 |
| Local LLM | Offline LLM | services/ai/providers/local.py | llama.cpp |
| Embedding Service | Text embeddings | services/ai/embedding/ | OpenAI embeddings |

---

## 3. AI Capabilities and Classification

### Capability AICAP-001: Text Generation / Report Generation
- **Type:** GENERATION
- **Purpose:** Generate written reports from scientific analysis results
- **Inputs:** Structured data (model results, metrics), metadata, report templates
- **Outputs:** Markdown/text reports, summaries
- **Location:** engine/hydoma/generative_ai/report_generator.py
- **AI Method:** LLM (GPT-4o, Claude 3)
- **External Dependency:** Yes (OpenAI/Anthropic API)
- **Decision Impact:** NONE - output only, no influence on calculations
- **Status:** EXPERIMENTAL

**Assessment:** Safe. No scientific calculations affected. Pure output formatting. This is a utility wrapper around external LLM APIs.

### Capability AICAP-002: Conversational Assistant
- **Type:** INTERPRETATION
- **Purpose:** Answer questions about scientific results in natural language
- **Inputs:** User queries, scientific data context
- **Outputs:** Natural language responses
- **Location:** engine/hydoma/generative_ai/assistant.py
- **AI Method:** LLM with RAG (Retrieval-Augmented Generation)
- **External Dependency:** Yes (OpenAI/Anthropic API)
- **Decision Impact:** NONE
- **Status:** EXPERIMENTAL

**Assessment:** Safe. No impact on calculations. Interpretation only.

### Capability AICAP-003: Anomaly Detection
- **Type:** CLASSIFICATION
- **Purpose:** Detect anomalous values in climate/hydrology data
- **Inputs:** Time series of weather/hydrology measurements
- **Outputs:** Anomaly flags, confidence scores
- **Location:** engine/hydoma/ml/anomaly.py
- **AI Method:** Statistical anomaly detection / ML models
- **External Dependency:** Unknown provider (possibly sklearn)
- **Decision Impact:** NONE directly, but anomalies could trigger review
- **Status:** EXPERIMENTAL

**Assessment:** Low risk. Anomalies flagged for review, not used to automatically adjust calculations.

### Capability AICAP-004: ML-Based Spatial Interpolation
- **Type:** PREDICTION
- **Purpose:** Predict values at unsampled locations using ML
- **Inputs:** Sampled spatial data, coordinates
- **Outputs:** Interpolated raster
- **Location:** engine/hydoma/ml/interpolation.py
- **AI Method:** Random Forest / Gradient Boosting
- **External Dependency:** scikit-learn
- **Decision Impact:** Could replace traditional IDW interpolation
- **Status:** EXPERIMENTAL

**Critical Note:** This is a potential boundary concern. ML interpolation could influence downstream calculations if it replaces the verified IDW method.

### Capability AICAP-005: Time Series Forecasting
- **Type:** PREDICTION
- **Purpose:** Forecast future weather/hydrology values
- **Inputs:** Historical time series
- **Outputs:** Forecasted values with confidence intervals
- **Location:** engine/hydoma/ml/forecasting.py
- **AI Method:** LSTM / Transformer models
- **External Dependency:** PyTorch / TensorFlow
- **Decision Impact:** Could feed into irrigation scheduling decisions
- **Status:** EXPERIMENTAL

**Critical Note:** If forecasting feeds into irrigation decisions, this creates a decision boundary that requires careful review.

---

## 4. AI Coupling Analysis

### 4.1 AI → Scientific Calculation Coupling

| AI Component | Does it Affect Scientific Calculations? | Evidence | Risk Level |
|-------------|-----------------------------------------|----------|------------|
| Report Generation | NO | Output only | NONE |
| Conversational Assistant | NO | Q&A only | NONE |
| Anomaly Detection | INDIRECT | Flags → review, not automatic correction | LOW |
| ML Interpolation | POTENTIAL | Could replace IDW in data pipeline | MEDIUM |
| ML Forecasting | POTENTIAL | Could feed future ET predictions | MEDIUM-HIGH |

### 4.2 Scientific → AI Coupling

| Scientific Component | Feeds AI Inputs? | Evidence |
|---------------------|------------------|----------|
| ET0 Results | YES | Report generator uses ET0 data |
| Runoff Results | YES | Same |
| Climate Data | YES | Anomaly detection input; forecasting target |
| Soil Data | YES | Anomaly detection input |
| Watershed Results | YES | Report generator |

### 4.3 Control Boundary Assessment

```
┌─────────────────────────────────────┐
│         SCIENTIFIC CORE              │
│  (ET0, SCS-CN, Darcy, Van Genuchten) │
│  Outputs → Provenance-tracked        │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│         DATA PROCESSING              │
│  (Interpolation, Smoothing)         │
│  Current: IDW (verified)            │
│  Experimental: ML Interpolation      │
│  ─────────────────────────────────   │
│  Boundary: ONLY verified methods →  │
│  Scientific calculations            │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│         DECISION LAYER               │
│  (EPIA, Irrigation Scheduling)      │
│  May use AI forecasts, but scientific│
│  inputs (ET0, soil) remain primary   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│         AI/INTERPRETATION LAYER      │
│  (Reports, Assistant, Analysis)     │
│  Does NOT influence scientific calc │
└─────────────────────────────────────┘
```

**Assessment:** Current boundary is clear. Scientific computation does not depend on AI. AI is used only for interpretation, reporting, and experimental prediction.

---

## 5. Hidden Assumptions in AI Components

| AI Component | Hidden Assumption | Evidence | Risk |
|-------------|-------------------|----------|------|
| Report Generator | LLM output is accurate | No verification of generated content | HIGH |
| ML Interpolation | Training data representative | Not documented | HIGH |
| ML Forecasting | Historical patterns persist | Stationarity assumption | HIGH |
| Anomaly Detection | Normal = historical baseline | No concept drift handling | MEDIUM |
| Conversational Assistant | Retrieved context sufficient | RAG depends on knowledge base quality | MEDIUM |

---

## 6. Input/Output Analysis

### 6.1 Report Generator
- **Inputs:** JSON-serialized model results, report templates
- **Outputs:** Text/markdown reports
- **Parameters Generated:** NONE (no scientific parameters)
- **Thresholds Set:** NONE
- **Decisions Made:** NONE (formatting/presentation only)

### 6.2 Conversational Assistant
- **Inputs:** Natural language queries, context from scientific results
- **Outputs:** Natural language responses
- **Parameters Generated:** NONE
- **Thresholds Set:** NONE
- **Decisions Made:** NONE (informational only)

### 6.3 Anomaly Detection
- **Inputs:** Time series data (climate, soil, hydrology)
- **Outputs:** Anomaly flags, confidence scores
- **Parameters Generated:** Anomaly threshold (configurable, not learned)
- **Decisions Made:** NONE (flags for human review)

### 6.4 ML Interpolation
- **Inputs:** Spatial sample points (coordinates + values)
- **Outputs:** Predicted values at unsampled locations
- **Parameters Generated:** NONE (model pre-trained)
- **Thresholds Set:** NONE

### 6.5 ML Forecasting
- **Inputs:** Historical time series
- **Outputs:** Forecasted values, confidence intervals
- **Parameters Generated:** NONE
- **Thresholds Set:** NONE

---

## 7. External Provider Dependencies

| AI Component | Provider | API Type | Cost Model | Data Usage |
|-------------|----------|----------|------------|------------|
| Report Generator | OpenAI | Chat Completions | Token-based | Data used for training (policy dependent) |
| | Anthropic | Messages | Token-based | Data used for training (policy dependent) |
| Conversational Assistant | OpenAI | Chat Completions | Token-based | Same as above |
| | Anthropic | Messages | Token-based | Same as above |
| ML Interpolation | scikit-learn (local) | Local compute | Compute resources | Full data control |
| ML Forecasting | PyTorch/TensorFlow (local) | Local compute | Compute resources | Full data control |
| Embedding Service | OpenAI | Embeddings API | Token-based | Data usage policy dependent |

**Risk Assessment:** External LLM providers may use data for training. This creates privacy and IP concerns for any confidential or novel scientific content.

---

## 8. AI Output Influence on Scientific Calculations

### 8.1 Direct Influence
**NONE FOUND.** No AI-generated parameters, coefficients, or thresholds feed into scientific calculations.

### 8.2 Indirect Influence
| Path | Risk Level | Mitigation |
|------|-----------|------------|
| ML Interpolation → Scientific Models | MEDIUM | Ensure verified methods (IDW) are default; ML is experimental opt-in |
| ML Forecasting → Decision Engine | MEDIUM | Document that forecasts are probabilistic, not deterministic |
| Report Generator → Human Decision | LOW | Add confidence/disclaimer to AI-generated content |

### 8.3 Control Boundary
Current boundary is:
```
Scientific Calculation → Results (provenance-tracked)
                      ↓
                   Data Processing (verified methods only)
                      ↓
                   AI Analysis (experimental, no feedback)
                      ↓
                   Human Decision
                      ↓
                   Action
```

**This boundary must be maintained.** AI must never feed back into scientific computation without explicit review and version control.

---

## 9. AI Safety Assessment

### 9.1 Current State
- ✅ AI does not silently influence scientific calculations
- ✅ AI outputs are clearly separated from scientific computation
- ✅ AI is marked as experimental
- ✅ No AI-generated formulas/parameters in production code

### 9.2 Concerns
1. **ML Interpolation** could replace verified methods → ensure fallback to IDW
2. **ML Forecasting** could feed decision layer → ensure probabilistic interpretation
3. **Report Generation** may hallucinate scientific facts → add verification step
4. **External LLM providers** may use data → consider local LLM for sensitive content

### 9.3 Recommendations

| Recommendation | Priority | Action |
|---------------|----------|--------|
| Maintain strict AI → scientific boundary | CRITICAL | Document and enforce |
| Add confidence scores to AI outputs | HIGH | Require for all AI-generated content |
| Local LLM fallback for reports | MEDIUM | Consider for data privacy |
| Verify ML interpolation vs IDW | MEDIUM | Benchmark against verified method |
| Document AI input/output contracts | HIGH | Explicit contracts needed |

---

## 10. AI Component Classification Summary

| AI Component | Classification | Influence on Science | Recommended Action |
|-------------|----------------|---------------------|-------------------|
| Report Generator | GENERATION | NONE | KEEP_WITH_REVIEW - add confidence labels |
| Conversational Assistant | INTERPRETATION | NONE | KEEP_WITH_REVIEW - add factuality checks |
| Anomaly Detection | CLASSIFICATION | INDIRECT | KEEP_WITH_REVIEW - add human-in-loop |
| ML Interpolation | PREDICTION | POTENTIAL | ISOLATE - must not replace verified methods |
| ML Forecasting | PREDICTION | POTENTIAL | ISOLATE - probabilistic only, no deterministic use |

---

## 11. Future AI Integration Points

### Potential Opportunities (Require Design)
1. **AI-Assisted Parameter Calibration** - Suggest parameter values from literature review
2. **AI-Powered Evidence Extraction** - From satellite/climate data
3. **AI-Enhanced Uncertainty Quantification** - Monte Carlo via ML surrogates
4. **AI Pattern Recognition** - In monitoring/hydrology data

### Requirements for Safe Integration
- All AI must produce **confidence scores**
- AI must never **auto-adjust** scientific parameters
- AI outputs must be **reviewable and reversible**
- AI must be **versioned** with clear lineage
- AI must be **testable** with reproducible inputs

---

## 12. AI Technology Stack

| Technology | Usage | Status |
|-----------|-------|--------|
| OpenAI API (GPT-4o, GPT-3.5) | LLM inference | EXPERIMENTAL |
| Anthropic API (Claude 3) | LLM inference | EXPERIMENTAL |
| scikit-learn | ML models (anomaly, interpolation) | EXPERIMENTAL |
| PyTorch / TensorFlow | Deep learning (forecasting) | NOT DEPLOYED |
| llama.cpp | Local LLM inference | OPTIONAL |

---

*See also: 10-HYDROMA-FORENSICS.md, 11-CPP-PYTHON-BOUNDARY.md, 02-SCIENTIFIC-KNOWLEDGE-REGISTRY.md*