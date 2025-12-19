"""Vector store implementation using ChromaDB."""

import logging
import os
from typing import List, Dict, Optional, Any, Callable
from pathlib import Path
import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions
from openai import OpenAI

from src.core.config import get_settings
from src.retrieval.embeddings import get_embedding_generator

logger = logging.getLogger(__name__)


class VectorStore:
    """Vector store for document embeddings using ChromaDB."""

    def __init__(
        self,
        collection_name: Optional[str] = None,
        persist_directory: Optional[str] = None,
    ):
        """Initialize the vector store."""
        self.settings = get_settings()
        self.collection_name = collection_name or self.settings.chroma_collection_name
        self.persist_directory = persist_directory or self.settings.chroma_db_path

        # Ensure directory exists
        os.makedirs(self.persist_directory, exist_ok=True)

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )

        # Get or create collection
        # Use OpenAI embedding function (supports OpenRouter via base_url)
        embedding_kwargs = {
            "api_key": self.settings.openai_api_key,
            "model_name": self.settings.openai_embedding_model,
        }
        
        # Add base_url if configured (for OpenRouter)
        if self.settings.openai_base_url:
            embedding_kwargs["api_base"] = self.settings.openai_base_url
            
            # Add OpenRouter headers if configured
            headers = {}
            if self.settings.openrouter_http_referer:
                headers["HTTP-Referer"] = self.settings.openrouter_http_referer
            if self.settings.openrouter_title:
                headers["X-Title"] = self.settings.openrouter_title
            
            if headers:
                embedding_kwargs["default_headers"] = headers
        
        embedding_fn = embedding_functions.OpenAIEmbeddingFunction(**embedding_kwargs)

        try:
            self.collection = self.client.get_collection(
                name=self.collection_name,
                embedding_function=embedding_fn,
            )
            logger.info(f"Loaded existing collection: {self.collection_name}")
        except Exception:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=embedding_fn,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(f"Created new collection: {self.collection_name}")

    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Add documents to the vector store.

        Args:
            documents: List of document texts
            metadatas: Optional list of metadata dictionaries
            ids: Optional list of document IDs

        Returns:
            List of document IDs
        """
        if not documents:
            return []

        if ids is None:
            import uuid
            ids = [str(uuid.uuid4()) for _ in documents]

        if metadatas is None:
            metadatas = [{}] * len(documents)

        try:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
            )
            logger.info(f"Added {len(documents)} documents to vector store")
            return ids
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            raise

    def search(
        self,
        query: str,
        n_results: int = 5,
        filter: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Search for similar documents.

        Args:
            query: Query text
            n_results: Number of results to return
            filter: Optional metadata filter

        Returns:
            Dictionary with 'documents', 'metadatas', 'distances', and 'ids'
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=filter,
            )
            return {
                "documents": results["documents"][0] if results["documents"] else [],
                "metadatas": results["metadatas"][0] if results["metadatas"] else [],
                "distances": results["distances"][0] if results["distances"] else [],
                "ids": results["ids"][0] if results["ids"] else [],
            }
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            raise

    def get_by_ids(self, ids: List[str]) -> Dict[str, Any]:
        """
        Get documents by their IDs.

        Args:
            ids: List of document IDs

        Returns:
            Dictionary with 'documents', 'metadatas', and 'ids'
        """
        try:
            results = self.collection.get(ids=ids)
            return {
                "documents": results["documents"],
                "metadatas": results["metadatas"],
                "ids": results["ids"],
            }
        except Exception as e:
            logger.error(f"Error getting documents by IDs: {e}")
            raise

    def delete(self, ids: Optional[List[str]] = None, filter: Optional[Dict[str, Any]] = None) -> None:
        """
        Delete documents from the vector store.

        Args:
            ids: Optional list of document IDs to delete
            filter: Optional metadata filter for deletion
        """
        try:
            if ids:
                self.collection.delete(ids=ids)
                logger.info(f"Deleted {len(ids)} documents")
            elif filter:
                self.collection.delete(where=filter)
                logger.info("Deleted documents matching filter")
            else:
                logger.warning("No IDs or filter provided for deletion")
        except Exception as e:
            logger.error(f"Error deleting documents: {e}")
            raise

    def update(
        self,
        ids: List[str],
        documents: Optional[List[str]] = None,
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """
        Update documents in the vector store.

        Args:
            ids: List of document IDs to update
            documents: Optional new document texts
            metadatas: Optional new metadata
        """
        try:
            self.collection.update(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
            )
            logger.info(f"Updated {len(ids)} documents")
        except Exception as e:
            logger.error(f"Error updating documents: {e}")
            raise

    def count(self) -> int:
        """Get the total number of documents in the collection."""
        try:
            return self.collection.count()
        except Exception as e:
            logger.error(f"Error counting documents: {e}")
            return 0

    def reset(self) -> None:
        """Reset the collection (delete all documents)."""
        try:
            self.client.delete_collection(name=self.collection_name)
            # Recreate collection with same embedding configuration
            embedding_kwargs = {
                "api_key": self.settings.openai_api_key,
                "model_name": self.settings.openai_embedding_model,
            }
            
            # Add base_url if configured (for OpenRouter)
            if self.settings.openai_base_url:
                embedding_kwargs["api_base"] = self.settings.openai_base_url
                
                # Add OpenRouter headers if configured
                headers = {}
                if self.settings.openrouter_http_referer:
                    headers["HTTP-Referer"] = self.settings.openrouter_http_referer
                if self.settings.openrouter_title:
                    headers["X-Title"] = self.settings.openrouter_title
                
                if headers:
                    embedding_kwargs["default_headers"] = headers
            
            embedding_fn = embedding_functions.OpenAIEmbeddingFunction(**embedding_kwargs)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=embedding_fn,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info("Reset vector store collection")
        except Exception as e:
            logger.error(f"Error resetting collection: {e}")
            raise


# Global instance
_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """Get or create the global vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store

