# Implementation Plan

- [x] 1. Set up project structure and Docker environment
  - Create Django project directory structure with config, api, and agent modules
  - Write Dockerfile for Django application with Python 3.11 base image
  - Write docker-compose.yml with PostgreSQL, OpenSearch, and Django services
  - Create requirements.txt with Django, DRF, LlamaIndex, boto3, and OpenSearch dependencies
  - Create .env.example file documenting all required environment variables
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 2. Implement CardHolder model and database setup
  - [x] 2.1 Create CardHolder model with username, phone_number, credit_card_number, and card_status fields
    - Write CardHolder model in api/models.py with proper field types and constraints
    - Add created_at and updated_at timestamp fields
    - _Requirements: 2.1, 2.2_
  
  - [x] 2.2 Create database migrations and dummy data fixture
    - Generate Django migrations for CardHolder model
    - Write management command to populate database with 10 dummy cardholders
    - Ensure phone numbers follow consistent format (+1234567890)
    - _Requirements: 2.3, 2.4, 2.5_

- [x] 3. Configure AWS Bedrock integration
  - [x] 3.1 Implement Bedrock client configuration
    - Write agent/bedrock_client.py using BedrockConverse and BedrockEmbedding
    - Configure BedrockConverse LLM with model, credentials, region, temperature=0.7, max_tokens=2048
    - Configure BedrockEmbedding with model_name, credentials, region, context_size=8192
    - Use environment variables for AWS credentials (access key, secret key, session token, region)
    - _Requirements: 7.1, 7.2, 7.3, 7.4_
  
  - [x] 3.2 Add error handling for AWS Bedrock operations
    - Implement retry logic with exponential backoff for Bedrock API calls
    - Add exception handling for authentication and service errors
    - _Requirements: 7.5, 9.2_

- [x] 4. Set up OpenSearch vector store
  - [x] 4.1 Implement OpenSearch connection and index initialization
    - Write agent/vector_store.py using OpensearchVectorClient and OpensearchVectorStore
    - Initialize OpensearchVectorClient with endpoint, index name, dim=1024, embedding_field, text_field
    - Configure HNSW method with engine="faiss", space_type="l2", ef_construction=256, m=48
    - Set http_auth with username and password from environment variables
    - Configure use_ssl and verify_certs settings
    - Create OpensearchVectorStore from client
    - _Requirements: 4.1, 4.2, 4.3_
  
  - [x] 4.2 Add OpenSearch error handling
    - Implement connection error handling with appropriate error messages
    - Add retry logic (2 retries with 1-second delay) for transient failures
    - _Requirements: 4.4, 9.3_

- [x] 5. Implement LlamaIndex agent tools
  - [x] 5.1 Create vector retriever tool
    - Write search_documents function in agent/tools.py as LlamaIndex FunctionTool
    - Create VectorStoreIndex from vector_store and embed_model
    - Use index.as_query_engine(similarity_top_k=5) for semantic search
    - Format results with node.text, node.metadata (filename), and node.score
    - Add comprehensive docstring explaining the tool's purpose for the agent
    - _Requirements: 5.1_
  
  - [x] 5.2 Create credit card blocking tool
    - Write block_credit_card function in agent/tools.py as LlamaIndex FunctionTool
    - Implement phone number lookup in PostgreSQL CardHolder table
    - Check if card is already blocked before updating
    - Update card_status field to 'blocked' and updated_at timestamp for matching cardholder
    - Return confirmation message with card ending digits, username, and blocked timestamp
    - Handle CardHolder.DoesNotExist exception with user-friendly message
    - Add comprehensive docstring explaining the tool's purpose for the agent
    - _Requirements: 5.2, 5.3_

- [x] 6. Configure LlamaIndex RAG agent
  - Write agent/agent.py with ReActAgent.from_tools() initialization
  - Register both vector retriever and credit card blocking tools with agent
  - Configure agent with AWS Bedrock LLM (amazon.nova-lite-v1:0) with streaming=True, temperature=0.7, max_tokens=2048
  - Set max_iterations to 10 and enable verbose mode for debugging
  - _Requirements: 5.4, 5.5, 5.6_

- [x] 7. Implement document upload endpoint
  - [x] 7.1 Create document upload API view
    - Write POST /api/documents/upload/ endpoint in api/views.py
    - Implement file validation for supported formats (PDF, TXT, DOCX)
    - Use LlamaIndex SimpleDirectoryReader to parse uploaded files
    - _Requirements: 3.1_
  
  - [x] 7.2 Implement document chunking and embedding
    - Chunk documents using LlamaIndex text splitters (512 tokens per chunk, 128 token overlap)
    - Generate embeddings for each chunk using AWS Bedrock amazon.titan-embed-text-v2:0
    - Store chunks with embeddings and metadata (filename, upload_date, chunk_index, total_chunks) in OpenSearch vector store
    - Return success response with document_id, chunks_created, filename, and success message
    - _Requirements: 3.2, 3.3, 3.4, 3.5_
  
  - [x] 7.3 Add error handling for document upload
    - Handle file validation errors with 400 responses
    - Handle OpenSearch storage failures with 503 responses
    - Implement proper error logging with structured format
    - _Requirements: 9.1, 9.5_

- [x] 8. Implement agent query endpoint with dual response modes
  - [x] 8.1 Create unified agent query endpoint with streaming support
    - Write POST /api/agent/query/ endpoint in api/views.py
    - Accept message, phone_number (optional), and stream (boolean, default true) in request body
    - Extract phone_number from request body for credit card operations
    - _Requirements: 6.1, 6.2_
  
  - [x] 8.2 Implement streaming response mode
    - Implement Server-Sent Events (SSE) for token streaming when stream=true
    - Use agent.stream_chat() to get streaming response generator
    - Stream tokens as SSE events with format: data: {"type": "token", "content": "..."}
    - Send completion event: data: {"type": "done"}
    - Set headers: Content-Type: text/event-stream, Cache-Control: no-cache, X-Accel-Buffering: no
    - _Requirements: 6.3, 6.4, 6.5_
  
  - [x] 8.3 Implement non-streaming response mode
    - Use agent.chat() for complete response when stream=false
    - Return JSON response with status, response text, sources, tools_used, and timestamp
    - Include metadata about which tools were invoked and document sources
    - _Requirements: 6.1, 6.2_
  
  - [x] 8.4 Add error handling for agent queries
    - Handle agent execution failures with 500 responses
    - Handle service unavailability with 503 responses
    - Stream error events in SSE format for streaming mode
    - Implement proper error logging with structured format
    - _Requirements: 9.2, 9.5_

- [x] 9. Create API serializers and URL routing
  - Write DRF serializers in api/serializers.py for request/response validation
  - Create DocumentUploadSerializer for file upload validation (file field)
  - Create AgentQuerySerializer for query request validation (message, phone_number optional, stream boolean default true)
  - Configure URL routing in api/urls.py for /api/documents/upload/ and /api/agent/query/
  - Configure main URL routing in config/urls.py to include api.urls
  - _Requirements: 3.1, 6.1_

- [x] 10. Configure Django settings and ASGI application
  - Configure Django settings.py with database connection to PostgreSQL using environment variables
  - Add CORS middleware configuration for allowed origins
  - Configure Django REST Framework settings with default renderer and parser classes
  - Set up logging configuration with structured JSON formatter for production
  - Configure ASGI application in config/asgi.py for uvicorn server
  - Add health check endpoint at /api/health/ to verify all services (PostgreSQL, OpenSearch, AWS Bedrock)
  - _Requirements: 1.1, 9.5_

- [x] 11. Write comprehensive tests
  - [x] 11.1 Write CardHolder model unit tests
    - Create api/tests/test_models.py with CardHolder model tests
    - Test cardholder creation with all required fields
    - Test phone number uniqueness constraint
    - Test card status transitions from active to blocked
    - Test username uniqueness constraint
    - _Requirements: 8.1_
  
  - [x] 11.2 Write agent tools unit tests
    - Create agent/tests/test_tools.py with tool function tests
    - Test search_documents with mocked OpenSearch responses (verify k=5 results)
    - Test block_credit_card success case with test database
    - Test block_credit_card with non-existent phone number
    - Test block_credit_card when card is already blocked
    - _Requirements: 8.4, 8.5_
  
  - [x] 11.3 Write document upload integration tests
    - Create api/tests/test_views.py with upload endpoint tests
    - Test successful document upload with sample PDF and TXT files
    - Test file validation errors for unsupported formats
    - Verify response includes document_id, chunks_created, and filename
    - Mock AWS Bedrock embedding calls to avoid external dependencies
    - _Requirements: 8.2_
  
  - [x] 11.4 Write agent query integration tests
    - Add agent query endpoint tests to api/tests/test_views.py
    - Test streaming response format (SSE with proper headers and event structure)
    - Test non-streaming response format (JSON with sources and tools_used)
    - Test credit card blocking via agent query
    - Test document search via agent query
    - Mock AWS Bedrock LLM responses to avoid external dependencies
    - _Requirements: 8.3, 8.6_
  
  - [x] 11.5 Write error handling tests
    - Test OpenSearch connection failures (503 response)
    - Test PostgreSQL connection failures (503 response)
    - Test AWS Bedrock API errors (500 response with retry logic)
    - Test invalid request payloads (400 response)
    - Verify proper error response formats with error code, message, and details
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [x] 12. Create deployment documentation
  - Write README.md with complete setup instructions and API documentation
  - Document all environment variables in .env.example with descriptions
  - Document Docker Compose setup steps: build, start services, run migrations, load dummy data
  - Provide example curl commands for document upload endpoint (multipart/form-data)
  - Provide example curl commands for agent query endpoint (both streaming and non-streaming modes)
  - Document health check endpoints for monitoring
  - Include troubleshooting section for common issues (OpenSearch connection, AWS credentials, etc.)
  - Reference AI_PROMPTING_GUIDELINES.md for best practices on crafting effective queries
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_
