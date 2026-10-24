# Canonical Architecture Diagrams (Mermaid)

## 1. Layered Architecture
```mermaid
graph TD
    subgraph "Layer 9: C++ Numerical Kernels"
        A["C++ Kernels<br/>et_calculations.cpp<br/>hydrology.cpp<br/>crop_water.cpp<br/>groundwater.cpp<br/>etc. (10 files)"]
    end
    
    subgraph "Layer 8: Scientific Engine"
        B["Hydroma Scientific Engine<br/>Python orchestration<br/>22 models (VERIFIED→STUB)"]
    end
    
    subgraph "Layer 7: Engine Gateway"
        C["Engine Gateway<br/>ctypes / pybind11 / buffer<br/>UNIFORMAT units"]
    end
    
    subgraph "Layer 6: Domain Services"
        D["Hydroma Domain Services<br/>Meteorology<br/>Hydrology<br/>AgriWater<br/>Remote Sensing<br/>Consolidated bounded contexts"]
    end
    
    subgraph "Layer 5: Evidence Engine"
        E["Evidence Engine<br/>Provenance tracking<br/>Trust level assignment<br/>Validation pipeline"]
    end
    
    subgraph "Layer 4: Knowledge (Daneshyar)"
        F["Knowledge Engine<br/>9 Knowledge Types<br/>CANON-XXX assets"]
    end
    
    subgraph "Layer 3: Decision (Tasmimyar)"
        G["Decision Engine<br/>11 Decision Elements<br/>Policy evaluation"]
    end
    
    subgraph "Layer 2: Application Orchestration"
        H["Application Orchestration<br/>API Gateway<br/>Workflow coordination"]
    end
    
    subgraph "Layer 1: Product Experience"
        I["Product Experience<br/>User Interfaces<br/>Reports<br/>(Out of scope per ECO-01)"]
    end
    
    subgraph "AI Layer (RESEARCH/OPTIONAL)"
        J["AI Layer<br/>Experimental<br/>Isolated from core"]
    end
    
    A -->|ctypes/buffer| C
    B -->|orchestration| C
    C -->|delegates| B
    B -->|computation| A
    D -->|domain calls| C
    E -->|validates| D
    D -->|emits evidence| E
    F -->|knowledge feed| E
    F -->|policy input| G
    G -->|decisions| H
    G -->|validated evidence| E
    H -->|API orchestration| I
    J -->|isolated input| E
    E -->|validated data| G
    G -->|filtered output| J
```

## 2. C++/Python Boundary Protocol
```mermaid
sequenceDiagram
    participant P as Python Engine
    participant G as Engine Gateway
    participant C as C++ Kernel
    participant E as Evidence Engine
    
    P->>G: compute_et(method="penman-monteith", data=array)
    G->>G: Validate SI units (UNIFORMAT)
    G->>C: ctypes call / buffer protocol
    Note over C: Zero-copy array operation
    C-->>G: Return result (float64)
    G->>G: Attach provenance tag
    G-->>P: Return result + evidence_tag
    P->>E: emit_evidence(evidence_item)
    E-->>P: evidence_id
```

## 3. Evidence Chain Flow
```mermaid
flowchart LR
    subgraph "Scientific Core"
        SCI["Scientific Engine<br/>(Hydroma)"]
    end
    
    subgraph "Provenance Layer"
        EV["Evidence Engine<br/>(Validation + Tags)"]
    end
    
    subgraph "Decision Layer"
        DEC["Decision Engine<br/>(Tasmimyar)"]
    end
    
    subgraph "Optional Layer"
        AI["AI Layer<br/>(RESEARCH)"]
    end
    
    subgraph "Consumer Layer"
        USR["User Interface"]
    end
    
    SCI -->|1. Emit raw computation| EV
    EV -->|2. Validate + provenance tag| DEC
    DEC -->|3. Decision with trust| AI
    AI -->|4. Augmented recommendation| USR
    EV -->|5. Bypass check| USR
    
    style SCI fill:#4CAF50
    style EV fill:#2196F3
    style DEC fill:#FF9800
    style AI fill:#9C27B0
    style USR fill:#F44336
    
    classDef core fill:#4CAF50;
    classDef evidence fill:#2196F3;
    classDef decision fill:#FF9800;
    classDef research fill:#9C27B0;
```

## 4. Scientific Dependency Chain (Chain-A)
```mermaid
graph TB
    subgraph "Level 1: Climate Forcing"
        CMIP6["CMIP6<br/>(CANON-018)<br/>VERIFIED"]
        WRF["WRF<br/>(CANON-014)<br/>IMPLEMENTATION_VERIFIED"]
        RegCM["RegCM<br/>(CANON-016)<br/>IMPLEMENTATION_VERIFIED"]
        HadGEM2["HadGEM2<br/>(CANON-017)<br/>IMPLEMENTATION_VERIFIED"]
    end
    
    subgraph "Level 2: Reference ET"
        PM["Penman-Monteith<br/>(CANON-001)<br/>VERIFIED"]
        Harg["Hargreaves<br/>(CANON-002)<br/>SCIENTIFICALLY_SUPPORTED"]
        Thorn["Thornthwaite<br/>(CANON-003)<br/>SCIENTIFICALLY_SUPPORTED"]
        HS["Hargreaves-Samani<br/>(CANON-005)<br/>IMPLEMENTATION_VERIFIED"]
        Makk["Makkink<br/>(CANON-006)<br/>IMPLEMENTATION_VERIFIED"]
        PT["Priestley-Taylor<br/>(CANON-007)<br/>SCIENTIFICALLY_SUPPORTED"]
        JH["Jensen-Haise<br/>(CANON-008)<br/>SCIENTIFICALLY_SUPPORTED"]
    end
    
    subgraph "Level 3: Water Demand"
        FAO56["FAO-56 Kc<br/>(CANON-009)<br/>VERIFIED"]
        BC["Blaney-Crop<br/>(CANON-004)<br/>SCIENTIFICALLY_SUPPORTED"]
    end
    
    subgraph "Level 4: Irrigation"
        AC["AquaCrop<br/>(CANON-010)<br/>SCIENTIFICALLY_SUPPORTED"]
        SWAT["SWAT<br/>(CANON-011)<br/>SCIENTIFICALLY_SUPPORTED"]
    end
    
    subgraph "Level 5: Groundwater"
        MODFLOW["MODFLOW<br/>(CANON-013)<br/>SCIENTIFICALLY_SUPPORTED"]
    end
    
    subgraph "Level 6: Remote Sensing"
        MODIS["MODIS ET<br/>(CANON-020)<br/>VERIFIED"]
        Landsat["Landsat<br/>(CANON-021)<br/>VERIFIED"]
        Sentinel["Sentinel-2<br/>(CANON-022)<br/>VERIFIED"]
    end
    
    CMIP6 --> PM & Harg & Thorn
    WRF --> PM & HS
    RegCM --> PM & Thorn
    HadGEM2 --> PM
    
    PM --> FAO56
    Harg --> BC
    Thorn --> BC
    
    FAO56 --> AC & SWAT
    BC --> AC
    
    SWAT --> MODFLOW
    AC --> MODFLOW
    
    MODIS -. Validates .-> PM
    Landsat -. Validates .-> Land use
    Sentinel -. Validates .-> AC
```

## 5. Service Consolidation Target
```mermaid
graph TD
    subgraph "Current: 73 Services"
        OLD["Infrastructure (45)<br/>Domain (28)"]
    end
    
    subgraph "Target: 8 Bounded Contexts"
        subgraph "Platform Core (25 services → 1 module)"
            PC["Config<br/>Logging<br/>Database<br/>Monitoring"]
        end
        
        subgraph "Meteorology (8 services → 1 module)"
            MET["Weather API<br/>Climate data<br/>Interpolation"]
        end
        
        subgraph "Hydrology (6 services → 1 module)"
            HYD["Streamflow<br/>Flood routing<br/>Watershed"]
        end
        
        subgraph "AgriWater (5 services → 1 module)"
            AGW["ET Calculation<br/>Crop water<br/>Irrigation"]
        end
        
        subgraph "Evidence Provenance (4 services → 1 module)"
            EVID["Audit trail<br/>Validation<br/>Tagging"]
        end
        
        subgraph "Decision Engine (3 services → 1 module)"
            DEC["Policy eval<br/>Risk assessment<br/>Optimization"]
        end
        
        subgraph "Remote Sensing (5 services → 1 module)"
            RS["Satellite data<br/>Image processing<br/>Validation"]
        end
        
        subgraph "Reporting (2 services → 1 module)"
            REP["Output generation<br/>Visualization"]
        end
    end
    
    OLD -->|"Consolidation"| PC & MET & HYD & AGW & EVID & DEC & RS & REP
    
    style PC fill:#2196F3
    style MET fill:#4CAF50
    style HYD fill:#4CAF50
    style AGW fill:#4CAF50
    style EVID fill:#FF9800
    style DEC fill:#FF9800
    style RS fill:#4CAF50
    style REP fill:#9C27B0
```

## 6. Boundary Violation Prevention
```mermaid
graph LR
    subgraph "Allowed Imports"
        S["services/"] -- "imports via Gateway" --> G["Engine Gateway"]
        G -- "ctypes/buffer" --> E["C++ Engine"]
        AI["ai/"] -- "only through" --> V["Evidence Engine"]
        V -- "validates AI inputs" --> DEC["Decision Engine"]
    end
    
    subgraph "Blocked Imports (ECO-LEGACY-001)"
        S -- X -- direct["engine/ (BLOCKED)"]
        AI -- X -- sci["Scientific Engine (BLOCKED)"]
        AI -- X -- cppc["C++ Kernels (BLOCKED)"]
    end
    
    style direct fill:#f44336,stroke:#f44336,color:white
    style sci fill:#f44336,stroke:#f44336,color:white
    style cppc fill:#f44336,stroke:#f44336,color:white
```

## 7. Evidence Tag Lifecycle
```mermaid
stateDiagram-v2
    [*] --> RawComputation: Scientific Engine emits
    RawComputation --> UnitValidation: UNIFORMAT check
    UnitValidation --> TrustAssignment: Model maturity
    TrustAssignment --> ProvenanceStorage: Evidence Engine
    ProvenanceStorage --> EvidenceDistribution: To consumers
    EvidenceDistribution --> DecisionEngine: HIGH/MEDIUM trust
    EvidenceDistribution --> AILayer: LOW trust ONLY
    DecisionEngine --> User: Decision with confidence
    AILayer --> DecisionEngine: AI recommendation
    EvidenceDistribution --> KnowledgeEngine: Validated knowledge
    KnowledgeEngine --> DecisionEngine: Policy inputs
```
