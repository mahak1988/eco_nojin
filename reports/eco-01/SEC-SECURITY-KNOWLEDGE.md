# ECO-01 Security Knowledge

**Document ID:** ECO-01-SEC-SECURITY-KNOWLEDGE  
**Scope:** engine/ + services/ security-related assets  
**Purpose:** Identify reusable security primitives separately from legacy application architecture

---

## 1. Executive Summary

Security knowledge in HyDroMA is limited and scattered. No structured security primitives exist in the scientific engine. Security is handled at the service infrastructure layer only.

---

## 2. Authentication Primitives

### 2.1 No Engine-Level Authentication

| Asset | Present | Location | Notes |
|-------|---------|----------|-------|
| Authentication in engine | NO | engine/ | Scientific engine has no auth |
| Authorization in engine | NO | engine/ | Scientific engine has no auth |
| Token management | NO | engine/ | N/A |

**Assessment:** Correct - scientific engine should not handle authentication.

### 2.2 Service-Level Authentication

| Service | Authentication Method | Security Knowledge | Reuse Potential |
|---------|----------------------|-------------------|-----------------|
| services/auth | JWT / OAuth2 | High | Infrastructure-level |
| services/auth_legacy | Session-based | Low | OBSOLETE |
| services/security | Role-based access | Medium | Infrastructure-level |

**Assessment:** Authentication is fully at service layer. Not reusable as a security primitive for scientific engine.

---

## 3. Authorization Concepts

### 3.1 Role-Based Access (Service Level)

| Entity | Roles | Location | Status |
|--------|-------|----------|--------|
| User | user, admin, researcher, hydrologist | services/users/models.py | PRESENT |
| Organization | owner, admin, member | services/organization/ | PRESENT |
| Project | owner, contributor, viewer | services/project/ | PRESENT |

**Assessment:** RBAC exists at service layer, not reusable for scientific computation.

### 3.2 Data Classification

| Asset | Present | Location | Notes |
|-------|---------|----------|-------|
| Data classification levels | NO | engine/ | No classification |
| Sensitive data marking | NO | engine/ | No marking |
| Public/restricted data | PARTIAL | services/data/ | Service-level only |

**Assessment:** No data classification in scientific engine.

---

## 4. Provenance as Security Primitive

### 4.1 Provenance Tracking

| Field | Present | Location | Reusasble? |
|-------|---------|----------|-----------|
| Source attribution | YES | engine/hydoma/provenance.py:12-89 | YES |
| Timestamp tracking | YES | provenance.py | YES |
| Method/version tracking | YES | provenance.py + model registry | YES |
| Input data lineage | PARTIAL | provenance.py | PARTIAL |
| Audit trail | YES | engine/hydoma/audit.py | YES |

**Assessment:** Provenance IS a reusable security/integrity primitive.

### 4.2 Provenance Security Value

| Security Property | Supported? | Location | Notes |
|-------------------|-----------|----------|-------|
| Integrity | YES | Provenance tracks source, method | HIGH value |
| Non-repudiation | YES | Timestamp + source | MEDIUM value |
| Traceability | YES | Full chain | HIGH value |
| Accountability | PARTIAL | No actor attribution | Needs user context |

---

## 5. Audit Logging

### 5.1 Current Audit Capabilities

| Feature | Present | Location | Status |
|---------|---------|----------|--------|
| Computation logging | YES | engine/hydoma/audit.py | PARTIAL |
| Input/output logging | YES | audit.py | PARTIAL |
| User attribution | NO | - | Missing |
| IP tracking | NO | - | Missing |
| Tamper evidence | NO | - | Missing |

### 5.2 Audit Log Content

| Event Type | Logged? | Details |
|-----------|---------|---------|
| Model execution | YES | Model name, inputs, result, duration |
| Data import | YES (partially) | Data source, size |
| Parameter change | NO | Not logged |
| User action | NO | Not in engine |
| System error | YES | Via structlog |

---

## 6. Validation and Sanitization

### 6.1 Input Validation

| Component | Validation Present | Location | Method |
|-----------|-------------------|----------|--------|
| Climate models | YES | et_calculator.py | Pydantic models |
| Soil models | YES | physics.py | Value range checks |
| Runoff models | YES | runoff_model.py | CN range check |
| Groundwater models | YES | groundwater_model.py | Parameter validation |
| Terrain analysis | YES | terrain_analysis.py | Array bounds |
| Radiation | YES | radiation.py | Unit conversion |

**Assessment:** Good input validation in scientific code. Pydantic V2 provides structural validation.

### 6.2 Sanitization

| Component | Sanitization Present | Location | Notes |
|-----------|---------------------|----------|-------|
| Climate data | YES | assimilation.py | Range checks |
| Soil data | YES | physics.py | Physical bounds |
| Rainfall | YES | runoff_model.py | Non-negative check |
| External API data | PARTIAL | clients/ | Some validation |

---

## 7. Privacy Controls

### 7.1 Personal Data Handling

| Data Type | Stored | Location | GDPR Compliant? |
|-----------|--------|----------|-----------------|
| User personal data | YES (services only) | services/users/ | UNKNOWN |
| User scientific data | YES (engine inputs) | engine/hydoma/ | UNKNOWN |
| Aggregated analytics | YES | services/analytics/ | UNKNOWN |
| Raw sensor data | YES | services/monitoring/ | UNKNOWN |

**Assessment:** No explicit privacy controls in scientific engine. Privacy is a service-level concern.

### 7.2 Scientific Data Anonymization

| Feature | Present | Location |
|---------|---------|----------|
| Data anonymization | NO | engine/ |
| Aggregation | YES | Various | Part of analysis |
| Pseudonymization | NO | - |
| Access control | NO | - |

---

## 8. Cryptographic Utilities

### 8.1 Cryptography in Engine

| Utility | Present | Location | Purpose |
|---------|---------|----------|---------|
| Hashing | NO | engine/ | N/A |
| Encryption | NO | engine/ | N/A |
| Signature | NO | engine/ | N/A |

**Assessment:** No cryptographic utilities in scientific engine. Correct.

### 8.2 Cryptographic in Services

| Utility | Present | Location | Notes |
|---------|---------|----------|-------|
| JWT signing | YES | services/auth/ | Standard |
| Password hashing | YES | services/auth/ | bcrypt/passlib |
| API key management | YES | services/config/ | ENV-based |
| Encryption at rest | PARTIAL | services/data/ | Database-level |

---

## 9. Reusable Security Primitives

### 9.1 Security Primitives That Exist

| Primitive | Location | Reusasble? | Notes |
|----------|----------|-----------|-------|
| Input validation (range checks) | engine/hydoma/ | YES | Extract as validation utilities |
| Pydantic schema validation | Multiple | YES | Strong validation framework |
| Provenance tracking | engine/hydoma/provenance.py | YES | Integrity/security primitive |
| Audit logging | engine/hydoma/audit.py | YES | Audit trail for calculations |
| Structlog structured logging | All modules | YES | Standard logging with context |

### 9.2 Security Primitives That Are Missing

| Primitive | Required For | Priority |
|----------|-------------|----------|
| Data integrity checksums | Verify data hasn't changed | HIGH |
| Tamper-evident logging | Audit trail integrity | MEDIUM |
| Access logging for scientific data | Compliance | LOW |
| Encryption at rest for sensitive data | Privacy | LOW |
| Digital signatures for model results | Non-repudiation | LOW |

---

## 10. Security Vulnerabilities Identified

### 10.1 Engine (Scientific Code)

| Vulnerability | Location | Risk | Notes |
|---------------|----------|------|-------|
| No input rate limiting | All models | LOW | Not applicable for computation |
| No resource limits | Iterative models | MEDIUM | Could be exploited via bad params |
| No memory limits | C++ bridge | MEDIUM | Buffer overflow potential |
| No execution time limits | Simulations | MEDIUM | Infinite loop potential |

### 10.2 Services

| Vulnerability | Location | Risk | Notes |
|---------------|----------|------|-------|
| Hardcoded secrets | services/config/ | CRITICAL | See SECURITY-FINDINGS.md |
| SQL injection | Services with string queries | HIGH | Need parameterization |
| API key exposure | Environment handling | HIGH | Secrets in code |

---

## 11. Security Primitive Assessment

### 11.1 Reusable Security Primitives

| Primitive | Location | Quality | Strategic Value |
|----------|----------|---------|-----------------|
| Pydantic V2 Validation | All engine models | HIGH | CORE |
| Provenance Tracking | engine/hydoma/provenance.py | HIGH | CORE |
| Audit Logging | engine/hydoma/audit.py | MEDIUM | IMPORTANT |
| Structlog | All modules | HIGH | OPTIONAL |
| Input Validation | Per-model | HIGH | CORE |

### 11.2 Security Primitive Classification

| Primitive | Classification | Notes |
|----------|----------------|-------|
| Pydantic V2 | CORE | Essential for data validation |
| Provenance | CORE | Essential for integrity |
| Audit Logging | IMPORTANT | Good practice |
| Structlog | OPTIONAL | Enhancement |
| C++ Buffer Safety | CORE | Memory safety at C++ boundary |

---

## 12. Critical Security Findings from ECO-00

Referenced from reports/engine-services/SECURITY-FINDINGS.md:

| Finding | Severity | Status |
|---------|----------|--------|
| Hardcoded secrets in services | CRITICAL | DOCUMENTED |
| SQL injection in services | HIGH | DOCUMENTED |
| Missing input validation in services | MEDIUM | DOCUMENTED |
| Insecure file upload | MEDIUM | DOCUMENTED |
| Missing rate limiting | LOW | DOCUMENTED |
| No HTTPS enforcement | HIGH | DOCUMENTED |

---

## 13. Security Knowledge Extraction

### 13.1 For Scientific Engine

The following should be extracted as reusable security primitives:

1. **Input Validation Patterns** - Extract as validation utilities
   - Range checking
   - Unit validation
   - Physical bounds enforcement
   - NaN/inf handling

2. **Provenance Framework** - Core security primitive
   - Source tracking
   - Method attribution
   - Version tracking

3. **Audit Framework** - Calculation audit trail
   - Computation logging
   - Input/output recording
   - Error/event logging

### 13.2 NOT for Scientific Engine

The following should NOT be part of scientific engine security:

1. Authentication (user management)
2. Authorization (role management)
3. Encryption (data at rest/in motion)
4. API key management
5. Session management

---

## 14. Recommendations

### Immediate Actions
1. ✅ **Document current security primitives** (this report)
2. ⚠️ **Extract input validation** into reusable validation utilities
3. ⚠️ **Ensure provenance tracks all scientific computation**
4. ⚠️ **Add audit trail for model execution**

### Phase 2 (Architecture)
1. **Separate scientific engine security** from infrastructure security
2. **Document security boundary** between computation and infrastructure
3. **Ensure provenance is comprehensive** for all knowledge assets
4. **Add data integrity verification** for critical data

### Phase 3 (Implementation)
1. **Implement data integrity checksums**
2. **Add tamper-evident logging for audit trail**
3. **Add resource limits for scientific computation**

---

## 15. Security Finding Summary

| Category | Findings |
|---------|----------|
| Authentication (engine) | None needed |
| Authorization (engine) | None needed |
| Data Classification | Missing |
| Input Validation | Good (Pydantic + range checks) |
| Audit Logging | Present, needs extension |
| Provenance | Present, high quality |
| Privacy Controls | None (service-level only) |
| Cryptographic Utilities | None (correct) |
| Vulnerability (engine) | 3 medium risks |
| Vulnerability (services) | Multiple critical/high (documented in ECO-00) |

---

## 16. Reusable Security Primitives List

| ID | Name | Location | Classification |
|-----|------|----------|----------------|
| SEC-PRIM-001 | Pydantic V2 Validation | Multiple | CORE |
| SEC-PRIM-002 | Provenance Tracking | engine/hydoma/provenance.py | CORE |
| SEC-PRIM-003 | Input Validation (range/physical) | Multiple models | CORE |
| SEC-PRIM-004 | Audit Logging | engine/hydoma/audit.py | IMPORTANT |
| SEC-PRIM-005 | Structured Logging | All modules (structlog) | OPTIONAL |
| SEC-PRIM-006 | Boundary Buffer Safety | engine/cpp_bridge/ | CORE |

---

*See also: 01-KNOWLEDGE-INVENTORY.md, 10-HYDROMA-FORENSICS.md, 20-CANONICAL-ASSETS.md, 22-LEGACY-DEPENDENCY-STRATEGY.md*