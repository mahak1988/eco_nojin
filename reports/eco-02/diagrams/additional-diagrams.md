# Additional Architecture Diagrams

## 8. Knowledge Integration Flow (Daneshyar)
```mermaid
graph TB
    subgraph "Daneshyar Knowledge Engine"
        DKN["Knowledge Types<br/>KT-001 to KT-009"]
        
        KT001["KT-001: Scientific Theory<br/>Trust: HIGH<br/>→ Scientific Engine"]
        KT002["KT-002: Engineering Method<br/>Trust: HIGH<br/>→ Domain Services"]
        KT003["KT-003: Domain Expertise<br/>Trust: MEDIUM<br/>→ Decision Engine"]
        KT004["KT-004: Observational Data<br/>Trust: HIGH<br/>→ Evidence Engine"]
        KT005["KT-005: Empirical Formula<br/>Trust: MEDIUM<br/>→ Scientific Engine"]
        KT006["KT-006: Institutional<br/>Trust: MEDIUM<br/>→ Decision Engine"]
        KT007["KT-007: Regulatory<br/>Trust: HIGH<br/>→ Decision Engine"]
        KT008["KT-008: Indigenous<br/>Trust: MEDIUM<br/>→ Knowledge Layer"]
        KT009["KT-009: AI/ML<br/>Trust: LOW<br/>→ AI Layer (isolated)"]
    end
    
    DKN --> KT001 & KT002 & KT003 & KT004 & KT005 & KT006 & KT007 & KT008 & KT009
    
    KT001 --> SCI["Scientific Engine"]
    KT002 --> DOM["Domain Services"]
    KT003 --> DEC["Decision Engine Tasmimyar"]
    KT004 --> EV["Evidence Engine"]
    KT005 --> SCI
    KT006 --> DEC
    KT007 --> DEC
    KT008 --> KNOWNGE["Knowledge Integration"]
    KT009 --> AI["AI Layer (RESEARCH)"]
    
    style KT001 fill:#4CAF50
    style KT004 fill:#4CAF50
    style KT007 fill:#4CAF50
    style KT003 fill:#FF9800
    style KT005 fill:#FF9800
    style KT006 fill:#FF9800
    style KT008 fill:#FF9800
    style KT009 fill:#9C27B0
    style KT002 fill:#2196F3
```

## 9. Technology Classification Matrix
```mermaid
quadrantChart
    title Technology Classification Framework
    x-axis LOW Investment → HIGH Investment
    y-axis LOW Criticality → HIGH Criticality
    quadrant-1 Research/Optional
    quadrant-2 Important/Medium Investment
    quadrant-3 Legacy/Deprecate
    quadrant-4 CORE/High Investment
    "AI/ML Models": [0.2, 0.3]
    "Weather Research": [0.3, 0.4]
    "Urban Water Demand": [0.4, 0.3]
    "Hargreaves ET": [0.6, 0.7]
    "Penman-Monteith ET0": [0.9, 0.95]
    "FAO-56 Kc Method": [0.8, 0.9]
    "CMIP6 Projections": [0.7, 0.85]
    "MODIS ET": [0.85, 0.8]
    "C++ Kernels": [0.95, 0.95]
    "Python Engine": [0.9, 0.9]
    "Duplicate Models": [0.1, 0.2]
    "Legacy Services": [0.2, 0.3]
```

## 10. Decision Element Relationships
```mermaid
graph LR
    subgraph "Decision Engine (Tasmimyar)"
        DE001["DE-001<br/>Policy Rules"]
        DE002["DE-002<br/>Risk Assessment"]
        DE003["DE-003<br/>Resource Allocation"]
        DE004["DE-004<br/>Trade-off Analysis"]
        DE005["DE-005<br/>Scenario Evaluation"]
        DE006["DE-006<br/>Stakeholder Weighting"]
        DE007["DE-007<br/>Temporal Constraints"]
        DE008["DE-008<br/>Spatial Constraints"]
        DE009["DE-009<br/>Regulatory Compliance"]
        DE010["DE-010<br/>Economic Factors"]
        DE011["DE-011<br/>Environmental Limits"]
    end
    
    EV["Evidence Engine"]
    AI["AI Layer"]
    
    EV --> DE002 & DE003 & DE005 & DE010
    DE006 --> DE004
    DE001 --> DE009
    DE007 --> DE005
    DE008 --> DE003
    DE011 --> DE003
    DE004 --> DE003
    
    DE002 --> AI
    DE004 --> AI
    AI --> DE004
```

## 11. Model Dependency Hierarchy
```mermaid
graph BT
    subgraph "VERIFIED Models"
        A["CANON-001 Penman-Monteith"]
        B["CANON-009 FAO-56"]
        C["CANON-018 CMIP6"]
        D["CANON-020 MODIS ET"]
    end
    
    subgraph "SCIENTIFICALLY_SUPPORTED Models"
        E["CANON-002 Hargreaves"]
        F["CANON-003 Thornthwaite"]
        G["CANON-007 Priestley-Taylor"]
        H["CANON-010 AquaCrop"]
        I["CANON-011 SWAT"]
        J["CANON-013 MODFLOW"]
    end
    
    subgraph "IMPLEMENTATION_VERIFIED Models"
        K["CANON-005 Hargreaves-Samani"]
        L["CANON-006 Makkink"]
        M["CANON-014 WRF"]
        N["CANON-016 RegCM"]
    end
    
    A --> B
    C --> A & E & F
    D -. Validates .-> A
    E --> B
    F --> B
    G --> B
    B --> H
    H --> I
    I --> J
    K --> A
    L --> A
    M --> A
    N --> A
    
    style A fill:#4CAF50,stroke:#388E3C
    style B fill:#4CAF50,stroke:#388E3C
    style C fill:#4CAF50,stroke:#388E3C
    style D fill:#4CAF50,stroke:#388E3C
    style E fill:#FF9800,stroke:#F57C00
    style H fill:#FF9800,stroke:#F57C00
    style I fill:#FF9800,stroke:#F57C00
    style J fill:#FF9800,stroke:#F57C00
    style K fill:#2196F3,stroke:#1976D2
    style M fill:#2196F3,stroke:#1976D2
```

## 12. Hydroma 4-Layer Deep Dive
```mermaid
graph TD
    subgraph "L4: Provenance & Output"
        L4A["Provenance Tracking<br/>Evidence Tags<br/>Metadata"]
    end
    
    subgraph "L3: Integration"
        L3A["Model Coupling<br/>Time Stepping<br/>Data Assembly"]
    end
    
    subgraph "L2: Numerical Computation"
        L2A["C++ Kernels (10 files)<br/>Eigen3 Library<br/>SIMD Optimization"]
    end
    
    subgraph "L1: Scientific Computation"
        L1A["ET Models (7)<br/>Hydrology (3)<br/>Crop Models (3)<br/>Climate (2)<br/>Groundwater (1)"]
    end
    
    L1A -->|"orchestrate"| L2A
    L2A -->|"compute"| L1A
    L1A -->|"emit results"| L3A
    L3A -->|"couple models"| L2A
    L3A -->|"package output"| L4A
    L4A -->|"tag provenance"| L3A
    
    USR["User/API"] -->|"request data"| L3A
    L4A -->|"deliver evidence"| USR
```

## 13. C++ Kernel Architecture
```mermaid
graph TD
    subgraph "C++ Kernel Suite"
        subgraph "ET Calculations"
            ET1["Penman-Monteith"]
            ET2["Hargreaves"]
            ET3["Thornthwaite"]
            ET4["Priestley-Taylor"]
        end
        
        subgraph "Hydrology"
            HY1["Streamflow Routing"]
            HY2["Flood Routing (Muskingum)"]
            HY3["Watershed Modeling (SCS-CN)"]
        end
        
        subgraph "Crop Water"
            CW1["FAO-56 Crop Coefficient"]
            CW2["AquaCrop Implementation"]
            CW3["Irrigation Scheduling"]
        end
        
        subgraph "Groundwater"
            GW1["MODFLOW Interface"]
            GW2["Groundwater Flow"]
            GW3["Aquifer Recharge"]
        end
        
        subgraph "Climate"
            CL1["Climate Interpolation"]
            CL2["Downscaling"]
            CL3["Bias Correction"]
        end
        
        subgraph "Utilities"
            UT1["Optimization (Pareto)"]
            UT2["Interpolation (IDW/Kriging)"]
            UT3["Statistics Library"]
        end
    end
    
    PY["Python Engine"] -->|"ctypes calls"| ET1 & HY1 & CW1 & GW1 & CL1 & UT1
    
    style ET1 fill:#4CAF50
    style HY1 fill:#4CAF50
    style CW1 fill:#4CAF50
    style GW1 fill:#4CAF50
    style CL1 fill:#4CAF50
```

## 14. Service Consolidation Before/After
```mermaid
pie showData
    title Current 73 Services Distribution
    "Infrastructure (45)" : 45
    "Domain (28)" : 28

pie showData
    title Target 8 Bounded Contexts
    "Platform Core (25)" : 25
    "Meteorology (8)" : 8
    "Hydrology (6)" : 6
    "AgriWater (5)" : 5
    "Evidence (4)" : 4
    "Decision (3)" : 3
    "Remote Sensing (5)" : 5
    "Reporting (2)" : 2
```

## 15. Architecture Compliance Dashboard
```mermaid
graph LR
    subgraph "Compliance Metrics"
        V1["Import Guards<br/>100% enforced<br/>✅"]
        V2["AI Isolation<br/>100% enforced<br/>✅"]
        V3["Unit Consistency<br/>100% UNIFORMAT<br/>✅"]
        V4["Model Maturity<br/>All classified<br/>✅"]
        V5["Evidence Chain<br/>All tagged<br/>✅"]
        V6["Canonical Assets<br/>All mapped<br/>✅"]
        V7["Test Coverage<br/>C++: 85% avg<br/>Python: TBD"]
        V8["Boundary Compliance<br/>All violations fixed<br/>✅"]
    end
    
    V1 --> V2 --> V3 --> V4 --> V5 --> V6 --> V7 --> V8
    
    style V1 fill:#4CAF50
    style V2 fill:#4CAF50
    style V3 fill:#4CAF50
    style V4 fill:#4CAF50
    style V5 fill:#4CAF50
    style V6 fill:#4CAF50
    style V7 fill:#FF9800
    style V8 fill:#4CAF50
```
