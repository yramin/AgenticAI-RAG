# Agentic RAG System

A production-ready Agentic Retrieval-Augmented Generation (RAG) system with multiple specialized agents, MCP servers, memory management, and planning capabilities.

## Architecture

The system implements three progressive tiers:

1. **Basic RAG**: Simple retrieval and generation pipeline
2. **AI Agent with Tools**: Agent that can use tools (calculator, web search, database)
3. **Advanced Agentic RAG**: Multi-agent system with MCP servers, memory, and planning

> 📊 **For detailed infographic diagrams, see [INFographic.md](INFographic.md)**

### System Architecture Diagram

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

### Data Flow Diagram

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

## Features

- **Multi-Agent System**: Specialized agents for local data, web search, and cloud storage
- **MCP Servers**: Model Context Protocol servers for tool integration
- **Memory Management**: Short-term and long-term memory for context retention
- **Planning Capabilities**: ReAct and Chain-of-Thought planning strategies
- **Vector Store**: ChromaDB integration for semantic search
- **REST API**: FastAPI-based API for programmatic access
- **Web UI**: Streamlit dashboard for interactive queries

## Project Structure

```
agentic-rag-system/
├── src/
│   ├── agents/          # Agent implementations
│   ├── memory/          # Memory management
│   ├── mcp/             # MCP servers
│   ├── planning/         # Planning strategies
│   ├── retrieval/        # Retrieval system
│   ├── tools/            # Agent tools
│   └── core/             # Core orchestration
├── api/                  # FastAPI application
├── ui/                   # Streamlit UI
├── tests/                # Test suite
└── data/                 # Data storage
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd AgenticAI-RAG
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

5. Create necessary directories:
```bash
mkdir -p data/chroma_db data/sample_documents
```

6. Add documents to the vector store (optional but recommended):
```bash
# Add sample documents
python scripts/add_documents.py --sample-docs

# Or add your own documents
python scripts/add_documents.py --file your_document.txt
python scripts/add_documents.py --directory data/sample_documents
```

## Configuration

Copy `.env.example` to `.env` and configure:

- **OpenAI/OpenRouter API Key**: Required for LLM and embeddings
  - For **OpenAI**: Leave `OPENAI_BASE_URL` empty or unset
  - For **OpenRouter**: Set `OPENAI_BASE_URL=https://openrouter.ai/api/v1` and use your OpenRouter API key
  - For OpenRouter, model names should include the provider prefix (e.g., `openai/gpt-4-turbo-preview`)
- **ChromaDB Path**: Local path for vector database
- **Web Search API**: Optional (Tavily or Serper)
- **Database URL**: Optional for database query tool
- **Cloud Storage**: Optional (AWS S3 or GCS)
- **Snowflake**: Optional for Snowflake data warehouse queries

## Usage

### Running the API Server

**Important:** The API server must be running before using the Streamlit UI.

You can run the API in several ways:

**Option 1: Using the startup script (recommended)**
```bash
./scripts/start_api.sh
```

**Option 2: From project root**
```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Option 3: From api directory**
```bash
cd api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### Running the Streamlit UI

**Note:** Make sure the API server is running first (see above).

**Option 1: Using the startup script (recommended)**
```bash
./scripts/start_ui.sh
```

**Option 2: Direct command**
```bash
streamlit run ui/streamlit_app.py
```

The UI will be available at `http://localhost:8501`

### Running Both Servers

You need to run both servers in separate terminal windows:

**Terminal 1 - API Server:**
```bash
./scripts/start_api.sh
```

**Terminal 2 - Streamlit UI:**
```bash
./scripts/start_ui.sh
```

### API Endpoints

- `POST /query`: Main query endpoint
  ```json
  {
    "query": "Your question here",
    "tier": "basic" | "agent" | "advanced",
    "session_id": "optional-session-id"
  }
  ```

- `GET /health`: Health check
- `GET /agents`: Agent status
- `GET /memory/{session_id}`: Get memory for session

## Development

### Running Tests

```bash
pytest tests/
```

### Adding Documents

You can add documents to the vector store in several ways:

**Option 1: Using the Streamlit UI (Easiest)**
1. Start the Streamlit UI (see above)
2. Go to the "Documents" tab
3. Use one of the following methods:
   - Click "Add Sample Documents" for quick start
   - Paste text directly and click "Add Text"
   - Upload text files (.txt, .md, .py, .json)
   - Add all files from a directory

**Option 2: Using Command Line Scripts**

```bash
# Add sample documents
python scripts/add_documents.py --sample-docs

# Add specific files
python scripts/add_documents.py --file doc1.txt doc2.txt

# Add all files from a directory
python scripts/add_documents.py --directory data/sample_documents

# Add text directly
python scripts/add_documents.py --text "Your document text here"
```

**Option 3: Programmatically**

```python
from src.retrieval.vector_store import get_vector_store

vector_store = get_vector_store()
vector_store.add_documents(
    documents=["Document text 1", "Document text 2"],
    metadatas=[{"source": "doc1"}, {"source": "doc2"}]
)
```

**Supported File Types:**
- `.txt` - Plain text files
- `.md` - Markdown files
- `.py` - Python files
- `.json` - JSON files

Large documents are automatically chunked for better retrieval.

## System Tiers

### Tier 1: Basic RAG
Simple retrieval and generation without agent capabilities.

### Tier 2: AI Agent with Tools
Single agent that can use tools (calculator, web search, database queries).

### Tier 3: Advanced Agentic RAG
Multi-agent system with:
- Specialized agents (local, search, cloud)
- MCP servers for tool integration
- Memory management (short-term and long-term)
- Planning strategies (ReAct, CoT)
- Response aggregation

## License

MIT License

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

