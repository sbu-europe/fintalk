"""
Fintalk Agent Module

This module provides the LlamaIndex ReActAgent configured with tools for
document search and credit card management operations.
"""

from agent.agent import agent, get_agent
from agent.tools import vector_retriever_tool, credit_card_blocker_tool
from agent.bedrock_client import llm, embed_model
from agent.vector_store import get_vector_store, get_storage_context

__all__ = [
    'agent',
    'get_agent',
    'vector_retriever_tool',
    'credit_card_blocker_tool',
    'llm',
    'embed_model',
    'get_vector_store',
    'get_storage_context',
]
