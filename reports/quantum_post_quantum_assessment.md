# Quantum & Post-Quantum Assessment Report
**Audit Date:** 2026-09-08  
**Working Directory:** D:\eco_nojin  
**Auditor:** Kilo  

---

## Executive Summary

Quantum computing is **not yet ready** for direct production deployment in agricultural modeling, but specific subproblems within Eco Nojin could benefit from quantum-inspired algorithms or near-term quantum hardware (NISQ). Post-quantum cryptography (PQC) is **immediately relevant** for data security.

| Domain | Quantum Relevance | Recommended Algorithm | Feasibility | Recommendation |
|--------|-------------------|----------------------|-------------|----------------|
| Soil Carbon Modeling | Medium | Quantum ML (Q kernel regression) | 3-5 years | Research Phase |
| Crop Yield Prediction | Medium | QAOA for planting schedules | 3-5 years | Research Phase |
| Water Resource Allocation | High | QAOA / VQE for multi-objective | 5-7 years | Research Phase |
| Risk Assessment | Medium | Quantum Monte Carlo | 2-4 years | Research Phase |
| Data Security | **Critical** | **Post-quantum cryptography (CRYSTALS-Kyber)** | **Now** | **Develop Now** |

---

## 1. Soil Carbon Modeling (RothC Parameter Estimation)

### Current State
- RothC-26.3 (`services/scientific_motors/rothc.py`, `rothc_real.py`) uses 5 pools with fixed decomposition rates.
- Parameters (DPM/RPM ratio, clay factor, rate modifiers) are calibrated via empirical rules or manual fitting.
- `carbon_sequestration.py` includes a `_compute_rate_modifier` based on temperature and rainfall.

### Quantum Opportunity
**Quantum Machine Learning for Inverse Modeling:**
- RothC parameter estimation is an inverse problem: given observed SOC time series, estimate decomposition rates, initial pool distributions, and carbon inputs.
- Classical optimization (Nelder-Mead, L-BFGS) gets stuck in local minima with noisy, sparse soil data.
- **Quantum Kernel Methods** (Havlíček et al., 2019) can map low-dimensional soil features into high-dimensional Hilbert spaces, enabling better regression of RothC parameters from limited calibration data.
- **Variational Quantum Circuits** could encode soil texture, climate, and management as quantum states and learn a parameter surrogates model.

### Algorithm Recommendation
- **Quantum Kernel Ridge Regression (QKRR)** for parameter calibration
- **VQE (Variational Quantum Eigensolver)** — not directly applicable; better for chemistry
- **QAOA** — not directly applicable to continuous parameter optimization

### Feasibility Assessment
- **NISQ Limitations:** Current quantum hardware (50-1000 qubits) cannot handle the dimensionality of RothC (5 pools × 20 years × spatial grid). Quantum advantage requires problem-specific encoding.
- **Hybrid Approach:** Classical RothC forward model + quantum ML surrogate for parameter calibration. This is the most realistic near-term path.
- **Timeline:** 3-5 years for proof-of-concept on cloud quantum hardware (Azure Quantum, AWS Braket).

### Recommendation
**Research Phase.** Implement a classical Bayesian calibration framework first (MCMC with likelihood-free inference). Revisit quantum ML when >1000 logical qubits are available.

---

## 2. Crop Yield Prediction (Planting Schedule Optimization)

### Current State
- `crop_advisor.py` uses deterministic suitability scoring (climate 30%, pH 15%, etc.).
- `aquacrop_real.py` simulates single scenarios; no optimization over planting dates or cultivar selection.
- `optimize_chain.py` uses NSGA-II (classical) for multi-objective optimization.

### Quantum Opportunity
**Quantum Optimization for Planting Schedules:**
- The planting date optimization problem is combinatorial: choose planting date + cultivar + irrigation regime to maximize yield × price - cost, subject to frost risk, water availability, and market windows.
- This maps naturally to **Quadratic Unconstrained Binary Optimization (QUBO)**.
- **QAOA (Quantum Approximate Optimization Algorithm)** can find near-optimal solutions to QUBO problems on NISQ devices.
- **Quantum Annealing (D-Wave)** is already commercially available for QUBO problems.

### Algorithm Recommendation
- **QAOA** for gate-based quantum computers (Azure Quantum, IBMQ)
- **Quantum Annealing** for D-Wave Advantage (already available)
- **Hybrid Solver** (D-Wave Leap) — classical + quantum hybrid, available today

### Feasibility Assessment
- **Current Hardware:** D-Wave Leap hybrid solver can handle ~10,000 variables. A planting schedule problem for 100 fields × 30 planting dates × 20 cultivars = 60,000 binary variables — within reach of hybrid decomposition.
- **NISQ Limitations:** Gate-based QAOA depth is limited by coherence time; shallow QAOA (p=2-4) may not outperform classical heuristics for this problem size.
- **Timeline:** 2-4 years for hybrid quantum-classical pilot; 5+ years for pure quantum advantage.

### Recommendation
**Research Phase.** Start with D-Wave hybrid solver pilot for a simplified single-field, single-crop planting date optimization. Use classical NSGA-II as baseline comparator.

---

## 3. Water Resource Allocation (Multi-Objective Distribution)

### Current State
- `pywr_real.py` runs a single reservoir → demand + environment network.
- `chain_runner.py` computes monthly inflow/demand proxies but no multi-reservoir, multi-user optimization.
- Water allocation is currently deterministic with no stochastic optimization.

### Quantum Opportunity
**Quantum Multi-Objective Optimization:**
- Water allocation across N users, M reservoirs, T time periods is a large-scale stochastic optimization problem.
- Objectives: maximize supply reliability, minimize deficit, maximize storage, minimize environmental impact.
- Constraints: reservoir capacity, pipe capacity, legal allocations, evaporation losses.
- **QAOA** can solve the underlying QUBO formulation of multi-objective water distribution.
- **VQE** could optimize continuous release rules via parameterized quantum circuits.

### Algorithm Recommendation
- **QAOA** for discrete allocation decisions (which field gets water when)
- **Quantum GNNs** for spatial water distribution across watershed networks
- **Hybrid Quantum-Classical** for large-scale problems

### Feasibility Assessment
- **Problem Scale:** A realistic watershed with 100 nodes, 12 months, 3 allocation tiers = ~3,600 binary variables. Manageable for hybrid solvers.
- **NISQ Limitations:** Current QAOA depth insufficient for complex temporal dependencies. Hybrid decomposition (problem splitting) required.
- **Timeline:** 5-7 years for meaningful quantum advantage on this problem.

### Recommendation
**Research Phase.** First, implement a classical stochastic optimization benchmark (e.g., SDDP - Stochastic Dual Dynamic Programming). Then explore quantum-inspired classical algorithms (e.g., tabu search with quantum-inspired transitions) as a bridge.

---

## 4. Risk Assessment (Drought/Flood Probability Estimation)

### Current State
- `drought_motor.py` computes SPI/SPEI using gamma CDF and normal standardization.
- `climate_motor.py` compares CMIP6 scenarios vs ERA5 baseline.
- Risk classification is deterministic thresholds (SPI < -1.5 = severe).

### Quantum Opportunity
**Quantum Probability Estimation:**
- Drought/flood risk estimation involves rare-event probability estimation under climate uncertainty.
- **Quantum Monte Carlo (QMC)** can sample probability distributions with fewer samples than classical MCMC for certain problem classes.
- **Quantum Amplitude Estimation (QAE)** provides quadratic speedup for estimating expected values of random variables — directly applicable to drought risk metrics.
- **Quantum Bayesian Networks** could update drought probability as new satellite/weather data arrives.

### Algorithm Recommendation
- **Quantum Amplitude Estimation (QAE)** for drought frequency estimation
- **Quantum Boltzmann Machines** for probabilistic modeling of climate teleconnections
- **Quantum-enhanced MCMC** for posterior sampling of climate parameters

### Feasibility Assessment
- **Current Hardware:** QAE requires ~1/ε qubits and gates for ε-error estimation. For SPI estimation with ε=0.1, ~100 qubits may suffice for proof-of-concept.
- **NISQ Limitations:** QAE depth is high; near-term implementations use "classical QAE" (hybrid). True quantum speedup requires fault-tolerant quantum computing.
- **Timeline:** 2-4 years for hybrid quantum amplitude estimation pilot; 5+ years for pure quantum advantage.

### Recommendation
**Research Phase.** Implement classical Bayesian drought risk model with MCMC first. Pilot hybrid quantum amplitude estimation on Azure Quantum or AWS Braket for a single-site SPI estimation task.

---

## 5. Post-Quantum Cryptography (PQC)

### Current State
- `services/security/pqcrypto.py` exists but not audited in detail.
- Platform handles sensitive agricultural data (land ownership, yields, financial transactions).
- No evidence of PQC integration in database encryption, API transport, or blockchain registry.

### Quantum Threat
- **Harvest Now, Decrypt Later (HNDL):** Adversaries are collecting encrypted data now to decrypt when quantum computers arrive (estimated 10-20 years for cryptographically relevant quantum computers).
- **Affected Algorithms:** RSA-2048/4096, ECDSA, ECDH, AES-256 (key sizes < 512 bits vulnerable to Grover's algorithm).

### PQC Recommendations
| Use Case | Current Algorithm | PQC Replacement | Standard |
|----------|-------------------|-----------------|----------|
| TLS/HTTPS | RSA/ECDSA | CRYSTALS-Kyber (KEM) + CRYSTALS-Dilithium (signatures) | NIST FIPS 203/204 |
| Data at Rest | AES-256 | AES-256 (safe if 512-bit keys) + Kyber for key encapsulation | NIST |
| Digital Signatures | ECDSA | CRYSTALS-Dilithium or SPHINCS+ | NIST FIPS 204 |
| Blockchain Registry | ECDSA | Dilithium or SPHINCS+ | NIST |

### Feasibility Assessment
- **NIST Standards Finalized (2024):** CRYSTALS-Kyber (key encapsulation), CRYSTALS-Dilithium (signatures), SPHINCS+ (hash-based signatures) are now FIPS standards.
- **Implementation Ready:** Open-source libraries exist (liboqs, pqcrypto, cryptography.io).
- **Performance:** PQC keys are larger (Dilithium public key ~2.5KB vs ECDSA 64 bytes) but acceptable for most use cases.
- **Timeline:** **Immediate.** Begin migration now to protect against HNDL attacks.

### Recommendation
**DEVELOP NOW.** 
1. Audit `services/security/pqcrypto.py` for NIST-compliant implementations.
2. Add Kyber key encapsulation for API gateway TLS.
3. Add Dilithium signatures for carbon credit blockchain registry.
4. Implement hybrid classical+PQC key exchange during transition period.

---

## Quantum Readiness Matrix

| Component | Quantum Ready? | Action |
|-----------|---------------|--------|
| RothC SOC model | No | Classical Bayesian calibration first |
| AquaCrop yield model | No | Classical NSGA-II baseline |
| Pywr water allocation | No | Classical SDDP baseline |
| SPI/SPEI drought | No | Classical Bayesian + hybrid QAE pilot |
| PQC security | **YES** | **Migrate to NIST PQC standards immediately** |
| Optimization (NSGA-II) | Partial | Quantum-inspired classical algorithms first |

---

## References

1. Havlíček, V., et al. (2019). "Supervised learning with quantum-enhanced feature spaces." Nature 567, 209–212.
2. Preskill, J. (2018). "Quantum Computing in the NISQ era and beyond." Quantum 2, 79.
3. NIST FIPS 203/204 (2024). CRYSTALS-Kyber and CRYSTALS-Dilithium standards.
4. Allen, R.G., et al. (1998). "FAO Irrigation and Drainage Paper 56." FAO.
5. Coleman, K., & Jenkinson, D.S. (1996). "RothC-26.3." Soil Use and Management.
6. Steduto, P., et al. (2012). "AquaCrop: The FAO crop water productivity model." FAO Irrigation and Drainage Paper 66.

---

## Appendix: Quantum Hardware Landscape (2026)

| Provider | Qubits | Type | Availability | Relevance |
|----------|--------|------|--------------|-----------|
| IBM Quantum | 1000+ | Superconducting | Cloud (IBMQ) | General QAOA/QML |
| Azure Quantum | 100+ | Superconducting + IonQ | Cloud | Integrated with Azure stack |
| AWS Braket | 100+ | Multi-vendor | Cloud | Diverse hardware access |
| D-Wave | 5000+ | Quantum Annealer | Cloud (Leap) | QUBO optimization |
| Google Quantum AI | 1000+ | Superconducting | Limited cloud | High-fidelity circuits |
| IonQ | 100+ | Trapped ion | Cloud | High coherence, low qubits |

**Key Insight:** For Eco Nojin's problem set, **D-Wave hybrid solvers** and **Azure Quantum** are the most immediately accessible platforms for pilot studies.
