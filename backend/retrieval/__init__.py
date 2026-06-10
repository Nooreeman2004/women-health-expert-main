"""
Retrieval Module

Production-ready vector search and context retrieval for RAG pipeline.
Uses Cohere Rerank API for fast, high-quality reranking.
"""

from .production_retriever import ProductionRetriever, RetrievalResult

__all__ = ['ProductionRetriever', 'RetrievalResult']



