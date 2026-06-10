"""
Embeddings Module

Generates and manages vector embeddings for knowledge base entries.
Supports OpenAI, Sentence Transformers, and other embedding models.
"""

from .generate_embeddings import EmbeddingGenerator, load_chunks

__all__ = ['EmbeddingGenerator', 'load_chunks']

