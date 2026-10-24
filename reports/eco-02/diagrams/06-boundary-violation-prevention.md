# Diagram 6: Boundary Violation Prevention

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
