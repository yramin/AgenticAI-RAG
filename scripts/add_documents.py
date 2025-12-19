"""Script to add documents to the vector store from files or text."""

import sys
import os
from pathlib import Path
from typing import List, Dict, Optional

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from src.retrieval.vector_store import get_vector_store


def add_text_documents(texts: List[str], metadatas: Optional[List[Dict]] = None):
    """
    Add text documents to the vector store.
    
    Args:
        texts: List of document texts
        metadatas: Optional list of metadata dictionaries
    """
    vector_store = get_vector_store()
    
    if metadatas is None:
        metadatas = [{}] * len(texts)
    
    ids = vector_store.add_documents(texts, metadatas)
    print(f"✅ Added {len(ids)} documents to vector store")
    return ids


def add_file_documents(file_paths: List[str], chunk_size: int = 1000):
    """
    Add documents from text files to the vector store.
    
    Args:
        file_paths: List of file paths to read
        chunk_size: Size of text chunks (characters) for splitting large documents
    """
    all_documents = []
    all_metadatas = []
    
    for file_path in file_paths:
        file_path = Path(file_path)
        if not file_path.exists():
            print(f"⚠️  Warning: File not found: {file_path}")
            continue
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split large documents into chunks
            if len(content) > chunk_size:
                chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
                for i, chunk in enumerate(chunks):
                    all_documents.append(chunk)
                    all_metadatas.append({
                        "source": str(file_path.name),
                        "chunk": i + 1,
                        "type": "file"
                    })
            else:
                all_documents.append(content)
                all_metadatas.append({
                    "source": str(file_path.name),
                    "type": "file"
                })
            
            print(f"✅ Loaded: {file_path.name}")
        except Exception as e:
            print(f"❌ Error reading {file_path}: {e}")
    
    if all_documents:
        ids = add_text_documents(all_documents, all_metadatas)
        return ids
    else:
        print("⚠️  No documents to add")
        return []


def add_from_directory(directory: str, extensions: List[str] = None):
    """
    Add all text files from a directory.
    
    Args:
        directory: Directory path
        extensions: List of file extensions to include (default: ['.txt', '.md', '.py'])
    """
    if extensions is None:
        extensions = ['.txt', '.md', '.py', '.json']
    
    directory = Path(directory)
    if not directory.exists():
        print(f"❌ Directory not found: {directory}")
        return []
    
    file_paths = []
    for ext in extensions:
        file_paths.extend(directory.glob(f"**/*{ext}"))
    
    if not file_paths:
        print(f"⚠️  No files found with extensions {extensions} in {directory}")
        return []
    
    print(f"📁 Found {len(file_paths)} files in {directory}")
    return add_file_documents([str(f) for f in file_paths])


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Add documents to the vector store")
    parser.add_argument("--text", nargs="+", help="Add text documents directly")
    parser.add_argument("--file", nargs="+", help="Add documents from files")
    parser.add_argument("--directory", help="Add all documents from a directory")
    parser.add_argument("--sample-docs", action="store_true", help="Add sample documents")
    
    args = parser.parse_args()
    
    if args.sample_docs:
        # Add sample documents
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
            {
                "text": """
                Oracle AI Database services on AWS provide customers with a simplified path 
                to migrate Oracle Exadata workloads. These services run on AWS infrastructure 
                and offer managed database solutions that maintain Oracle compatibility while 
                leveraging AWS cloud capabilities. The services include automated migration tools, 
                performance optimization, and seamless integration with AWS services.
                """,
                "metadata": {"source": "oracle_aws_services", "type": "cloud_service"},
            },
        ]
        
        documents = [doc["text"] for doc in sample_docs]
        metadatas = [doc["metadata"] for doc in sample_docs]
        add_text_documents(documents, metadatas)
    
    elif args.text:
        add_text_documents(args.text)
    
    elif args.file:
        add_file_documents(args.file)
    
    elif args.directory:
        add_from_directory(args.directory)
    
    else:
        print("Please specify --text, --file, --directory, or --sample-docs")
        print("\nExamples:")
        print("  python scripts/add_documents.py --sample-docs")
        print("  python scripts/add_documents.py --file doc1.txt doc2.txt")
        print("  python scripts/add_documents.py --directory data/sample_documents")
        print("  python scripts/add_documents.py --text 'Your document text here'")

