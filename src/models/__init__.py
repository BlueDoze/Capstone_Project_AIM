"""
Módulo de Modelos
=================

Este módulo contém todos os gerenciadores de modelos para o sistema RAG multimodal,
incluindo modelos Gemini e de embedding.
"""

from .gemini_models import GeminiModelManager
from .embedding_models import EmbeddingModelManager

__all__ = ['GeminiModelManager', 'EmbeddingModelManager']
