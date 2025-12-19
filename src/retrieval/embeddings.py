"""Embedding generation using OpenAI."""

import logging
from typing import List, Optional
from functools import lru_cache
from openai import OpenAI
from src.core.config import get_settings

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generate embeddings using OpenAI."""

    def __init__(self, client: Optional[OpenAI] = None):
        """Initialize the embedding generator."""
        self.settings = get_settings()
        self.client = client or OpenAI(**self.settings.get_openai_client_kwargs())
        self.model = self.settings.openai_embedding_model
        self._cache: dict = {}

    def generate_embedding(self, text: str, use_cache: bool = True) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Input text to embed
            use_cache: Whether to use caching

        Returns:
            Embedding vector as a list of floats
        """
        if use_cache and text in self._cache:
            return self._cache[text]

        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text,
            )
            embedding = response.data[0].embedding
            if use_cache:
                self._cache[text] = embedding
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    def generate_embeddings_batch(
        self, texts: List[str], use_cache: bool = True
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch.

        Args:
            texts: List of input texts to embed
            use_cache: Whether to use caching

        Returns:
            List of embedding vectors
        """
        # Check cache first
        cached_embeddings = {}
        texts_to_embed = []
        indices = []

        for i, text in enumerate(texts):
            if use_cache and text in self._cache:
                cached_embeddings[i] = self._cache[text]
            else:
                texts_to_embed.append(text)
                indices.append(i)

        if not texts_to_embed:
            # All embeddings were cached
            return [cached_embeddings[i] for i in range(len(texts))]

        # Generate embeddings for uncached texts
        embeddings = []
        try:
            # OpenAI supports batch processing
            response = self.client.embeddings.create(
                model=self.model,
                input=texts_to_embed,
            )
            new_embeddings = {indices[i]: item.embedding for i, item in enumerate(response.data)}
            
            # Update cache
            if use_cache:
                for idx, text in zip(indices, texts_to_embed):
                    self._cache[text] = new_embeddings[idx]

            # Combine cached and new embeddings
            for i in range(len(texts)):
                if i in cached_embeddings:
                    embeddings.append(cached_embeddings[i])
                else:
                    embeddings.append(new_embeddings[i])

            return embeddings
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise

    def clear_cache(self) -> None:
        """Clear the embedding cache."""
        self._cache.clear()

    def get_cache_size(self) -> int:
        """Get the number of cached embeddings."""
        return len(self._cache)


# Global instance
_embedding_generator: Optional[EmbeddingGenerator] = None


def get_embedding_generator() -> EmbeddingGenerator:
    """Get or create the global embedding generator instance."""
    global _embedding_generator
    if _embedding_generator is None:
        _embedding_generator = EmbeddingGenerator()
    return _embedding_generator

