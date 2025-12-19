"""Short-term memory for conversation context."""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
import tiktoken
from src.core.config import get_settings

logger = logging.getLogger(__name__)


class Message:
    """Represents a single message in the conversation."""

    def __init__(
        self,
        role: str,
        content: str,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a message."""
        self.role = role  # 'user', 'assistant', 'system'
        self.content = content
        self.timestamp = timestamp or datetime.now()
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create message from dictionary."""
        timestamp = datetime.fromisoformat(data["timestamp"]) if isinstance(data.get("timestamp"), str) else data.get("timestamp")
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=timestamp,
            metadata=data.get("metadata", {}),
        )


class ShortTermMemory:
    """Manages short-term conversation memory with token-aware windowing."""

    def __init__(
        self,
        max_messages: Optional[int] = None,
        max_tokens: Optional[int] = None,
        model: str = "gpt-4",
    ):
        """Initialize short-term memory."""
        self.settings = get_settings()
        self.max_messages = max_messages or self.settings.short_term_memory_size
        self.max_tokens = max_tokens or self.settings.max_context_tokens
        self.model = model

        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fallback to cl100k_base encoding
            self.encoding = tiktoken.get_encoding("cl100k_base")

        self.messages: List[Message] = []

    def add_message(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a message to memory.

        Args:
            role: Message role ('user', 'assistant', 'system')
            content: Message content
            metadata: Optional metadata
        """
        message = Message(role=role, content=content, metadata=metadata)
        self.messages.append(message)
        self._trim_if_needed()

    def get_messages(
        self,
        include_metadata: bool = False,
        format_for_llm: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get messages in memory.

        Args:
            include_metadata: Whether to include metadata
            format_for_llm: Format as OpenAI chat format

        Returns:
            List of messages
        """
        if format_for_llm:
            return [
                {"role": msg.role, "content": msg.content}
                for msg in self.messages
            ]
        else:
            return [msg.to_dict() if include_metadata else {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
            } for msg in self.messages]

    def get_context(self, max_tokens: Optional[int] = None) -> str:
        """
        Get conversation context as a formatted string.

        Args:
            max_tokens: Maximum tokens to include

        Returns:
            Formatted context string
        """
        max_tokens = max_tokens or self.max_tokens
        context_messages = self._get_messages_within_token_limit(max_tokens)
        return "\n".join([
            f"{msg.role}: {msg.content}"
            for msg in context_messages
        ])

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.encoding.encode(text))

    def get_total_tokens(self) -> int:
        """Get total tokens in current messages."""
        return sum(self.count_tokens(msg.content) for msg in self.messages)

    def _get_messages_within_token_limit(
        self, max_tokens: int
    ) -> List[Message]:
        """Get messages that fit within token limit."""
        total_tokens = 0
        selected_messages = []

        # Start from most recent messages
        for msg in reversed(self.messages):
            msg_tokens = self.count_tokens(msg.content)
            if total_tokens + msg_tokens <= max_tokens:
                selected_messages.insert(0, msg)
                total_tokens += msg_tokens
            else:
                break

        return selected_messages

    def _trim_if_needed(self) -> None:
        """Trim messages if they exceed limits."""
        # Trim by message count
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]

        # Trim by token count
        total_tokens = self.get_total_tokens()
        if total_tokens > self.max_tokens:
            self.messages = self._get_messages_within_token_limit(self.max_tokens)

    def clear(self) -> None:
        """Clear all messages."""
        self.messages = []

    def summarize(self) -> str:
        """
        Create a summary of the conversation.

        Returns:
            Summary string
        """
        if not self.messages:
            return "No conversation history."

        summary_parts = [
            f"Conversation with {len(self.messages)} messages:",
        ]
        for msg in self.messages[-5:]:  # Last 5 messages
            summary_parts.append(f"- {msg.role}: {msg.content[:100]}...")

        return "\n".join(summary_parts)

    def to_dict(self) -> Dict[str, Any]:
        """Convert memory to dictionary."""
        return {
            "messages": [msg.to_dict() for msg in self.messages],
            "max_messages": self.max_messages,
            "max_tokens": self.max_tokens,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ShortTermMemory":
        """Create memory from dictionary."""
        memory = cls(
            max_messages=data.get("max_messages"),
            max_tokens=data.get("max_tokens"),
        )
        memory.messages = [
            Message.from_dict(msg_data)
            for msg_data in data.get("messages", [])
        ]
        return memory

