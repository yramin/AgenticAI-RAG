"""Streamlit UI for Agentic RAG System."""

import streamlit as st
import json
import os
import sys
import asyncio
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import orchestrator and memory directly
from src.core.orchestrator import get_orchestrator
from src.memory.long_term_memory import LongTermMemory

# Page configuration
st.set_page_config(
    page_title="Agentic RAG System",
    page_icon="🤖",
    layout="wide",
)


@st.cache_resource
def get_orchestrator_instance():
    """Get cached orchestrator instance."""
    return get_orchestrator()


def query_api(query: str, tier: str, session_id: Optional[str] = None) -> dict:
    """Query the orchestrator directly (no HTTP needed)."""
    try:
        orchestrator = get_orchestrator_instance()
        # Run async function in sync context
        # Use nest_asyncio to handle event loops in Streamlit
        try:
            import nest_asyncio
            nest_asyncio.apply()
        except ImportError:
            pass  # If not available, try without it
        
        # Try to run the async function
        try:
            # Check if there's a running loop
            asyncio.get_running_loop()
            # If we get here, there's a running loop - nest_asyncio should handle it
            response = asyncio.run(
                orchestrator.process_query(
                    query=query,
                    tier=tier,
                    session_id=session_id,
                )
            )
        except RuntimeError:
            # No running loop, safe to use asyncio.run
            response = asyncio.run(
                orchestrator.process_query(
                    query=query,
                    tier=tier,
                    session_id=session_id,
                )
            )
        return response
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_agent_status() -> dict:
    """Get agent status directly from orchestrator."""
    try:
        orchestrator = get_orchestrator_instance()
        return orchestrator.get_agent_status()
    except Exception as e:
        return {"error": str(e)}


def get_system_info() -> dict:
    """Get system information directly from orchestrator."""
    try:
        orchestrator = get_orchestrator_instance()
        return orchestrator.get_system_info()
    except Exception as e:
        return {"error": str(e)}


def main():
    """Main Streamlit app."""
    st.title("🤖 Agentic RAG System")
    st.markdown("Production-ready RAG system with multiple agents and MCP servers")

    # Initialize session state
    if "session_id" not in st.session_state:
        import uuid
        st.session_state.session_id = str(uuid.uuid4())
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []

    # Sidebar
    with st.sidebar:
        st.header("Configuration")
        
        # Tier selection
        tier = st.selectbox(
            "Select Tier",
            ["basic", "agent", "advanced"],
            help="Basic: Simple RAG | Agent: With Tools | Advanced: Multi-Agent",
        )

        st.markdown("---")
        st.header("System Status")
        
        # System info
        if st.button("Refresh Status"):
            system_info = get_system_info()
            if "error" not in system_info:
                st.json(system_info)
            else:
                st.error(f"Error: {system_info['error']}")

        # Agent status
        agent_status = get_agent_status()
        if "error" not in agent_status:
            st.subheader("Agents")
            for agent_name, status in agent_status.get("agents", {}).items():
                with st.expander(agent_name.upper()):
                    st.json(status)

        st.markdown("---")
        st.markdown(f"**Session ID:** `{st.session_state.session_id}`")
        
        if st.button("New Session"):
            import uuid
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.conversation_history = []
            st.rerun()

    # Main content area
    tab1, tab2, tab3, tab4 = st.tabs(["💬 Chat", "📊 System Info", "🧠 Memory", "📄 Documents"])

    with tab1:
        st.header("Query Interface")

        # Display conversation history
        if st.session_state.conversation_history:
            st.subheader("Conversation History")
            for i, entry in enumerate(st.session_state.conversation_history):
                with st.expander(f"Query {i+1}: {entry['query'][:50]}..."):
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        st.markdown("**Query:**")
                        st.text(entry["query"])
                        st.markdown(f"**Tier:** {entry['tier']}")
                    with col2:
                        st.markdown("**Response:**")
                        if entry["response"].get("success"):
                            st.success(entry["response"].get("answer", "No answer"))
                        else:
                            st.error(entry["response"].get("error", "Unknown error"))

        # Query input
        st.markdown("---")
        query = st.text_area(
            "Enter your query:",
            height=100,
            placeholder="Ask a question...",
        )

        col1, col2 = st.columns([1, 4])
        with col1:
            submit_button = st.button("Submit", type="primary", use_container_width=True)

        if submit_button and query:
            with st.spinner("Processing query..."):
                response = query_api(
                    query=query,
                    tier=tier,
                    session_id=st.session_state.session_id,
                )

                # Add to conversation history
                st.session_state.conversation_history.append({
                    "query": query,
                    "tier": tier,
                    "response": response,
                })

                # Display response
                if response.get("success"):
                    st.success("✅ Query processed successfully!")
                    st.markdown("### Answer:")
                    st.markdown(response.get("answer", "No answer provided"))

                    # Show sources if available
                    if response.get("sources"):
                        with st.expander("Sources"):
                            for source in response["sources"]:
                                st.json(source)

                    # Show metadata
                    with st.expander("Response Metadata"):
                        metadata = {k: v for k, v in response.items() if k not in ["answer", "sources"]}
                        st.json(metadata)
                else:
                    st.error(f"❌ Error: {response.get('error', 'Unknown error')}")

                st.rerun()

    with tab2:
        st.header("System Information")

        if st.button("Refresh System Info"):
            system_info = get_system_info()
            if "error" not in system_info:
                st.json(system_info)

                # Display key metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(
                        "Documents",
                        system_info.get("vector_store", {}).get("document_count", 0),
                    )
                with col2:
                    tools_count = sum(
                        1 for v in system_info.get("tools", {}).values() if v
                    )
                    st.metric("Active Tools", tools_count)
                with col3:
                    st.metric("Model", system_info.get("model", "Unknown"))
            else:
                st.error(f"Error: {system_info['error']}")

    with tab3:
        st.header("Memory Management")

        session_id = st.text_input(
            "Session ID",
            value=st.session_state.session_id,
        )

        if st.button("Load Memory"):
            try:
                long_term_memory = LongTermMemory()
                memories = long_term_memory.get_session_memories(session_id, limit=50)
                
                st.metric("Memories", len(memories))

                if memories:
                    st.subheader("Memory Entries")
                    for memory in memories:
                        memory_id = memory.get('id', 'Unknown')
                        with st.expander(f"Memory: {str(memory_id)[:8]}..."):
                            st.text(memory.get("content", ""))
                            st.json(memory.get("metadata", {}))
            except Exception as e:
                st.error(f"Error loading memory: {e}")

        if st.button("Clear Memory", type="secondary"):
            try:
                long_term_memory = LongTermMemory()
                deleted_count = long_term_memory.delete_session_memories(session_id)
                st.success(f"Deleted {deleted_count} memories")
            except Exception as e:
                st.error(f"Error clearing memory: {e}")

    with tab4:
        st.header("Document Management")
        st.markdown("Add documents to the vector store for RAG queries.")
        
        # Get document count
        try:
            system_info = get_system_info()
            if "error" not in system_info:
                doc_count = system_info.get("vector_store", {}).get("document_count", 0)
                st.metric("Documents in Vector Store", doc_count)
            else:
                st.warning(f"Could not fetch document count: {system_info.get('error')}")
                doc_count = 0
        except Exception as e:
            st.warning(f"Could not fetch document count: {e}")
            doc_count = 0
        
        st.markdown("---")
        
        # Option 1: Add sample documents
        st.subheader("Quick Start: Add Sample Documents")
        st.markdown("Add pre-configured sample documents about Oracle Exadata migration.")
        if st.button("Add Sample Documents", type="primary"):
            try:
                import subprocess
                result = subprocess.run(
                    ["python", "scripts/add_documents.py", "--sample-docs"],
                    capture_output=True,
                    text=True,
                    cwd=Path(__file__).parent.parent
                )
                if result.returncode == 0:
                    st.success("✅ Sample documents added successfully!")
                    st.code(result.stdout)
                    st.rerun()
                else:
                    st.error(f"Error: {result.stderr}")
            except Exception as e:
                st.error(f"Error adding sample documents: {e}")
        
        st.markdown("---")
        
        # Option 2: Add text directly
        st.subheader("Add Text Documents")
        text_input = st.text_area(
            "Enter document text:",
            height=200,
            placeholder="Paste your document text here...",
        )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            add_text_button = st.button("Add Text", type="primary")
        
        if add_text_button and text_input:
            try:
                import subprocess
                # Escape the text for command line
                import shlex
                result = subprocess.run(
                    ["python", "scripts/add_documents.py", "--text"] + [text_input],
                    capture_output=True,
                    text=True,
                    cwd=Path(__file__).parent.parent
                )
                if result.returncode == 0:
                    st.success("✅ Document added successfully!")
                    st.code(result.stdout)
                    st.rerun()
                else:
                    st.error(f"Error: {result.stderr}")
            except Exception as e:
                st.error(f"Error adding document: {e}")
        
        st.markdown("---")
        
        # Option 3: Upload files
        st.subheader("Upload Text Files")
        uploaded_files = st.file_uploader(
            "Choose text files to upload",
            type=["txt", "md", "py", "json"],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            if st.button("Add Uploaded Files", type="primary"):
                try:
                    import tempfile
                    import subprocess
                    
                    file_paths = []
                    with tempfile.TemporaryDirectory() as tmpdir:
                        for uploaded_file in uploaded_files:
                            file_path = os.path.join(tmpdir, uploaded_file.name)
                            with open(file_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            file_paths.append(file_path)
                        
                        result = subprocess.run(
                            ["python", "scripts/add_documents.py", "--file"] + file_paths,
                            capture_output=True,
                            text=True,
                            cwd=Path(__file__).parent.parent
                        )
                        
                        if result.returncode == 0:
                            st.success(f"✅ Added {len(uploaded_files)} file(s) successfully!")
                            st.code(result.stdout)
                            st.rerun()
                        else:
                            st.error(f"Error: {result.stderr}")
                except Exception as e:
                    st.error(f"Error adding files: {e}")
        
        st.markdown("---")
        
        # Option 4: Add from directory
        st.subheader("Add Documents from Directory")
        st.markdown("Add all text files from a directory (e.g., `data/sample_documents`)")
        directory_path = st.text_input(
            "Directory path:",
            value="data/sample_documents",
            placeholder="data/sample_documents",
        )
        
        if st.button("Add from Directory"):
            if directory_path:
                try:
                    import subprocess
                    result = subprocess.run(
                        ["python", "scripts/add_documents.py", "--directory", directory_path],
                        capture_output=True,
                        text=True,
                        cwd=Path(__file__).parent.parent
                    )
                    if result.returncode == 0:
                        st.success("✅ Documents from directory added successfully!")
                        st.code(result.stdout)
                        st.rerun()
                    else:
                        st.error(f"Error: {result.stderr}")
                except Exception as e:
                    st.error(f"Error adding from directory: {e}")
            else:
                st.warning("Please enter a directory path")
        
        st.markdown("---")
        
        # Instructions
        with st.expander("📖 How to Add Documents"):
            st.markdown("""
            ### Methods to Add Documents:
            
            1. **Sample Documents**: Click "Add Sample Documents" to add pre-configured example documents.
            
            2. **Text Input**: Paste text directly into the text area and click "Add Text".
            
            3. **File Upload**: Upload `.txt`, `.md`, `.py`, or `.json` files using the file uploader.
            
            4. **Directory**: Specify a directory path containing text files to add all files at once.
            
            ### Command Line Alternative:
            
            You can also add documents using the command line:
            
            ```bash
            # Add sample documents
            python scripts/add_documents.py --sample-docs
            
            # Add specific files
            python scripts/add_documents.py --file doc1.txt doc2.txt
            
            # Add from directory
            python scripts/add_documents.py --directory data/sample_documents
            
            # Add text directly
            python scripts/add_documents.py --text "Your document text here"
            ```
            
            ### Tips:
            - Documents are automatically chunked if they're too large
            - Each document can have metadata (source, type, etc.)
            - After adding documents, queries will search through them
            - The vector store uses semantic search to find relevant documents
            """)


if __name__ == "__main__":
    main()

