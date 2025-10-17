```mermaid
flowchart LR
  subgraph UI[Presentation Layer]
    VUE[Vue + Tailwind UI\n(Westeros Dashboard)]
  end

  subgraph EDGE[Edge & API]
    BFF[Gateway API (BFF)\nREST + WS/SSE]
    AUTH[Auth (OIDC)]
    RL[Rate Limiter / API Keys]
  end

  subgraph RUNTIME[Agent Runtime (ADK)]
    IB[IronBank Agent\npolicy/pricing/risk]
    ENF[Enforcer / Orchestrator]
    STK[House Stark Agent]
    LAN[House Lannister Agent]
    TAR[House Targaryen Agent]
    NW[Night's Watch Agent]
  end

  subgraph PROTO[Protocol Adapters]
    A2A[A2A Broker\nrouting + signatures]
    MCP[MCP Router\nknowledge tools]
    APP[Agents Payment Protocol\nsettlement adapter]
  end

  subgraph DATA[Data & Messaging]
    BUS[Event Bus / Log\n(NATS/Kafka/Redis Streams)]
    LEDGER[Ledger DB\n(Postgres/SQLite)]
    STATE[World State DB\n(Postgres/SQLite)]
    CACHE[Cache (Redis)]
    SECRETS[Secrets/Config (Secret Manager)]
    OBS[Observability (OpenTelemetry)]
  end

  VUE <-- REST / WS-SSE --> BFF
  AUTH --> BFF
  RL --> BFF
  BFF --> IB
  BFF --> BUS
  BUS --> BFF
  BFF --> VUE

  IB --> ENF

  %% Agents -> Protocols
  STK --> A2A
  LAN --> A2A
  TAR --> A2A
  NW  --> A2A
  ENF --> A2A
  IB  --> A2A

  STK --> MCP
  LAN --> MCP
  TAR --> MCP
  NW  --> MCP
  ENF --> MCP
  IB  --> MCP

  STK --> APP
  LAN --> APP
  TAR --> APP
  NW  --> APP
  ENF --> APP
  IB  --> APP

  %% Protocols -> Data
  APP --> LEDGER
  A2A --> BUS
  MCP --> STATE

  %% Feedback to agents
  STATE --> IB
  LEDGER --> IB

  %% Infra bits
  CACHE --> BFF
  SECRETS --> BFF
  SECRETS --> APP

  %% Observability
  BFF -. traces/metrics .-> OBS
  IB  -.-> OBS
  ENF -.-> OBS
  STK -.-> OBS
  LAN -.-> OBS
  TAR -.-> OBS
  NW  -.-> OBS
  A2A -.-> OBS
  MCP -.-> OBS
  APP -.-> OBS
```

