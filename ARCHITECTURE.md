# Agentic RAG System Architecture

This document provides detailed architecture diagrams and explanations for the Agentic RAG system.

## Infographic: Complete System Overview

```mermaid
graph TB
    subgraph UserLayer["👤 USER LAYER"]
        User[User]
        Browser[Web Browser]
    end
    
    subgraph Presentation["🎨 PRESENTATION LAYER"]
        Streamlit[Streamlit UI<br/>📊 Dashboard<br/>💬 Chat Interface<br/>📄 Document Management]
    end
    
    subgraph APILayer["🌐 API LAYER"]
        FastAPI[FastAPI Server<br/>RESTful API<br/>Port: 8000]
        Routes["API Endpoints<br/>/query<br/>/health<br/>/agents<br/>/system<br/>/memory"]
    end
    
    subgraph Orchestration["🎯 ORCHESTRATION LAYER"]
        Orchestrator[Orchestrator<br/>Tier Selection<br/>Request Routing<br/>Response Aggregation]
        Config[Configuration Manager<br/>Environment Variables<br/>API Keys<br/>Settings]
    end
    
    subgraph Tier1["📚 TIER 1: BASIC RAG"]
        BasicFlow["Basic RAG Flow"]
        VS1[Vector Store<br/>ChromaDB<br/>Document Search]
        LLM1[LLM<br/>OpenAI/OpenRouter<br/>Answer Generation]
        BasicFlow --> VS1
        VS1 --> LLM1
    end
    
    subgraph Tier2["🤖 TIER 2: AGENT WITH TOOLS"]
        AgentFlow["Agent Processing Flow"]
        LocalAgent2[Local Data Agent<br/>Document Queries]
        ToolsGroup["🛠️ TOOLS"]
        Calc[Calculator<br/>Math Operations]
        WebSearch[Web Search<br/>Tavily/Serper]
        DBQuery[Database Query<br/>SQL Execution]
        Memory2[Memory System<br/>Context Retention]
        LLM2[LLM with Tools<br/>Tool Calling]
        
        AgentFlow --> LocalAgent2
        AgentFlow --> ToolsGroup
        AgentFlow --> Memory2
        ToolsGroup --> Calc
        ToolsGroup --> WebSearch
        ToolsGroup --> DBQuery
        LocalAgent2 --> LLM2
        ToolsGroup --> LLM2
        Memory2 --> LLM2
    end
    
    subgraph Tier3["🚀 TIER 3: ADVANCED AGENTIC"]
        AggFlow["Multi-Agent Flow"]
        Aggregator[Aggregator Agent<br/>Coordinator]
        
        subgraph SpecializedAgents["Specialized Agents"]
            LocalAgent3[Local Data Agent<br/>📁 Local Documents]
            SearchAgent3[Search Agent<br/>🌐 Web Search]
            CloudAgent3[Cloud Agent<br/>☁️ Cloud Storage]
        end
        
        subgraph MCPServers["MCP Servers"]
            LocalMCP[Local MCP Server<br/>Document Operations]
            SearchMCP[Search MCP Server<br/>Web Search Tools]
            CloudMCP[Cloud MCP Server<br/>Storage Operations]
        end
        
        subgraph PlanningSystem["Planning System"]
            ReAct[ReAct Planner<br/>Reasoning + Acting]
            CoT[CoT Planner<br/>Chain-of-Thought]
        end
        
        Memory3[Memory System<br/>Short & Long Term]
        Synthesis[Response Synthesis<br/>Multi-Agent Results]
        LLM3[LLM<br/>Final Answer Generation]
        
        AggFlow --> Aggregator
        Aggregator --> SpecializedAgents
        Aggregator --> MCPServers
        Aggregator --> PlanningSystem
        Aggregator --> Memory3
        SpecializedAgents --> LocalAgent3
        SpecializedAgents --> SearchAgent3
        SpecializedAgents --> CloudAgent3
        MCPServers --> LocalMCP
        MCPServers --> SearchMCP
        MCPServers --> CloudMCP
        PlanningSystem --> ReAct
        PlanningSystem --> CoT
        SpecializedAgents --> Synthesis
        MCPServers --> Synthesis
        PlanningSystem --> Synthesis
        Memory3 --> Synthesis
        Synthesis --> LLM3
    end
    
    subgraph DataLayer["💾 DATA LAYER"]
        VectorStore[Vector Store<br/>ChromaDB<br/>Persistent Storage]
        Embeddings[Embedding Generator<br/>OpenAI/OpenRouter<br/>Text Embeddings]
        Documents[Document Collection<br/>Knowledge Base<br/>Text Files]
    end
    
    subgraph MemoryLayer["🧠 MEMORY LAYER"]
        ShortTerm[Short-term Memory<br/>Conversation History<br/>Token-aware Window]
        LongTerm[Long-term Memory<br/>Semantic Search<br/>Persistent Context]
    end
    
    User --> Browser
    Browser --> Streamlit
    Streamlit --> FastAPI
    FastAPI --> Routes
    Routes --> Orchestrator
    Orchestrator --> Config
    
    Orchestrator --> Tier1
    Orchestrator --> Tier2
    Orchestrator --> Tier3
    
    Tier1 --> DataLayer
    Tier2 --> DataLayer
    Tier3 --> DataLayer
    
    Tier2 --> MemoryLayer
    Tier3 --> MemoryLayer
    
    DataLayer --> VectorStore
    DataLayer --> Embeddings
    DataLayer --> Documents
    Documents --> VectorStore
    Embeddings --> VectorStore
    
    MemoryLayer --> ShortTerm
    MemoryLayer --> LongTerm
    LongTerm --> VectorStore
    
    style UserLayer fill:#e3f2fd
    style Presentation fill:#f3e5f5
    style APILayer fill:#e8f5e9
    style Orchestration fill:#fff3e0
    style Tier1 fill:#e1f5ff
    style Tier2 fill:#fff4e1
    style Tier3 fill:#e8f5e9
    style DataLayer fill:#fce4ec
    style MemoryLayer fill:#f1f8e9
```

## System Overview

The Agentic RAG system is built with a three-tier architecture, progressively adding capabilities from simple retrieval to advanced multi-agent coordination.

## Architecture Diagrams

### High-Level System Architecture

```mermaid
graph TB
    subgraph UI["User Interface Layer"]
        Streamlit[Streamlit UI<br/>Query Interface]
    end
    
    subgraph API["API Layer"]
        FastAPI[FastAPI Server<br/>REST API]
        Routes[API Routes<br/>/query, /health, /agents]
    end
    
    subgraph Orchestrator["Orchestration Layer"]
        OrchestratorCore[Orchestrator<br/>Tier Selection & Coordination]
        Config[Config Manager<br/>Environment Settings]
    end
    
    subgraph Tier1["Tier 1: Basic RAG"]
        BasicRAG[Basic RAG Pipeline]
        VectorStore1[Vector Store<br/>ChromaDB]
        LLM1[LLM<br/>OpenAI/OpenRouter]
    end
    
    subgraph Tier2["Tier 2: Agent with Tools"]
        AgentTools[Local Data Agent<br/>with Tools]
        Tools[Tools<br/>Calculator, Web Search, DB]
        LLM2[LLM<br/>with Tool Calling]
    end
    
    subgraph Tier3["Tier 3: Advanced Agentic"]
        Aggregator[Aggregator Agent<br/>Multi-Agent Coordinator]
        LocalAgent[Local Data Agent]
        SearchAgent[Search Agent]
        CloudAgent[Cloud Agent]
        MCP[MCP Servers<br/>Local, Search, Cloud]
    end
    
    subgraph Memory["Memory System"]
        ShortTerm[Short-term Memory<br/>Conversation Context]
        LongTerm[Long-term Memory<br/>Vector Store]
    end
    
    subgraph Planning["Planning System"]
        ReAct[ReAct Planner<br/>Reasoning + Acting]
        CoT[Chain-of-Thought<br/>Multi-step Reasoning]
    end
    
    subgraph Retrieval["Retrieval System"]
        Embeddings[Embedding Generator<br/>OpenAI/OpenRouter]
        VectorStore2[Vector Store<br/>ChromaDB]
    end
    
    Streamlit --> FastAPI
    FastAPI --> Routes
    Routes --> OrchestratorCore
    OrchestratorCore --> Config
    
    OrchestratorCore --> Tier1
    OrchestratorCore --> Tier2
    OrchestratorCore --> Tier3
    
    BasicRAG --> VectorStore1
    BasicRAG --> LLM1
    
    AgentTools --> Tools
    AgentTools --> LLM2
    AgentTools --> VectorStore1
    
    Aggregator --> LocalAgent
    Aggregator --> SearchAgent
    Aggregator --> CloudAgent
    Aggregator --> MCP
    
    LocalAgent --> VectorStore2
    SearchAgent --> Tools
    CloudAgent --> MCP
    
    Tier2 --> Memory
    Tier3 --> Memory
    Tier3 --> Planning
    
    Memory --> ShortTerm
    Memory --> LongTerm
    LongTerm --> VectorStore2
    
    Planning --> ReAct
    Planning --> CoT
    
    Retrieval --> Embeddings
    Retrieval --> VectorStore2
    VectorStore2 --> Embeddings
    
    style Tier1 fill:#e1f5ff
    style Tier2 fill:#fff4e1
    style Tier3 fill:#e8f5e9
    style Memory fill:#f3e5f5
    style Planning fill:#fce4ec
```

### Request Flow Diagram

```mermaid
sequenceDiagram
    participant User
    participant UI as Streamlit UI
    participant API as FastAPI
    participant Orch as Orchestrator
    participant Agent as Agent Layer
    participant Memory as Memory System
    participant Retrieval as Retrieval System
    participant LLM as LLM/OpenRouter
    participant Tools as Tools
    
    User->>UI: Submit Query
    UI->>API: POST /query
    API->>Orch: Process Query (tier)
    
    alt Tier 1: Basic RAG
        Orch->>Retrieval: Search Documents
        Retrieval->>VectorStore: Semantic Search
        VectorStore-->>Retrieval: Relevant Documents
        Retrieval-->>Orch: Context
        Orch->>LLM: Generate Answer (with context)
        LLM-->>Orch: Response
    else Tier 2: Agent with Tools
        Orch->>Agent: Process with Tools
        Agent->>Memory: Load Context
        Agent->>Retrieval: Search Documents
        Agent->>Tools: Execute Tool (if needed)
        Tools-->>Agent: Tool Result
        Agent->>LLM: Generate Answer
        LLM-->>Agent: Response
        Agent->>Memory: Store Conversation
        Agent-->>Orch: Response
    else Tier 3: Advanced Agentic
        Orch->>Aggregator: Coordinate Agents
        Aggregator->>LocalAgent: Query Local Data
        Aggregator->>SearchAgent: Query Web
        Aggregator->>CloudAgent: Query Cloud
        LocalAgent->>Retrieval: Search Documents
        SearchAgent->>Tools: Web Search
        CloudAgent->>MCP: Cloud Operations
        LocalAgent-->>Aggregator: Response 1
        SearchAgent-->>Aggregator: Response 2
        CloudAgent-->>Aggregator: Response 3
        Aggregator->>Memory: Load Context
        Aggregator->>Planning: Generate Plan
        Planning->>LLM: Synthesize Responses
        LLM-->>Planning: Synthesized Answer
        Planning-->>Aggregator: Final Answer
        Aggregator->>Memory: Store Conversation
        Aggregator-->>Orch: Response
    end
    
    Orch-->>API: Response
    API-->>UI: JSON Response
    UI-->>User: Display Answer
```

### Component Interaction Diagram

```mermaid
graph LR
    subgraph Agents["Agent Types"]
        Base[Base Agent<br/>Common Functionality]
        Local[Local Data Agent<br/>Document Queries]
        Search[Search Agent<br/>Web Search]
        Cloud[Cloud Agent<br/>Cloud Storage]
        Agg[Aggregator Agent<br/>Multi-Agent Coordinator]
    end
    
    subgraph Services["Services"]
        MCP[MCP Servers<br/>Tool Integration]
        Mem[Memory Manager<br/>Context Retention]
        Plan[Planning Engine<br/>ReAct & CoT]
    end
    
    subgraph Data["Data Layer"]
        VS[Vector Store<br/>ChromaDB]
        Embed[Embeddings<br/>OpenAI/OpenRouter]
        Docs[Documents<br/>Knowledge Base]
    end
    
    subgraph Tools["Tools"]
        Calc[Calculator]
        Web[Web Search]
        DB[Database Query]
    end
    
    Base --> Local
    Base --> Search
    Base --> Cloud
    Agg --> Local
    Agg --> Search
    Agg --> Cloud
    
    Local --> VS
    Search --> Web
    Cloud --> MCP
    
    Base --> Mem
    Base --> Plan
    Base --> Tools
    
    Tools --> Calc
    Tools --> Web
    Tools --> DB
    
    VS --> Embed
    Docs --> VS
    Embed --> Docs
    
    style Agents fill:#e3f2fd
    style Services fill:#f1f8e9
    style Data fill:#fff3e0
    style Tools fill:#fce4ec
```

### Three-Tier Architecture Comparison

```mermaid
graph TB
    subgraph T1["Tier 1: Basic RAG"]
        Q1[User Query]
        R1[Retrieve Documents]
        G1[Generate Answer]
        Q1 --> R1 --> G1
    end
    
    subgraph T2["Tier 2: Agent with Tools"]
        Q2[User Query]
        A2[Agent Processes]
        T2_Tools[Use Tools<br/>Calculator, Search, DB]
        M2[Memory Context]
        G2[Generate Answer]
        Q2 --> A2
        A2 --> T2_Tools
        A2 --> M2
        T2_Tools --> G2
        M2 --> G2
    end
    
    subgraph T3["Tier 3: Advanced Agentic"]
        Q3[User Query]
        AG3[Aggregator Agent]
        LA3[Local Agent]
        SA3[Search Agent]
        CA3[Cloud Agent]
        P3[Planning<br/>ReAct/CoT]
        M3[Memory System]
        S3[Synthesize]
        G3[Generate Answer]
        Q3 --> AG3
        AG3 --> LA3
        AG3 --> SA3
        AG3 --> CA3
        AG3 --> P3
        AG3 --> M3
        LA3 --> S3
        SA3 --> S3
        CA3 --> S3
        P3 --> S3
        M3 --> S3
        S3 --> G3
    end
    
    style T1 fill:#e1f5ff
    style T2 fill:#fff4e1
    style T3 fill:#e8f5e9
```

## Component Descriptions

### Tier 1: Basic RAG
- **Purpose**: Simple retrieval and generation
- **Components**: Vector Store, LLM
- **Flow**: Query → Retrieve → Generate
- **Use Case**: Quick answers from document knowledge base

### Tier 2: Agent with Tools
- **Purpose**: Agent with tool capabilities
- **Components**: Local Data Agent, Tools (Calculator, Web Search, Database), Memory
- **Flow**: Query → Agent → Tools/Memory → Generate
- **Use Case**: Complex queries requiring calculations, web search, or database access

### Tier 3: Advanced Agentic
- **Purpose**: Multi-agent coordination with planning
- **Components**: Aggregator Agent, Specialized Agents (Local, Search, Cloud), MCP Servers, Planning, Memory
- **Flow**: Query → Aggregator → Multiple Agents → Planning → Synthesis → Generate
- **Use Case**: Complex queries requiring multiple data sources and sophisticated reasoning

## Key Components

### Agents
- **Base Agent**: Common functionality for all agents
- **Local Data Agent**: Queries local documents via vector store
- **Search Agent**: Performs web searches for current information
- **Cloud Agent**: Accesses cloud storage (AWS S3, GCS)
- **Aggregator Agent**: Coordinates multiple agents and synthesizes responses

### Memory System
- **Short-term Memory**: Recent conversation context (token-aware)
- **Long-term Memory**: Persistent semantic memory in vector store

### Planning System
- **ReAct Planner**: Thought-action-observation loop
- **Chain-of-Thought Planner**: Multi-step reasoning chains

### Retrieval System
- **Embedding Generator**: Creates embeddings using OpenAI/OpenRouter
- **Vector Store**: ChromaDB for semantic search

### Tools
- **Calculator**: Safe mathematical operations
- **Web Search**: Tavily or Serper API integration
- **Database Query**: Safe SQL query execution

### MCP Servers
- **Local Server**: Document operations via MCP protocol
- **Search Server**: Web search via MCP protocol
- **Cloud Server**: Cloud storage operations via MCP protocol

## Data Flow

1. **User Query** → Streamlit UI
2. **UI** → FastAPI (POST /query)
3. **API** → Orchestrator (selects tier)
4. **Orchestrator** → Appropriate tier handler
5. **Tier Handler** → Agents/Tools/Retrieval
6. **Response** → Back through layers to user

## Technology Stack

- **UI**: Streamlit
- **API**: FastAPI
- **LLM**: OpenAI/OpenRouter
- **Vector Store**: ChromaDB
- **Embeddings**: OpenAI/OpenRouter
- **MCP**: Model Context Protocol SDK
- **Language**: Python 3.11+

