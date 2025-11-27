"""
OpenSearch vector store configuration for document embeddings.

This module initializes the OpenSearch vector client and store using LlamaIndex's
OpensearchVectorStore integration. The vector store is configured with HNSW
algorithm for efficient similarity search.
"""

import os
import logging
import time
from typing import Optional, Callable, Any
from llama_index.vector_stores.opensearch import (
    OpensearchVectorStore,
    OpensearchVectorClient
)
from llama_index.core import StorageContext

logger = logging.getLogger(__name__)


def retry_with_backoff(
    func: Callable,
    max_retries: int = 2,
    initial_delay: float = 1.0,
    *args,
    **kwargs
) -> Any:
    """
    Retry a function with exponential backoff for transient failures.
    
    Args:
        func: The function to retry
        max_retries: Maximum number of retry attempts (default: 2)
        initial_delay: Initial delay in seconds between retries (default: 1.0)
        *args: Positional arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function
    
    Returns:
        The result of the function call
        
    Raises:
        The last exception encountered if all retries fail
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            
            if attempt < max_retries:
                delay = initial_delay * (2 ** attempt)
                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries + 1} failed: {str(e)}. "
                    f"Retrying in {delay} seconds..."
                )
                time.sleep(delay)
            else:
                logger.error(
                    f"All {max_retries + 1} attempts failed. Last error: {str(e)}"
                )
    
    raise last_exception


def get_opensearch_client(
    endpoint: Optional[str] = None,
    index: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    use_ssl: Optional[bool] = None
) -> OpensearchVectorClient:
    """
    Initialize and return an OpenSearch vector client.
    
    Args:
        endpoint: OpenSearch endpoint URL (defaults to env var OPENSEARCH_ENDPOINT)
        index: Index name (defaults to env var OPENSEARCH_INDEX or 'fintalk_documents')
        username: OpenSearch username (defaults to env var OPENSEARCH_USER)
        password: OpenSearch password (defaults to env var OPENSEARCH_PASSWORD)
        use_ssl: Whether to use SSL (defaults to env var OPENSEARCH_USE_SSL)
    
    Returns:
        OpensearchVectorClient configured for the Fintalk system
        
    Raises:
        ValueError: If required credentials are missing
        ConnectionError: If unable to connect to OpenSearch
    """
    # Get configuration from environment variables with defaults
    endpoint = endpoint or os.getenv('OPENSEARCH_ENDPOINT', 'http://opensearch:9200')
    index = index or os.getenv('OPENSEARCH_INDEX', 'fintalk_documents')
    username = username or os.getenv('OPENSEARCH_USER', 'admin')
    password = password or os.getenv('OPENSEARCH_PASSWORD')
    
    if use_ssl is None:
        use_ssl = os.getenv('OPENSEARCH_USE_SSL', 'true').lower() == 'true'
    
    if not password:
        raise ValueError("OpenSearch password is required. Set OPENSEARCH_PASSWORD environment variable.")
    
    logger.info(f"Initializing OpenSearch client for endpoint: {endpoint}, index: {index}")
    
    def _create_client():
        """Internal function to create OpenSearch client with retry support."""
        try:
            # Initialize OpenSearch vector client with HNSW configuration
            client = OpensearchVectorClient(
                endpoint=endpoint,
                index=index,
                dim=1024,  # Dimension for amazon.titan-embed-text-v2:0
                embedding_field="embedding",
                text_field="content",
                method={
                    "name": "hnsw",
                    "engine": "faiss",  # Using FAISS engine for better performance
                    "space_type": "l2",
                    "parameters": {
                        "ef_construction": 256,
                        "m": 48
                    }
                },
                http_auth=(username, password),
                use_ssl=use_ssl,
                verify_certs=False  # Set to True in production with proper certificates
            )
            
            logger.info(f"Successfully initialized OpenSearch client for index: {index}")
            return client
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenSearch client: {str(e)}")
            raise ConnectionError(f"Unable to connect to OpenSearch at {endpoint}: {str(e)}")
    
    # Use retry logic with 2 retries and 1-second initial delay
    try:
        return retry_with_backoff(_create_client, max_retries=2, initial_delay=1.0)
    except Exception as e:
        # Re-raise with appropriate error message
        raise ConnectionError(
            f"Failed to connect to OpenSearch at {endpoint} after multiple attempts. "
            f"Please verify that OpenSearch is running and credentials are correct. Error: {str(e)}"
        )


def get_vector_store(client: Optional[OpensearchVectorClient] = None) -> OpensearchVectorStore:
    """
    Create and return an OpenSearch vector store.
    
    Args:
        client: Optional pre-configured OpensearchVectorClient. If None, creates a new client.
    
    Returns:
        OpensearchVectorStore instance ready for document storage and retrieval
        
    Raises:
        ConnectionError: If unable to create vector store
    """
    if client is None:
        client = get_opensearch_client()
    
    try:
        vector_store = OpensearchVectorStore(client)
        logger.info("Successfully created OpenSearch vector store")
        return vector_store
        
    except Exception as e:
        logger.error(f"Failed to create vector store: {str(e)}")
        raise ConnectionError(f"Unable to create OpenSearch vector store: {str(e)}")


def get_storage_context(vector_store: Optional[OpensearchVectorStore] = None) -> StorageContext:
    """
    Create and return a LlamaIndex storage context with OpenSearch vector store.
    
    Args:
        vector_store: Optional pre-configured OpensearchVectorStore. If None, creates a new store.
    
    Returns:
        StorageContext configured with OpenSearch vector store
        
    Raises:
        ConnectionError: If unable to create storage context
    """
    if vector_store is None:
        vector_store = get_vector_store()
    
    try:
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        logger.info("Successfully created storage context with OpenSearch vector store")
        return storage_context
        
    except Exception as e:
        logger.error(f"Failed to create storage context: {str(e)}")
        raise ConnectionError(f"Unable to create storage context: {str(e)}")
