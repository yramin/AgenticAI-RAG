"""Long-term memory using vector store for persistent context."""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid
from src.core.config import get_settings
from src.retrieval.vector_store import get_vector_store

logger = logging.getLogger(__name__)


class LongTermMemory:
    """Manages long-term memory using vector store for semantic search."""

    def __init__(self, collection_name: Optional[str] = None):
        """Initialize long-term memory."""
        self.settings = get_settings()
        self.enabled = self.settings.long_term_memory_enabled

        if not self.enabled:
            logger.info("Long-term memory is disabled")
            return

        # Use a separate collection for long-term memory
        memory_collection = collection_name or f"{self.settings.chroma_collection_name}_memory"
        self.vector_store = get_vector_store()
        # Note: We'll use the same vector store but with different collection
        # For simplicity, we'll use metadata to distinguish memory entries
        self.memory_collection_name = memory_collection

    def store_conversation(
        self,
        session_id: str,
        messages: List[Dict[str, Any]],
        summary: Optional[str] = None,
    ) -> str:
        """
        Store a conversation in long-term memory.

        Args:
            session_id: Session identifier
            messages: List of messages
            summary: Optional conversation summary

        Returns:
            Memory entry ID
        """
        if not self.enabled:
            return ""

        try:
            # Create a text representation of the conversation
            conversation_text = self._format_conversation(messages, summary)

            # Generate a unique ID
            memory_id = str(uuid.uuid4())

            # Store in vector store with metadata
            metadata = {
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "message_count": len(messages),
                "type": "conversation",
            }
            if summary:
                metadata["summary"] = summary

            self.vector_store.add_documents(
                documents=[conversation_text],
                metadatas=[metadata],
                ids=[memory_id],
            )

            logger.info(f"Stored conversation in long-term memory: {memory_id}")
            return memory_id
        except Exception as e:
            logger.error(f"Error storing conversation: {e}")
            return ""

    def search_memories(
        self,
        query: str,
        session_id: Optional[str] = None,
        n_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant memories.

        Args:
            query: Search query
            session_id: Optional session ID to filter by
            n_results: Number of results to return

        Returns:
            List of memory entries
        """
        if not self.enabled:
            return []

        try:
            # Build filter if session_id is provided
            filter_dict = None
            if session_id:
                filter_dict = {"session_id": session_id}

            # Search vector store
            results = self.vector_store.search(
                query=query,
                n_results=n_results,
                filter=filter_dict,
            )

            # Format results
            memories = []
            for i, doc_id in enumerate(results["ids"]):
                memories.append({
                    "id": doc_id,
                    "content": results["documents"][i],
                    "metadata": results["metadatas"][i],
                    "distance": results["distances"][i],
                })

            return memories
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            return []

    def get_session_memories(
        self,
        session_id: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get all memories for a specific session.

        Args:
            session_id: Session identifier
            limit: Maximum number of memories to return

        Returns:
            List of memory entries
        """
        if not self.enabled:
            return []

        try:
            # Search with session filter
            results = self.vector_store.search(
                query="",  # Empty query to get all
                n_results=limit,
                filter={"session_id": session_id},
            )

            memories = []
            for i, doc_id in enumerate(results["ids"]):
                memories.append({
                    "id": doc_id,
                    "content": results["documents"][i],
                    "metadata": results["metadatas"][i],
                })

            # Sort by timestamp
            memories.sort(
                key=lambda x: x["metadata"].get("timestamp", ""),
                reverse=True,
            )

            return memories
        except Exception as e:
            logger.error(f"Error getting session memories: {e}")
            return []

    def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a specific memory entry.

        Args:
            memory_id: Memory entry ID

        Returns:
            True if successful
        """
        if not self.enabled:
            return False

        try:
            self.vector_store.delete(ids=[memory_id])
            logger.info(f"Deleted memory: {memory_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting memory: {e}")
            return False

    def delete_session_memories(self, session_id: str) -> int:
        """
        Delete all memories for a session.

        Args:
            session_id: Session identifier

        Returns:
            Number of memories deleted
        """
        if not self.enabled:
            return 0

        try:
            memories = self.get_session_memories(session_id, limit=1000)
            if not memories:
                return 0

            memory_ids = [m["id"] for m in memories]
            self.vector_store.delete(ids=memory_ids)
            logger.info(f"Deleted {len(memory_ids)} memories for session: {session_id}")
            return len(memory_ids)
        except Exception as e:
            logger.error(f"Error deleting session memories: {e}")
            return 0

    def _format_conversation(
        self,
        messages: List[Dict[str, Any]],
        summary: Optional[str] = None,
    ) -> str:
        """Format conversation for storage."""
        parts = []
        if summary:
            parts.append(f"Summary: {summary}\n")
        parts.append("Conversation:")
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            parts.append(f"{role}: {content}")
        return "\n".join(parts)

    def store_fact(
        self,
        fact: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Store a fact or piece of information.

        Args:
            fact: Fact to store
            session_id: Optional session ID
            metadata: Optional additional metadata

        Returns:
            Memory entry ID
        """
        if not self.enabled:
            return ""

        try:
            memory_id = str(uuid.uuid4())
            fact_metadata = {
                "timestamp": datetime.now().isoformat(),
                "type": "fact",
            }
            if session_id:
                fact_metadata["session_id"] = session_id
            if metadata:
                fact_metadata.update(metadata)

            self.vector_store.add_documents(
                documents=[fact],
                metadatas=[fact_metadata],
                ids=[memory_id],
            )

            logger.info(f"Stored fact in long-term memory: {memory_id}")
            return memory_id
        except Exception as e:
            logger.error(f"Error storing fact: {e}")
            return ""

