# Diagram 4: Scientific Dependency Chain (Chain-A)

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
