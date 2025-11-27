"""
AWS Bedrock Client Configuration

This module provides configured instances of AWS Bedrock LLM and embedding models
for use throughout the Fintalk application. It uses LlamaIndex's BedrockConverse
and BedrockEmbedding classes with credentials from environment variables.

Includes retry logic with exponential backoff for handling transient failures
and comprehensive error handling for authentication and service errors.
"""

import os
import logging
import time
from typing import Optional, Callable, Any
from functools import wraps
from llama_index.llms.bedrock_converse import BedrockConverse
from llama_index.embeddings.bedrock import BedrockEmbedding

# Configure logging
logger = logging.getLogger(__name__)


class BedrockError(Exception):
    """Base exception for Bedrock-related errors"""
    pass


class BedrockAuthenticationError(BedrockError):
    """Raised when AWS authentication fails"""
    pass


class BedrockServiceError(BedrockError):
    """Raised when Bedrock service is unavailable or returns an error"""
    pass


def retry_with_exponential_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    exponential_base: float = 2.0,
    max_delay: float = 60.0
):
    """
    Decorator that implements retry logic with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds before first retry
        exponential_base: Base for exponential backoff calculation
        max_delay: Maximum delay between retries in seconds
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    # Check if this is the last attempt
                    if attempt == max_retries:
                        logger.error(
                            f"Failed after {max_retries} retries: {func.__name__}"
                        )
                        break
                    
                    # Check for authentication errors (don't retry)
                    error_msg = str(e).lower()
                    if any(auth_err in error_msg for auth_err in [
                        'credentials', 'unauthorized', 'forbidden',
                        'access denied', 'invalid token'
                    ]):
                        logger.error(f"Authentication error in {func.__name__}: {e}")
                        raise BedrockAuthenticationError(
                            f"AWS authentication failed: {e}"
                        ) from e
                    
                    # Log retry attempt
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries} failed for "
                        f"{func.__name__}: {e}. Retrying in {delay}s..."
                    )
                    
                    # Wait before retry
                    time.sleep(delay)
                    
                    # Calculate next delay with exponential backoff
                    delay = min(delay * exponential_base, max_delay)
            
            # If we get here, all retries failed
            raise BedrockServiceError(
                f"Bedrock service error after {max_retries} retries: {last_exception}"
            ) from last_exception
        
        return wrapper
    return decorator


@retry_with_exponential_backoff(max_retries=3)
def get_bedrock_llm(
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2048
) -> BedrockConverse:
    """
    Initialize and return a configured AWS Bedrock LLM instance.
    
    Uses BedrockConverse which is the recommended approach for AWS Bedrock
    integration with LlamaIndex, providing better streaming support and
    integration with the Converse API.
    
    Includes automatic retry logic with exponential backoff for transient failures.
    
    Args:
        model: Model ID to use (defaults to env var BEDROCK_LLM_MODEL)
        temperature: Sampling temperature (0.0 to 1.0)
        max_tokens: Maximum tokens in response
        
    Returns:
        Configured BedrockConverse instance
        
    Raises:
        ValueError: If required AWS credentials are missing
        BedrockAuthenticationError: If AWS authentication fails
        BedrockServiceError: If Bedrock service is unavailable after retries
    """
    try:
        # Get AWS credentials from environment
        aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        aws_session_token = os.getenv('AWS_SESSION_TOKEN')  # Optional
        aws_region = os.getenv('AWS_REGION', 'us-east-1')
        
        # Validate required credentials
        if not aws_access_key_id or not aws_secret_access_key:
            raise BedrockAuthenticationError(
                "AWS credentials not found. Please set AWS_ACCESS_KEY_ID and "
                "AWS_SECRET_ACCESS_KEY environment variables."
            )
        
        # Get model from parameter or environment
        model_id = model or os.getenv('BEDROCK_LLM_MODEL', 'amazon.nova-lite-v1:0')
        
        logger.info(f"Initializing Bedrock LLM with model: {model_id}")
        
        # Initialize BedrockConverse
        llm = BedrockConverse(
            model=model_id,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token,
            region_name=aws_region,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        logger.info("Bedrock LLM initialized successfully")
        return llm
        
    except BedrockAuthenticationError:
        # Re-raise authentication errors without retry
        raise
    except Exception as e:
        logger.error(f"Error initializing Bedrock LLM: {e}")
        raise BedrockServiceError(f"Failed to initialize Bedrock LLM: {e}") from e


@retry_with_exponential_backoff(max_retries=3)
def get_bedrock_embedding(
    model_name: Optional[str] = None,
    context_size: int = 8192
) -> BedrockEmbedding:
    """
    Initialize and return a configured AWS Bedrock embedding model instance.
    
    Includes automatic retry logic with exponential backoff for transient failures.
    
    Args:
        model_name: Embedding model ID (defaults to env var BEDROCK_EMBEDDING_MODEL)
        context_size: Maximum context size for embeddings
        
    Returns:
        Configured BedrockEmbedding instance
        
    Raises:
        ValueError: If required AWS credentials are missing
        BedrockAuthenticationError: If AWS authentication fails
        BedrockServiceError: If Bedrock service is unavailable after retries
    """
    try:
        # Get AWS credentials from environment
        aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        aws_session_token = os.getenv('AWS_SESSION_TOKEN')  # Optional
        aws_region = os.getenv('AWS_REGION', 'us-east-1')
        
        # Validate required credentials
        if not aws_access_key_id or not aws_secret_access_key:
            raise BedrockAuthenticationError(
                "AWS credentials not found. Please set AWS_ACCESS_KEY_ID and "
                "AWS_SECRET_ACCESS_KEY environment variables."
            )
        
        # Get model from parameter or environment
        embedding_model = model_name or os.getenv(
            'BEDROCK_EMBEDDING_MODEL',
            'amazon.titan-embed-text-v2:0'
        )
        
        logger.info(f"Initializing Bedrock Embedding with model: {embedding_model}")
        
        # Initialize BedrockEmbedding
        embed_model = BedrockEmbedding(
            model_name=embedding_model,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token,
            region_name=aws_region,
            context_size=context_size
        )
        
        logger.info("Bedrock Embedding initialized successfully")
        return embed_model
        
    except BedrockAuthenticationError:
        # Re-raise authentication errors without retry
        raise
    except Exception as e:
        logger.error(f"Error initializing Bedrock Embedding: {e}")
        raise BedrockServiceError(
            f"Failed to initialize Bedrock Embedding: {e}"
        ) from e


# Create singleton instances for reuse across the application
try:
    llm = get_bedrock_llm()
    embed_model = get_bedrock_embedding()
    logger.info("AWS Bedrock clients initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize AWS Bedrock clients: {e}")
    llm = None
    embed_model = None
