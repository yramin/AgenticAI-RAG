"""Script to add sample documents to the vector store."""

import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Lazy import to avoid issues when module is scanned but not used
def _get_vector_store():
    """Lazy import of vector store."""
    try:
        from src.retrieval.vector_store import get_vector_store
        return get_vector_store()
    except ImportError as e:
        raise ImportError(
            f"Failed to import vector store. Make sure all dependencies are installed. "
            f"Original error: {e}"
        )

def add_sample_documents():
    """Add sample documents to the vector store."""
    vector_store = _get_vector_store()
    
    sample_docs = [
        {
            "text": """
            Oracle Exadata is a database machine that combines hardware and software 
            to provide high-performance database solutions. When migrating Exadata 
            workloads to the cloud, it's important to consider compatibility, 
            performance, and feature parity.
            """,
            "metadata": {"source": "exadata_migration_guide", "type": "documentation"},
        },
        {
            "text": """
            Cloud migration strategies for Oracle Exadata include:
            1. Lift and shift - moving workloads with minimal changes
            2. Replatforming - adapting to cloud-native services
            3. Refactoring - redesigning for cloud architecture
            
            Each approach has different trade-offs in terms of effort, cost, and feature availability.
            """,
            "metadata": {"source": "migration_strategies", "type": "guide"},
        },
        {
            "text": """
            Oracle Cloud Infrastructure (OCI) provides Exadata Cloud Service which 
            maintains full feature compatibility with on-premises Exadata. This 
            service offers the same architecture and capabilities, making it ideal 
            for migrations requiring minimal changes.
            """,
            "metadata": {"source": "oci_exadata", "type": "cloud_service"},
        },
    ]
    
    documents = [doc["text"] for doc in sample_docs]
    metadatas = [doc["metadata"] for doc in sample_docs]
    
    ids = vector_store.add_documents(documents, metadatas)
    print(f"Added {len(ids)} sample documents to vector store")
    print(f"Document IDs: {ids}")

if __name__ == "__main__":
    add_sample_documents()

