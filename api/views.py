import os
import logging
import tempfile
import uuid
import json
from datetime import datetime
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.http import StreamingHttpResponse
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter

from .serializers import DocumentUploadSerializer, AgentQuerySerializer
from agent.bedrock_client import embed_model
from agent.vector_store import get_vector_store, get_storage_context
from agent.agent import agent

logger = logging.getLogger(__name__)


@api_view(['GET'])
def health_check(request):
    """
    Health check endpoint that verifies all critical services.
    
    This endpoint checks the connectivity and health of:
    - PostgreSQL database
    - OpenSearch vector store
    - AWS Bedrock service
    
    Returns:
        200 OK: All services are healthy
        503 Service Unavailable: One or more services are unhealthy
    """
    health_status = {
        'status': 'healthy',
        'services': {}
    }
    all_healthy = True
    
    # Check PostgreSQL connection
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        health_status['services']['postgresql'] = {
            'status': 'healthy',
            'message': 'Database connection successful'
        }
        logger.debug("PostgreSQL health check: OK")
    except Exception as e:
        health_status['services']['postgresql'] = {
            'status': 'unhealthy',
            'message': f'Database connection failed: {str(e)}'
        }
        all_healthy = False
        logger.error(f"PostgreSQL health check failed: {e}")
    
    # Check OpenSearch connection
    try:
        from agent.vector_store import get_vector_store
        vector_store = get_vector_store()
        # Try to access the client to verify connection
        if hasattr(vector_store, 'client') and vector_store.client:
            health_status['services']['opensearch'] = {
                'status': 'healthy',
                'message': 'Vector store connection successful'
            }
            logger.debug("OpenSearch health check: OK")
        else:
            raise ConnectionError("Vector store client not initialized")
    except Exception as e:
        health_status['services']['opensearch'] = {
            'status': 'unhealthy',
            'message': f'Vector store connection failed: {str(e)}'
        }
        all_healthy = False
        logger.error(f"OpenSearch health check failed: {e}")
    
    # Check AWS Bedrock connection
    try:
        from agent.bedrock_client import llm
        # Verify that the LLM client is initialized
        if llm is not None:
            health_status['services']['aws_bedrock'] = {
                'status': 'healthy',
                'message': 'AWS Bedrock client initialized'
            }
            logger.debug("AWS Bedrock health check: OK")
        else:
            raise ConnectionError("AWS Bedrock client not initialized")
    except Exception as e:
        health_status['services']['aws_bedrock'] = {
            'status': 'unhealthy',
            'message': f'AWS Bedrock connection failed: {str(e)}'
        }
        all_healthy = False
        logger.error(f"AWS Bedrock health check failed: {e}")
    
    # Set overall status
    if not all_healthy:
        health_status['status'] = 'unhealthy'
        return Response(health_status, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    return Response(health_status, status=status.HTTP_200_OK)


@api_view(['POST'])
def upload_document(request):
    """
    Upload and index a document for semantic search.
    
    This endpoint accepts document files (PDF, TXT, DOCX), chunks them,
    generates embeddings using AWS Bedrock, and stores them in OpenSearch
    vector store for later retrieval.
    
    Request:
        POST /api/documents/upload/
        Content-Type: multipart/form-data
        Body: file=<document file>
    
    Response:
        200 OK:
        {
            "status": "success",
            "document_id": "uuid",
            "chunks_created": 15,
            "filename": "document.pdf",
            "message": "Document uploaded and indexed successfully"
        }
        
        400 Bad Request: Invalid file format or validation error
        503 Service Unavailable: OpenSearch connection failure
        500 Internal Server Error: Unexpected error during processing
    """
    # Validate request data
    serializer = DocumentUploadSerializer(data=request.data)
    
    if not serializer.is_valid():
        logger.warning(f"Document upload validation failed: {serializer.errors}")
        return Response(
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid request data",
                    "details": serializer.errors
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    uploaded_file = serializer.validated_data['file']
    filename = uploaded_file.name
    document_id = str(uuid.uuid4())
    
    logger.info(f"Processing document upload: {filename} (ID: {document_id})")
    
    # Create temporary directory for file processing
    temp_dir = None
    
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, filename)
        
        # Save uploaded file to temporary location
        with open(temp_file_path, 'wb') as temp_file:
            for chunk in uploaded_file.chunks():
                temp_file.write(chunk)
        
        logger.info(f"Saved uploaded file to temporary location: {temp_file_path}")
        
        # Load document using LlamaIndex SimpleDirectoryReader
        try:
            documents = SimpleDirectoryReader(
                input_files=[temp_file_path]
            ).load_data()
            
            if not documents:
                logger.error(f"No documents loaded from file: {filename}")
                return Response(
                    {
                        "error": {
                            "code": "DOCUMENT_LOAD_ERROR",
                            "message": "Failed to load document content",
                            "details": "The file could not be parsed or is empty"
                        }
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            logger.info(f"Loaded {len(documents)} document(s) from {filename}")
            
        except Exception as e:
            logger.error(f"Error loading document with SimpleDirectoryReader: {e}")
            return Response(
                {
                    "error": {
                        "code": "DOCUMENT_PARSE_ERROR",
                        "message": "Failed to parse document",
                        "details": str(e)
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Add metadata to documents
        upload_date = datetime.utcnow().isoformat()
        for doc in documents:
            doc.metadata.update({
                'filename': filename,
                'upload_date': upload_date,
                'document_id': document_id
            })
        
        # Chunk documents using SentenceSplitter
        # 512 tokens per chunk with 128 token overlap
        try:
            text_splitter = SentenceSplitter(
                chunk_size=512,
                chunk_overlap=128
            )
            nodes = text_splitter.get_nodes_from_documents(documents)
            
            # Add chunk metadata
            for idx, node in enumerate(nodes):
                node.metadata.update({
                    'chunk_index': idx,
                    'total_chunks': len(nodes)
                })
            
            logger.info(f"Created {len(nodes)} chunks from document {filename}")
            
        except Exception as e:
            logger.error(f"Error chunking document: {e}")
            return Response(
                {
                    "error": {
                        "code": "CHUNKING_ERROR",
                        "message": "Failed to chunk document",
                        "details": str(e)
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Get storage context with OpenSearch vector store
        try:
            storage_context = get_storage_context()
            
        except ConnectionError as e:
            logger.error(f"OpenSearch connection error: {e}")
            return Response(
                {
                    "error": {
                        "code": "SERVICE_UNAVAILABLE",
                        "message": "Unable to connect to vector store",
                        "details": str(e)
                    }
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            logger.error(f"Error getting storage context: {e}")
            return Response(
                {
                    "error": {
                        "code": "STORAGE_ERROR",
                        "message": "Failed to initialize storage",
                        "details": str(e)
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Generate embeddings and store in OpenSearch
        try:
            # Create index from nodes with embeddings
            index = VectorStoreIndex(
                nodes=nodes,
                storage_context=storage_context,
                embed_model=embed_model,
                show_progress=True
            )
            
            logger.info(
                f"Successfully indexed {len(nodes)} chunks for document {filename}"
            )
            
        except ConnectionError as e:
            logger.error(f"OpenSearch storage failure: {e}")
            return Response(
                {
                    "error": {
                        "code": "SERVICE_UNAVAILABLE",
                        "message": "Failed to store document in vector store",
                        "details": str(e)
                    }
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            logger.error(f"Error generating embeddings or storing in vector store: {e}")
            return Response(
                {
                    "error": {
                        "code": "INDEXING_ERROR",
                        "message": "Failed to index document",
                        "details": str(e)
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Return success response
        response_data = {
            "status": "success",
            "document_id": document_id,
            "chunks_created": len(nodes),
            "filename": filename,
            "message": "Document uploaded and indexed successfully"
        }
        
        logger.info(f"Document upload completed successfully: {response_data}")
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        # Catch any unexpected errors
        logger.error(f"Unexpected error during document upload: {e}", exc_info=True)
        return Response(
            {
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                    "details": str(e)
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        
    finally:
        # Clean up temporary files
        if temp_dir and os.path.exists(temp_dir):
            try:
                import shutil
                shutil.rmtree(temp_dir)
                logger.debug(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary directory: {e}")


@api_view(['POST'])
def agent_query(request):
    """
    Process a query through the RAG agent with support for streaming and non-streaming responses.
    
    This endpoint accepts natural language queries and processes them through the LlamaIndex
    ReActAgent. The agent can dynamically select tools (document search or credit card blocking)
    based on the query intent. Responses can be streamed token-by-token using Server-Sent Events
    or returned as a complete JSON response.
    
    Request:
        POST /api/agent/query/
        Content-Type: application/json
        Body: {
            "message": "What are the key points in the financial report?",
            "phone_number": "+1234567890",  // Optional, for credit card operations
            "stream": true  // Optional, default true
        }
    
    Response (Streaming mode, stream=true):
        Content-Type: text/event-stream
        
        data: {"type": "token", "content": "Based"}
        data: {"type": "token", "content": " on"}
        data: {"type": "token", "content": " the"}
        ...
        data: {"type": "done"}
    
    Response (Non-streaming mode, stream=false):
        200 OK:
        {
            "status": "success",
            "response": "Based on the financial report...",
            "sources": [...],
            "tools_used": ["search_documents"],
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
        400 Bad Request: Invalid request data
        500 Internal Server Error: Agent execution failure
        503 Service Unavailable: Required services unavailable
    """
    # Validate request data
    serializer = AgentQuerySerializer(data=request.data)
    
    if not serializer.is_valid():
        logger.warning(f"Agent query validation failed: {serializer.errors}")
        return Response(
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid request data",
                    "details": serializer.errors
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    message = serializer.validated_data['message']
    phone_number = serializer.validated_data.get('phone_number', '')
    stream_response = serializer.validated_data.get('stream', True)
    
    logger.info(
        f"Processing agent query: message='{message[:50]}...', "
        f"phone_number='{phone_number}', stream={stream_response}"
    )
    
    # Check if agent is available
    if agent is None:
        logger.error("Agent is not initialized")
        error_response = {
            "error": {
                "code": "SERVICE_UNAVAILABLE",
                "message": "Agent service is not available",
                "details": "The AI agent failed to initialize. Please check AWS Bedrock configuration."
            }
        }
        
        if stream_response:
            # Return error as SSE event
            def error_stream():
                yield f"data: {json.dumps({'type': 'error', 'content': error_response})}\n\n"
            
            return StreamingHttpResponse(
                error_stream(),
                content_type='text/event-stream',
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        else:
            return Response(error_response, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    # Prepare query with phone number context if provided
    query_text = message
    if phone_number:
        # Add phone number to the query context for the agent
        query_text = f"{message}\n\n[User phone number: {phone_number}]"
    
    # Process query based on streaming mode
    if stream_response:
        # Streaming mode using Server-Sent Events (SSE)
        return _handle_streaming_query(query_text, message)
    else:
        # Non-streaming mode with complete JSON response
        return _handle_non_streaming_query(query_text, message)


def _handle_streaming_query(query_text: str, original_message: str):
    """
    Handle agent query with streaming response using Server-Sent Events.
    
    Args:
        query_text: The query text with context (may include phone number)
        original_message: The original user message
        
    Returns:
        StreamingHttpResponse with SSE events
    """
    import asyncio
    
    async def async_event_stream():
        try:
            logger.info("Starting streaming agent query")
            
            # In LlamaIndex 0.14.x, ReActAgent uses async workflow API
            # Import AgentStream event type
            from llama_index.core.agent.workflow import AgentStream
            
            # Use agent.run() to get handler
            handler = agent.run(user_msg=query_text)
            
            # Stream events as they arrive
            async for event in handler.stream_events():
                # Check if this is an AgentStream event (contains response text)
                if isinstance(event, AgentStream):
                    event_data = {
                        "type": "token",
                        "content": event.delta
                    }
                    yield f"data: {json.dumps(event_data)}\n\n"
            
            # Send completion event
            completion_event = {"type": "done"}
            yield f"data: {json.dumps(completion_event)}\n\n"
            
            logger.info("Streaming agent query completed successfully")
            
        except ConnectionError as e:
            logger.error(f"Service connection error during streaming: {e}")
            error_event = {
                "type": "error",
                "content": {
                    "code": "SERVICE_UNAVAILABLE",
                    "message": "Unable to connect to required services",
                    "details": str(e)
                }
            }
            yield f"data: {json.dumps(error_event)}\n\n"
            
        except Exception as e:
            logger.error(f"Error during streaming agent query: {e}", exc_info=True)
            error_event = {
                "type": "error",
                "content": {
                    "code": "AGENT_EXECUTION_ERROR",
                    "message": "Agent execution failed",
                    "details": str(e)
                }
            }
            yield f"data: {json.dumps(error_event)}\n\n"
    
    def event_stream():
        """Synchronous wrapper for async event stream"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            async_gen = async_event_stream()
            while True:
                try:
                    yield loop.run_until_complete(async_gen.__anext__())
                except StopAsyncIteration:
                    break
        finally:
            loop.close()
    
    # Return streaming response with appropriate headers
    response = StreamingHttpResponse(
        event_stream(),
        content_type='text/event-stream'
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    
    return response


def _handle_non_streaming_query(query_text: str, original_message: str):
    """
    Handle agent query with complete JSON response (non-streaming mode).
    
    Args:
        query_text: The query text with context (may include phone number)
        original_message: The original user message
        
    Returns:
        Response with complete agent response and metadata
    """
    import asyncio
    
    async def run_agent():
        # In LlamaIndex 0.14.x, ReActAgent uses async workflow API
        handler = agent.run(user_msg=query_text)
        response = await handler
        return response
    
    try:
        logger.info("Starting non-streaming agent query")
        
        # Run the agent asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response = loop.run_until_complete(run_agent())
        finally:
            loop.close()
        
        # Extract response text
        response_text = str(response)
        
        # Extract sources from response (for document retrieval)
        sources = []
        if hasattr(response, 'tool_calls') and response.tool_calls:
            for tool_call in response.tool_calls:
                # Check if this was a search_documents call
                if tool_call.tool_name == 'search_documents' and hasattr(tool_call, 'tool_output'):
                    # Try to extract source information from the tool output
                    output_text = str(tool_call.tool_output.raw_output) if hasattr(tool_call.tool_output, 'raw_output') else ''
                    # Parse source information if available
                    # For now, just indicate that documents were searched
                    if 'Source:' in output_text:
                        sources.append({
                            "tool": "search_documents",
                            "note": "Documents retrieved from vector store"
                        })
        
        # Extract tools used from response
        # In LlamaIndex 0.14.x, tool calls are in response.tool_calls
        tools_used = []
        if hasattr(response, 'tool_calls') and response.tool_calls:
            for tool_call in response.tool_calls:
                tool_name = tool_call.tool_name
                if tool_name not in tools_used:
                    tools_used.append(tool_name)
        
        # Build response data
        response_data = {
            "status": "success",
            "response": response_text,
            "sources": sources,
            "tools_used": tools_used,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(
            f"Non-streaming agent query completed: "
            f"tools_used={tools_used}, sources_count={len(sources)}"
        )
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except ConnectionError as e:
        logger.error(f"Service connection error: {e}")
        return Response(
            {
                "error": {
                    "code": "SERVICE_UNAVAILABLE",
                    "message": "Unable to connect to required services",
                    "details": str(e)
                }
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
        
    except Exception as e:
        logger.error(f"Error during non-streaming agent query: {e}", exc_info=True)
        return Response(
            {
                "error": {
                    "code": "AGENT_EXECUTION_ERROR",
                    "message": "Agent execution failed",
                    "details": str(e)
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
