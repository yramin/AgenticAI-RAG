# Agentic RAG System - Infographic Architecture

## Complete System Infographic

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
    
    style UserLayer fill:#e3f2fd,stroke:#1976d2,stroke-width:3px
    style Presentation fill:#f3e5f5,stroke:#7b1fa2,stroke-width:3px
    style APILayer fill:#e8f5e9,stroke:#388e3c,stroke-width:3px
    style Orchestration fill:#fff3e0,stroke:#f57c00,stroke-width:3px
    style Tier1 fill:#e1f5ff,stroke:#0277bd,stroke-width:3px
    style Tier2 fill:#fff4e1,stroke:#ef6c00,stroke-width:3px
    style Tier3 fill:#e8f5e9,stroke:#2e7d32,stroke-width:3px
    style DataLayer fill:#fce4ec,stroke:#c2185b,stroke-width:3px
    style MemoryLayer fill:#f1f8e9,stroke:#558b2f,stroke-width:3px
```

## System Flow Infographic

```mermaid
flowchart TD
    Start([User Query]) --> UI{Streamlit UI}
    UI --> API[FastAPI API<br/>Port 8000]
    API --> Orch{Orchestrator<br/>Select Tier}
    
    Orch -->|Tier 1| T1[Basic RAG]
    Orch -->|Tier 2| T2[Agent + Tools]
    Orch -->|Tier 3| T3[Advanced Agentic]
    
    T1 --> VS[Vector Store<br/>Search Documents]
    VS --> LLM1[LLM Generate<br/>with Context]
    LLM1 --> Response1[Response]
    
    T2 --> Agent[Local Agent]
    Agent --> Mem2[Load Memory]
    Agent --> VS2[Search Documents]
    Agent --> Tools{Use Tools?}
    Tools -->|Yes| ToolExec[Execute Tool<br/>Calc/Web/DB]
    Tools -->|No| Skip
    ToolExec --> LLM2[LLM Generate<br/>with Tools]
    Skip --> LLM2
    VS2 --> LLM2
    Mem2 --> LLM2
    LLM2 --> Store2[Store in Memory]
    Store2 --> Response2[Response]
    
    T3 --> Agg[Aggregator Agent]
    Agg --> Select{Select Agents}
    Select --> Local[Local Agent]
    Select --> Search[Search Agent]
    Select --> Cloud[Cloud Agent]
    
    Local --> VS3[Search Documents]
    Search --> Web[Web Search]
    Cloud --> MCP[MCP Servers]
    
    VS3 --> Results1[Results 1]
    Web --> Results2[Results 2]
    MCP --> Results3[Results 3]
    
    Results1 --> Agg2[Aggregator]
    Results2 --> Agg2
    Results3 --> Agg2
    
    Agg2 --> Plan{Planning}
    Plan --> ReAct[ReAct Planner]
    Plan --> CoT[CoT Planner]
    
    ReAct --> Mem3[Load Memory]
    CoT --> Mem3
    Mem3 --> Synth[Synthesize<br/>Multi-Agent Results]
    Synth --> LLM3[LLM Generate<br/>Final Answer]
    LLM3 --> Store3[Store in Memory]
    Store3 --> Response3[Response]
    
    Response1 --> End([Return to User])
    Response2 --> End
    Response3 --> End
    
    style Start fill:#4caf50,color:#fff
    style End fill:#4caf50,color:#fff
    style T1 fill:#2196f3,color:#fff
    style T2 fill:#ff9800,color:#fff
    style T3 fill:#9c27b0,color:#fff
    style Orch fill:#f44336,color:#fff
    style Agg fill:#9c27b0,color:#fff
```

## Component Stack Infographic

```mermaid
graph LR
    subgraph Frontend["🖥️ FRONTEND"]
        StreamlitUI[Streamlit UI<br/>Port 8501]
    end
    
    subgraph Backend["⚙️ BACKEND"]
        FastAPIServer[FastAPI Server<br/>Port 8000]
    end
    
    subgraph Core["🎯 CORE SYSTEM"]
        OrchestratorCore[Orchestrator]
        ConfigCore[Config Manager]
    end
    
    subgraph Agents["🤖 AGENTS"]
        BaseAgent[Base Agent]
        LocalAgent[Local Agent]
        SearchAgent[Search Agent]
        CloudAgent[Cloud Agent]
        AggAgent[Aggregator Agent]
    end
    
    subgraph Services["🔧 SERVICES"]
        MemoryService[Memory Service]
        PlanningService[Planning Service]
        RetrievalService[Retrieval Service]
        MCPService[MCP Service]
    end
    
    subgraph Storage["💾 STORAGE"]
        ChromaDB[(ChromaDB<br/>Vector Store)]
        FileSystem[File System<br/>Documents]
    end
    
    subgraph External["🌐 EXTERNAL"]
        OpenAI[OpenAI/OpenRouter<br/>LLM & Embeddings]
        WebAPIs[Web APIs<br/>Tavily/Serper]
        CloudStorage[Cloud Storage<br/>AWS S3/GCS]
    end
    
    StreamlitUI --> FastAPIServer
    FastAPIServer --> OrchestratorCore
    OrchestratorCore --> ConfigCore
    OrchestratorCore --> Agents
    Agents --> Services
    Services --> Storage
    Services --> External
    
    BaseAgent --> LocalAgent
    BaseAgent --> SearchAgent
    BaseAgent --> CloudAgent
    AggAgent --> LocalAgent
    AggAgent --> SearchAgent
    AggAgent --> CloudAgent
    
    MemoryService --> ChromaDB
    RetrievalService --> ChromaDB
    RetrievalService --> OpenAI
    MCPService --> CloudStorage
    
    Agents --> OpenAI
    Services --> WebAPIs
    
    style Frontend fill:#e3f2fd
    style Backend fill:#e8f5e9
    style Core fill:#fff3e0
    style Agents fill:#f3e5f5
    style Services fill:#fce4ec
    style Storage fill:#f1f8e9
    style External fill:#fff9c4
```

## Technology Stack Infographic

```mermaid
mindmap
  root((Agentic RAG<br/>System))
    Frontend
      Streamlit
        Chat Interface
        Document Management
        System Monitoring
    Backend
      FastAPI
        REST API
        Async Support
        CORS Enabled
    LLM Integration
      OpenAI
        GPT Models
        Embeddings
      OpenRouter
        Multiple Providers
        Unified API
    Vector Database
      ChromaDB
        Persistent Storage
        Semantic Search
        Collection Management
    Agents
      Base Agent
        Common Functionality
      Specialized Agents
        Local Data
        Web Search
        Cloud Storage
      Aggregator
        Multi-Agent Coordination
    Memory
      Short-term
        Conversation History
        Token Management
      Long-term
        Semantic Memory
        Persistent Context
    Planning
      ReAct
        Reasoning + Acting
        Tool Selection
      Chain-of-Thought
        Multi-step Reasoning
        Plan Generation
    Tools
      Calculator
        Safe Math Operations
      Web Search
        Tavily/Serper
      Database
        SQL Queries
    MCP Servers
      Local Server
        Document Operations
      Search Server
        Web Search Tools
      Cloud Server
        Storage Operations
```

## Data Flow Infographic

```mermaid
graph LR
    subgraph Input["📥 INPUT"]
        UserQuery[User Query]
        Documents[Documents<br/>Text Files]
    end
    
    subgraph Processing["⚙️ PROCESSING"]
        Embed[Embedding<br/>Generation]
        Store[Vector Store<br/>Indexing]
        Search[Semantic<br/>Search]
        Retrieve[Retrieve<br/>Relevant Docs]
    end
    
    subgraph Intelligence["🧠 INTELLIGENCE"]
        Agent[Agent<br/>Processing]
        Plan[Planning<br/>Strategy]
        Memory[Memory<br/>Context]
        Tools[Tool<br/>Execution]
    end
    
    subgraph Generation["✍️ GENERATION"]
        LLM[LLM<br/>OpenAI/OpenRouter]
        Synthesize[Synthesize<br/>Response]
        Format[Format<br/>Output]
    end
    
    subgraph Output["📤 OUTPUT"]
        Answer[Answer to User]
        Sources[Source<br/>Citations]
        Metadata[Response<br/>Metadata]
    end
    
    UserQuery --> Processing
    Documents --> Embed
    Embed --> Store
    Store --> Search
    Search --> Retrieve
    Retrieve --> Intelligence
    UserQuery --> Intelligence
    Intelligence --> Agent
    Agent --> Plan
    Agent --> Memory
    Agent --> Tools
    Plan --> Generation
    Memory --> Generation
    Tools --> Generation
    Retrieve --> Generation
    Generation --> LLM
    LLM --> Synthesize
    Synthesize --> Format
    Format --> Output
    Output --> Answer
    Output --> Sources
    Output --> Metadata
    
    style Input fill:#e3f2fd
    style Processing fill:#e8f5e9
    style Intelligence fill:#fff3e0
    style Generation fill:#f3e5f5
    style Output fill:#fce4ec
```

