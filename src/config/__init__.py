"""
Configurações do Sistema RAG Multimodal
=======================================

Este módulo contém todas as configurações necessárias para o sistema RAG multimodal,
incluindo configurações de modelos, diretórios e parâmetros de processamento.
"""

from .settings import RAGConfig
from .environment import EnvironmentManager

__all__ = ['RAGConfig', 'EnvironmentManager']
