"""
LlamaIndex agent tools for document search and credit card management.

This module implements two specialized tools for the RAG agent:
1. Vector Retriever Tool: Searches documents using semantic similarity
2. Credit Card Blocking Tool: Blocks credit cards by phone number lookup
"""

import os
import logging
import django
from typing import Optional

# Configure Django settings before importing models
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from llama_index.core.tools import FunctionTool
from llama_index.core import VectorStoreIndex
from api.models import CardHolder
from django.utils import timezone
from agent.vector_store import get_vector_store
from agent.bedrock_client import embed_model

logger = logging.getLogger(__name__)


def search_documents(query: str) -> str:
    """
    Searches through uploaded documents using semantic similarity.
    
    This tool performs vector similarity search in OpenSearch to find
    the most relevant document chunks based on the user's query. It uses
    AWS Bedrock embeddings to convert the query into a vector and then
    finds the top 5 most similar document chunks.
    
    Use this tool when the user asks questions about uploaded documents,
    financial reports, or any content that has been indexed in the system.
    
    Args:
        query (str): The search query to find relevant document chunks
        
    Returns:
        str: Relevant document excerpts with metadata (top 5 results) or
             a message indicating no relevant documents were found
    """
    try:
        logger.info(f"Searching documents with query: {query}")
        
        # Get vector store
        vector_store = get_vector_store()
        
        # Import LLM for query engine
        from agent.bedrock_client import llm
        
        # Create vector store index with Bedrock embedding model
        index = VectorStoreIndex.from_vector_store(
            vector_store=vector_store,
            embed_model=embed_model
        )
        
        # Create query engine with k=5 for top 5 results
        # Explicitly pass llm to avoid OpenAI default
        query_engine = index.as_query_engine(
            similarity_top_k=5,
            llm=llm
        )
        
        # Execute query
        response = query_engine.query(query)
        
        # Format results
        formatted_results = []
        if hasattr(response, 'source_nodes') and response.source_nodes:
            for idx, node in enumerate(response.source_nodes, 1):
                formatted_results.append(
                    f"[Result {idx}]\n"
                    f"Content: {node.text}\n"
                    f"Source: {node.metadata.get('filename', 'Unknown')}\n"
                    f"Similarity: {node.score:.3f}\n"
                )
            
            result_text = "\n".join(formatted_results)
            logger.info(f"Found {len(response.source_nodes)} relevant documents")
            return result_text
        else:
            logger.info("No relevant documents found")
            return "No relevant documents found for your query."
            
    except Exception as e:
        logger.error(f"Error searching documents: {str(e)}")
        return f"Error searching documents: {str(e)}"


def block_credit_card(phone_number: str) -> str:
    """
    Blocks a credit card associated with the given phone number.
    
    This tool updates the database to mark all credit cards associated
    with the phone number as blocked. It's used for account security
    when cardholders report lost or stolen cards, or when suspicious
    activity is detected.
    
    Use this tool when the user requests to block their credit card,
    reports a lost or stolen card, or asks to deactivate their card.
    
    Args:
        phone_number (str): The phone number associated with the account
                           (e.g., "+1234567890")
        
    Returns:
        str: Confirmation message with blocked card details including
             the last 4 digits of the card, username, and timestamp
    """
    try:
        logger.info(f"Attempting to block credit card for phone: {phone_number}")
        if not phone_number.startswith('+'):
            phone_number = '+' + phone_number 
        # Find cardholder by phone number
        cardholder = CardHolder.objects.get(phone_number=phone_number)
        
        # Check if already blocked
        if cardholder.card_status == 'blocked':
            logger.info(f"Card for {phone_number} is already blocked")
            return (
                f"Credit card for phone number {phone_number} is already blocked.\n"
                f"Card ending in: {cardholder.credit_card_number[-4:]}\n"
                f"Username: {cardholder.username}"
            )
        
        # Block the card
        cardholder.card_status = 'blocked'
        cardholder.updated_at = timezone.now()
        cardholder.save()
        
        logger.info(f"Successfully blocked card for {phone_number}")
        return (
            f"Successfully blocked credit card for phone number {phone_number}.\n"
            f"Card ending in: {cardholder.credit_card_number[-4:]}\n"
            f"Username: {cardholder.username}\n"
            f"Blocked at: {cardholder.updated_at.isoformat()}"
        )
        
    except CardHolder.DoesNotExist:
        logger.warning(f"No cardholder found with phone number: {phone_number}")
        return f"No cardholder found with phone number: {phone_number}"
    except Exception as e:
        logger.error(f"Error blocking credit card: {str(e)}")
        return f"Error blocking credit card: {str(e)}"


def enable_credit_card(phone_number: str) -> str:
    """
    Enables a previously blocked credit card associated with the given phone number.
    
    This tool updates the database to mark all credit cards associated
    with the phone number as active. It's used when cardholders want to
    reactivate their blocked cards after recovering a lost card or
    resolving security concerns.
    
    Use this tool when the user requests to enable/unblock/reactivate
    their credit card, or asks to restore card functionality.
    
    Args:
        phone_number (str): The phone number associated with the account
                           (e.g., "+1234567890")
        
    Returns:
        str: Confirmation message with enabled card details including
             the last 4 digits of the card, username, and timestamp
    """
    try:
        logger.info(f"Attempting to enable credit card for phone: {phone_number}")
        if not phone_number.startswith('+'):
            phone_number = '+' + phone_number 
        # Find cardholder by phone number
        cardholder = CardHolder.objects.get(phone_number=phone_number)
        
        # Check if already active
        if cardholder.card_status == 'active':
            logger.info(f"Card for {phone_number} is already active")
            return (
                f"Credit card for phone number {phone_number} is already active.\n"
                f"Card ending in: {cardholder.credit_card_number[-4:]}\n"
                f"Username: {cardholder.username}"
            )
        
        # Enable the card
        cardholder.card_status = 'active'
        cardholder.updated_at = timezone.now()
        cardholder.save()
        
        logger.info(f"Successfully enabled card for {phone_number}")
        return (
            f"Successfully enabled credit card for phone number {phone_number}.\n"
            f"Card ending in: {cardholder.credit_card_number[-4:]}\n"
            f"Username: {cardholder.username}\n"
            f"Enabled at: {cardholder.updated_at.isoformat()}"
        )
        
    except CardHolder.DoesNotExist:
        logger.warning(f"No cardholder found with phone number: {phone_number}")
        return f"No cardholder found with phone number: {phone_number}"
    except Exception as e:
        logger.error(f"Error enabling credit card: {str(e)}")
        return f"Error enabling credit card: {str(e)}"


# Create LlamaIndex FunctionTool instances
vector_retriever_tool = FunctionTool.from_defaults(
    fn=search_documents,
    name="search_documents",
    description=(
        "Searches through uploaded documents using semantic similarity. "
        "Use this tool when the user asks questions about uploaded documents, "
        "financial reports, or any content that has been indexed in the system."
    )
)

credit_card_blocker_tool = FunctionTool.from_defaults(
    fn=block_credit_card,
    name="block_credit_card",
    description=(
        "Blocks a credit card associated with the given phone number. "
        "Use this tool when the user requests to block their credit card, "
        "reports a lost or stolen card, or asks to deactivate their card."
    )
)

credit_card_enabler_tool = FunctionTool.from_defaults(
    fn=enable_credit_card,
    name="enable_credit_card",
    description=(
        "Enables a previously blocked credit card associated with the given phone number. "
        "Use this tool when the user requests to enable, unblock, or reactivate their "
        "credit card, or asks to restore card functionality."
    )
)

logger.info("Agent tools initialized successfully")
