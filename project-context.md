# Fintalk Project Context

## Executive Summary

Fintalk is a Django REST API implementing a RAG (Retrieval-Augmented Generation) system for financial document querying and credit card management. The system leverages LlamaIndex as the agent orchestration framework, AWS Bedrock for AI capabilities, PostgreSQL for structured user data, and OpenSearch for vector storage. The entire stack runs in Docker containers with persistent storage.

**Key Capabilities:**
- Semantic document search using vector embeddings
- Credit card blocking via phone number lookup
- Real-time streaming responses from AI agent
- Containerized deployment with data persistence

## Project Structure

```
fintalk/
├── manage.py
├── config/
│   ├── settings.py        # Django settings with environment configuration
│   ├── urls.py            # Main URL routing
│   ├── asgi.py            # ASGI configuration for uvicorn
│   └── wsgi.py            # WSGI configuration (optional)
├── api/
│   ├── models.py          # CardHolder model
│   ├── views.py           # API endpoints (upload, query, health)
│   ├── serializers.py     # DRF serializers for validation
│   ├── urls.py            # API routes
│   ├── management/
│   │   └── commands/
│   │       └── populate_dummy_users.py  # Dummy data generation
│   └── tests/
│       ├── test_models.py
│       ├── test_views.py
│       └── test_serializers.py
├── agent/
│   ├── agent.py           # LlamaIndex ReActAgent setup
│   ├── tools.py           # Custom agent tools (search, block card)
│   ├── vector_store.py    # OpenSearch vector store configuration
│   ├── bedrock_client.py  # AWS Bedrock LLM and embedding setup
│   └── tests/
│       ├── test_agent.py
│       └── test_tools.py
├── requirements.txt       # Python dependencies
├── Dockerfile            # Django container image
├── docker-compose.yml    # Multi-container orchestration
├── .env.example          # Environment variable template
├── README.md             # Setup and API documentation
├── AI_PROMPTING_GUIDELINES.md  # Best practices for querying the agent
└── project-context.md    # Technical documentation
```

## Architecture Overview

### System Components

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTP/SSE
       ▼
┌─────────────────────────────────────┐
│        Django REST API              │
│  ┌───────────────────────────────┐  │
│  │    LlamaIndex ReActAgent      │  │
│  │  ┌─────────────────────────┐  │  │
│  │  │   Tool 1: Vector Search │  │  │
│  │  └─────────────────────────┘  │  │
│  │  ┌─────────────────────────┐  │  │
│  │  │ Tool 2: Block Card      │  │  │
│  │  └─────────────────────────┘  │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
       │                    │
       │                    │
       ▼                    ▼
┌──────────────┐    ┌──────────────┐
│  PostgreSQL  │    │  OpenSearch  │
│ (CardHolder) │    │   (Vectors)  │
└──────────────┘    └──────────────┘
       │                    │
       └────────┬───────────┘
                ▼
         ┌──────────────┐
         │ AWS Bedrock  │
         │ LLM + Embed  │
         └──────────────┘
```

### Technology Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| Framework | Django | 5.2.8 | Web framework |
| API | Django REST Framework | 3.16.1 | REST API |
| Agent | LlamaIndex | 0.14.8 | RAG orchestration |
| Database | PostgreSQL | 15 | Cardholder data storage |
| Vector DB | OpenSearch | 3 | Document embeddings |
| AI Service | AWS Bedrock | - | LLM & embeddings |
| Server | Uvicorn | 0.38.0 | ASGI server |
| Container | Docker Compose | - | Orchestration |

## Data Models

### CardHolder Model (PostgreSQL)

```python
class CardHolder(models.Model):
    """
    Stores cardholder information including credit card data.
    Phone number is the unique identifier for credit card operations.
    """
    username = models.CharField(max_length=100, unique=True)
    phone_number = models.CharField(max_length=20, unique=True, db_index=True)
    credit_card_number = models.CharField(max_length=19)
    card_status = models.CharField(
        max_length=10,
        choices=[('active', 'Active'), ('blocked', 'Blocked')],
        default='active'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'cardholders'
        ordering = ['-created_at']
```

### Document Index (OpenSearch)

The OpenSearch index is configured using LlamaIndex's OpensearchVectorClient:

```python
from llama_index.vector_stores.opensearch import (
    OpensearchVectorStore,
    OpensearchVectorClient
)

# Initialize OpenSearch vector client
client = OpensearchVectorClient(
    endpoint=os.getenv('OPENSEARCH_ENDPOINT', 'http://opensearch:9200'),
    index=os.getenv('OPENSEARCH_INDEX', 'fintalk_documents'),
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
    http_auth=(
        os.getenv('OPENSEARCH_USER', 'admin'),
        os.getenv('OPENSEARCH_PASSWORD')
    ),
    use_ssl=os.getenv('OPENSEARCH_USE_SSL', 'true').lower() == 'true',
    verify_certs=False  # Set to True in production with proper certificates
)

# Create vector store
vector_store = OpensearchVectorStore(client)
```

**Index Structure:**
- **embedding**: 1024-dimensional knn_vector field using HNSW algorithm with FAISS engine
- **content**: Text field for document content
- **metadata**: Object field containing filename, upload_date, chunk_index, and total_chunks
- **HNSW Parameters**: ef_construction=256, m=48 for optimized search performance

## API Endpoints

### 1. Document Upload

**Endpoint:** `POST /api/documents/upload/`

**Purpose:** Upload and index documents for RAG retrieval

**Request:**
```http
POST /api/documents/upload/ HTTP/1.1
Content-Type: multipart/form-data

file: <binary file data>
```

**Response:**
```json
{
  "status": "success",
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "chunks_created": 15,
  "filename": "financial_report_2024.pdf",
  "message": "Document uploaded and indexed successfully"
}
```

**Process Flow:**
1. Validate file type (PDF, TXT, DOCX)
2. Load document with LlamaIndex SimpleDirectoryReader
3. Chunk document (512 tokens per chunk, 128 token overlap)
4. Generate embeddings via AWS Bedrock (amazon.titan-embed-text-v2:0)
5. Store chunks + vectors in OpenSearch
6. Return confirmation with document metadata

### 2. Agent Query

**Endpoint:** `POST /api/agent/query/`

**Purpose:** Send query to RAG agent with streaming or normal response

**Request:**
```json
{
  "message": "What are the key points in the Q3 financial report?",
  "phone_number": "+1234567890",
  "stream": true
}
```

**Response Format 1: Streaming (SSE) - when `stream=true` or omitted:**
```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive

data: {"type": "token", "content": "Based"}

data: {"type": "token", "content": " on"}

data: {"type": "token", "content": " the"}

data: {"type": "token", "content": " uploaded"}

data: {"type": "token", "content": " documents"}

data: {"type": "done"}
```

**Response Format 2: Normal JSON - when `stream=false`:**
```json
{
  "status": "success",
  "response": "Based on the uploaded documents, the Q3 financial report highlights three key points: 1) Revenue increased by 15% year-over-year, 2) Operating expenses decreased by 8%, and 3) Net profit margin improved to 22%.",
  "sources": [
    {
      "filename": "Q3_financial_report.pdf",
      "chunk_index": 2,
      "relevance_score": 0.92
    },
    {
      "filename": "Q3_financial_report.pdf",
      "chunk_index": 5,
      "relevance_score": 0.87
    }
  ],
  "tools_used": ["search_documents"],
  "timestamp": "2024-11-26T10:30:45Z"
}
```

**Process Flow:**
1. Parse request body and validate
2. Initialize LlamaIndex ReActAgent
3. Agent analyzes query intent using AWS Bedrock LLM
4. Agent selects appropriate tool(s):
   - Vector search for document queries
   - Credit card blocker for account management
5. Execute tool functions
6. Return response based on stream parameter:
   - If `stream=true`: Stream response tokens back to client via SSE
   - If `stream=false`: Return complete response as JSON with metadata

## LlamaIndex Agent Configuration

### Agent Architecture

The system uses a **ReActAgent** (Reasoning + Acting) that follows this pattern:
1. **Thought**: Analyze the user's request
2. **Action**: Select and execute appropriate tool
3. **Observation**: Process tool results
4. **Answer**: Generate final response

### Agent Setup

```python
from llama_index.core.agent import ReActAgent
from llama_index.llms.bedrock_converse import BedrockConverse
from llama_index.embeddings.bedrock import BedrockEmbedding

# Initialize Bedrock LLM with streaming using BedrockConverse
llm = BedrockConverse(
    model="amazon.nova-lite-v1:0",
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    aws_session_token=os.getenv('AWS_SESSION_TOKEN'),
    region_name=os.getenv('AWS_REGION', 'us-east-1'),
    temperature=0.7,
    max_tokens=2048
)

# Initialize embedding model
embed_model = BedrockEmbedding(
    model_name="amazon.titan-embed-text-v2:0",
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    aws_session_token=os.getenv('AWS_SESSION_TOKEN'),
    region_name=os.getenv('AWS_REGION', 'us-east-1'),
    context_size=8192
)

# Create agent with tools
agent = ReActAgent.from_tools(
    tools=[vector_retriever_tool, credit_card_blocker_tool],
    llm=llm,
    verbose=True,
    max_iterations=10
)
```

### Tool Definitions

#### Tool 1: Vector Retriever

```python
from llama_index.core.tools import FunctionTool
from llama_index.core import VectorStoreIndex

def search_documents(query: str) -> str:
    """
    Searches through uploaded documents using semantic similarity.
    
    This tool performs vector similarity search in OpenSearch to find
    the most relevant document chunks based on the user's query.
    
    Args:
        query (str): The search query to find relevant document chunks
        
    Returns:
        str: Relevant document excerpts with metadata (top 5 results)
    """
    # Create vector store index
    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
        embed_model=embed_model
    )
    
    # Create query engine with k=5
    query_engine = index.as_query_engine(similarity_top_k=5)
    
    # Execute query
    response = query_engine.query(query)
    
    # Format results
    formatted_results = []
    for idx, node in enumerate(response.source_nodes, 1):
        formatted_results.append(
            f"[Result {idx}]\n"
            f"Content: {node.text}\n"
            f"Source: {node.metadata.get('filename', 'Unknown')}\n"
            f"Similarity: {node.score:.3f}\n"
        )
    
    return "\n".join(formatted_results) if formatted_results else "No relevant documents found."

vector_retriever_tool = FunctionTool.from_defaults(fn=search_documents)
```

#### Tool 2: Credit Card Blocker

```python
def block_credit_card(phone_number: str) -> str:
    """
    Blocks a credit card associated with the given phone number.
    
    This tool updates the database to mark all credit cards associated
    with the phone number as blocked. It's used for account security
    when cardholders report lost or stolen cards.
    
    Args:
        phone_number (str): The phone number associated with the account
        
    Returns:
        str: Confirmation message with blocked card details
    """
    from api.models import CardHolder
    from django.utils import timezone
    
    try:
        # Find cardholder by phone number
        cardholder = CardHolder.objects.get(phone_number=phone_number)
        
        # Check if already blocked
        if cardholder.card_status == 'blocked':
            return (
                f"Credit card for phone number {phone_number} is already blocked.\n"
                f"Card ending in: {cardholder.credit_card_number[-4:]}\n"
                f"Username: {cardholder.username}"
            )
        
        # Block the card
        cardholder.card_status = 'blocked'
        cardholder.updated_at = timezone.now()
        cardholder.save()
        
        return (
            f"Successfully blocked credit card for phone number {phone_number}.\n"
            f"Card ending in: {cardholder.credit_card_number[-4:]}\n"
            f"Username: {cardholder.username}\n"
            f"Blocked at: {cardholder.updated_at.isoformat()}"
        )
        
    except CardHolder.DoesNotExist:
        return f"No cardholder found with phone number: {phone_number}"

credit_card_blocker_tool = FunctionTool.from_defaults(fn=block_credit_card)
```

## AWS Bedrock Configuration

### Models Used

| Purpose | Model ID | Specifications |
|---------|----------|----------------|
| LLM | amazon.nova-lite-v1:0 | Fast, cost-effective text generation with streaming |
| Embeddings | amazon.titan-embed-text-v2:0 | 1024-dimensional vectors, optimized for semantic search |

### Configuration

```python
import os
from llama_index.llms.bedrock_converse import BedrockConverse
from llama_index.embeddings.bedrock import BedrockEmbedding

# LLM configuration using BedrockConverse (recommended approach)
llm = BedrockConverse(
    model=os.getenv('BEDROCK_LLM_MODEL', 'amazon.nova-lite-v1:0'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    aws_session_token=os.getenv('AWS_SESSION_TOKEN'),  # Optional for temporary credentials
    region_name=os.getenv('AWS_REGION', 'us-east-1'),
    temperature=0.7,
    max_tokens=2048
)

# Embedding configuration
embed_model = BedrockEmbedding(
    model_name=os.getenv('BEDROCK_EMBEDDING_MODEL', 'amazon.titan-embed-text-v2:0'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    aws_session_token=os.getenv('AWS_SESSION_TOKEN'),  # Optional for temporary credentials
    region_name=os.getenv('AWS_REGION', 'us-east-1'),
    context_size=8192
)
```

**Note:** BedrockConverse is the recommended approach over the deprecated Bedrock class. It provides better integration with AWS Bedrock's Converse API and improved streaming support.

### Streaming Implementation

```python
from django.http import StreamingHttpResponse, JsonResponse
from django.utils import timezone
import json

def stream_agent_response(agent, query, phone_number=None):
    """Generator function for streaming agent responses"""
    try:
        # Prepare query with phone number context if provided
        full_query = query
        if phone_number:
            full_query = f"{query}\n[User phone number: {phone_number}]"
        
        # Execute agent with streaming
        streaming_response = agent.stream_chat(full_query)
        
        # Stream tokens as they arrive
        for token in streaming_response.response_gen:
            event_data = json.dumps({
                'type': 'token',
                'content': token
            })
            yield f"data: {event_data}\n\n"
        
        # Send completion event
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        
    except Exception as e:
        error_data = json.dumps({
            'type': 'error',
            'message': str(e)
        })
        yield f"data: {error_data}\n\n"

# In view
def agent_query_view(request):
    """Unified endpoint supporting both streaming and non-streaming responses"""
    data = json.loads(request.body)
    query = data.get('message')
    phone_number = data.get('phone_number')  # Optional
    stream = data.get('stream', True)  # Default to streaming
    
    if stream:
        # Streaming response via SSE
        response = StreamingHttpResponse(
            stream_agent_response(agent, query, phone_number),
            content_type='text/event-stream'
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response
    else:
        # Normal JSON response
        full_query = query
        if phone_number:
            full_query = f"{query}\n[User phone number: {phone_number}]"
        
        agent_response = agent.chat(full_query)
        
        # Extract sources from response
        sources = []
        if hasattr(agent_response, 'source_nodes'):
            sources = [
                {
                    'filename': node.metadata.get('filename', 'Unknown'),
                    'chunk_index': node.metadata.get('chunk_index', 0),
                    'relevance_score': node.score
                }
                for node in agent_response.source_nodes
            ]
        
        return JsonResponse({
            'status': 'success',
            'response': str(agent_response),
            'sources': sources,
            'tools_used': getattr(agent_response, 'tool_calls', []),
            'timestamp': timezone.now().isoformat()
        })
```

## Docker Configuration

### Container Services

```yaml
name: fintalk

services:
  postgres:
    image: postgres:15
    container_name: fintalk-postgres
    environment:
      POSTGRES_DB: fintalk
      POSTGRES_USER: fintalk_user
      POSTGRES_PASSWORD: fintalk_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - fintalk-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  opensearch:
    image: opensearchproject/opensearch:3
    container_name: fintalk-opensearch
    environment:
      - cluster.name=opensearch-cluster
      - node.name=opensearch
      - discovery.type=single-node        # important for single-node setup
      - bootstrap.memory_lock=true
      - OPENSEARCH_JAVA_OPTS=-Xms512m -Xmx512m
      - OPENSEARCH_INITIAL_ADMIN_PASSWORD=${OPENSEARCH_PASSWORD}
    env_file:
      - .env
    ulimits:
      memlock:
        soft: -1
        hard: -1
      nofile:
        soft: 65536  # maximum number of open files for the OpenSearch user, set to at least 65536 on modern systems
        hard: 65536
    volumes:
      - opensearch_data:/usr/share/opensearch/data
    ports:
      - 9200:9200
      - 9600:9600  # required for Performance Analyzer

    networks:
      - fintalk-network

  opensearch-dashboards:
    image: opensearchproject/opensearch-dashboards:3
    container_name: opensearch-dashboards
    ports:
      - 5601:5601
    environment:
      OPENSEARCH_HOSTS: '["https://opensearch:9200"]' 
    networks:
      - fintalk-network

  django:
    build: .
    container_name: fintalk-django
    command: uvicorn config.asgi:application --host 0.0.0.0 --port 8000 --reload
    ports:
      - "8000:8000"
    env_file:
      - .env
    networks:
      - fintalk-network
    volumes:
      - .:/app

volumes:
  postgres_data:
  opensearch_data:

networks:
  fintalk-network:
    driver: bridge
```

### Environment Variables

```bash
# Django Configuration
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# PostgreSQL Configuration
POSTGRES_DB=fintalk
POSTGRES_USER=fintalk_user
POSTGRES_PASSWORD=fintalk_password
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# OpenSearch Configuration
OPENSEARCH_ENDPOINT=http://opensearch:9200
OPENSEARCH_USER=admin
OPENSEARCH_PASSWORD=Rag-test-bs23@123

# AWS Bedrock Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
AWS_SESSION_TOKEN=your-aws-session-token-if-using-temporary-credentials
BEDROCK_LLM_MODEL=amazon.nova-lite-v1:0
BEDROCK_EMBEDDING_MODEL=amazon.titan-embed-text-v2:0
```

## Testing Strategy

### Test Structure

```
tests/
├── api/
│   ├── test_models.py        # CardHolder model tests
│   ├── test_serializers.py   # DRF serializer tests
│   └── test_views.py         # Endpoint integration tests
├── agent/
│   ├── test_agent.py         # Agent execution tests
│   └── test_tools.py         # Tool function tests
└── fixtures/
    ├── cardholders.json      # Dummy cardholder data
    └── sample_docs/          # Test documents
        ├── sample.pdf
        └── sample.txt
```

### Test Coverage Goals

| Component | Target Coverage | Priority Tests |
|-----------|----------------|----------------|
| Models | 95%+ | CRUD, validation, constraints |
| Views | 90%+ | Endpoints, error handling, streaming |
| Tools | 95%+ | Vector search, card blocking, edge cases |
| Agent | 80%+ | Tool selection, multi-turn, errors |

### Key Test Scenarios

#### 1. Model Tests (`api/tests/test_models.py`)

```python
from django.test import TestCase
from api.models import CardHolder

class CardHolderModelTest(TestCase):
    def test_cardholder_creation(self):
        """Test basic cardholder creation"""
        cardholder = CardHolder.objects.create(
            username='testuser',
            phone_number='+1234567890',
            credit_card_number='4111111111111111',
            card_status='active'
        )
        self.assertEqual(cardholder.card_status, 'active')
    
    def test_card_blocking(self):
        """Test credit card blocking functionality"""
        cardholder = CardHolder.objects.create(
            username='testuser',
            phone_number='+1234567890',
            credit_card_number='4111111111111111',
            card_status='active'
        )
        cardholder.card_status = 'blocked'
        cardholder.save()
        self.assertEqual(cardholder.card_status, 'blocked')
    
    def test_phone_number_uniqueness(self):
        """Test phone number unique constraint"""
        CardHolder.objects.create(
            username='user1',
            phone_number='+1234567890',
            credit_card_number='4111111111111111'
        )
        with self.assertRaises(Exception):
            CardHolder.objects.create(
                username='user2',
                phone_number='+1234567890',
                credit_card_number='5111111111111111'
            )
```

#### 2. Tool Tests (`agent/tests/test_tools.py`)

```python
from unittest.mock import Mock, patch
from django.test import TestCase
from agent.tools import block_credit_card, search_documents
from api.models import CardHolder

class ToolTests(TestCase):
    def setUp(self):
        self.cardholder = CardHolder.objects.create(
            username='testuser',
            phone_number='+1234567890',
            credit_card_number='4111111111111111',
            card_status='active'
        )
    
    def test_block_credit_card_success(self):
        """Test successful credit card blocking"""
        result = block_credit_card('+1234567890')
        self.assertIn('Successfully blocked', result)
        self.cardholder.refresh_from_db()
        self.assertEqual(self.cardholder.card_status, 'blocked')
    
    def test_block_credit_card_not_found(self):
        """Test blocking with non-existent phone number"""
        result = block_credit_card('+9999999999')
        self.assertIn('No cardholder found', result)
    
    @patch('agent.tools.vector_store')
    def test_search_documents(self, mock_vector_store):
        """Test document search functionality"""
        mock_vector_store.similarity_search.return_value = [
            {
                'content': 'Test content',
                'metadata': {'filename': 'test.pdf'},
                'score': 0.95
            }
        ]
        result = search_documents('test query')
        self.assertIn('Test content', result)
        self.assertIn('test.pdf', result)
```

#### 3. API Tests (`api/tests/test_views.py`)

```python
from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
import json

class APITests(TestCase):
    def setUp(self):
        self.client = Client()
    
    def test_document_upload(self):
        """Test document upload endpoint"""
        file_content = b"Sample document content for testing"
        uploaded_file = SimpleUploadedFile(
            "test.txt",
            file_content,
            content_type="text/plain"
        )
        
        response = self.client.post(
            '/api/documents/upload/',
            {'file': uploaded_file},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('document_id', data)
    
    def test_agent_query_streaming(self):
        """Test agent query with streaming response"""
        payload = {
            'message': 'What is in the documents?',
            'phone_number': '+1234567890',
            'stream': True
        }
        
        response = self.client.post(
            '/api/agent/query/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/event-stream')
    
    def test_agent_query_normal(self):
        """Test agent query with normal JSON response"""
        payload = {
            'message': 'What is in the documents?',
            'phone_number': '+1234567890',
            'stream': False
        }
        
        response = self.client.post(
            '/api/agent/query/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('response', data)
        self.assertIn('sources', data)
        self.assertIn('tools_used', data)
```

### Test Execution

```bash
# Run all tests
python manage.py test

# Run with coverage report
coverage run --source='.' manage.py test
coverage report -m
coverage html  # Generate HTML report

# Run specific test module
python manage.py test api.tests.test_models

# Run tests in parallel
python manage.py test --parallel

# Run with verbose output
python manage.py test --verbosity=2
```

### Dummy Data

The project includes a management command to populate the database with test data:

```bash
docker-compose exec django python manage.py populate_dummy_users
```

**Generated Data:**
- 10 cardholders with varied phone numbers
- Mix of active and blocked credit cards
- Different card types (Visa, MasterCard, Amex)
- Realistic phone number formats

## Deployment and Operations

### Initial Setup

```bash
# 1. Clone repository
git clone <repository-url>
cd fintalk

# 2. Create environment file
cp .env.example .env
# Edit .env with your AWS credentials

# 3. Build and start containers
docker-compose up --build -d

# 4. Wait for services to be healthy
docker-compose ps

# 5. Run database migrations
docker-compose exec django python manage.py migrate

# 6. Create OpenSearch index
docker-compose exec django python manage.py create_vector_index

# 7. Load dummy data
docker-compose exec django python manage.py populate_dummy_users

# 8. Verify deployment
curl http://localhost:8000/api/health/
```

### Health Checks

The system includes health check endpoints:

```bash
# Overall system health
curl http://localhost:8000/api/health/

# PostgreSQL health
curl http://localhost:8000/api/health/postgres/

# OpenSearch health
curl http://localhost:8000/api/health/opensearch/

# AWS Bedrock connectivity
curl http://localhost:8000/api/health/bedrock/
```

### Monitoring and Logging

**Application Logs:**
```bash
# Django application logs
docker-compose logs -f django

# PostgreSQL logs
docker-compose logs -f postgres

# OpenSearch logs
docker-compose logs -f opensearch

# All services
docker-compose logs -f
```

**Log Configuration:**
- Django: Structured logging to stdout (JSON format in production)
- Log levels: DEBUG (development), INFO (production)
- Request/response logging for all API calls
- Tool invocation logging for debugging

### Performance Considerations

1. **Vector Search Optimization**
   - HNSW algorithm parameters tuned for speed/accuracy balance
   - Index warming on application startup
   - Top-k limited to 5 results to reduce latency

2. **Database Connection Pooling**
   - PostgreSQL: 20 max connections
   - Connection timeout: 30 seconds
   - Idle connection timeout: 300 seconds

3. **Streaming Response**
   - Buffer size: 1024 bytes
   - Keep-alive timeout: 60 seconds
   - Chunked transfer encoding

4. **Caching Strategy** (Future Enhancement)
   - Redis for frequently accessed cardholder data
   - LlamaIndex query cache for repeated questions
   - Document chunk caching

### Security Best Practices

1. **Credential Management**
   - Never commit `.env` file
   - Use AWS IAM roles in production
   - Rotate AWS credentials regularly
   - Store credit card numbers encrypted at rest

2. **API Security**
   - CORS configuration for allowed origins
   - Rate limiting: 100 requests/minute per IP
   - Input validation on all endpoints
   - SQL injection prevention via Django ORM

3. **Container Security**
   - Run containers as non-root user
   - Minimal base images (python:3.11-slim)
   - Regular security updates
   - No unnecessary ports exposed

## Common Issues and Troubleshooting

### Issue: OpenSearch connection refused

**Solution:**
```bash
# Check OpenSearch is running
docker-compose ps opensearch

# Check OpenSearch logs
docker-compose logs opensearch

# Restart OpenSearch
docker-compose restart opensearch
```

### Issue: AWS Bedrock authentication error

**Solution:**
```bash
# Verify AWS credentials
aws sts get-caller-identity

# Check environment variables
docker-compose exec django env | grep AWS

# Test Bedrock access
aws bedrock list-foundation-models --region us-east-1
```

### Issue: Database migration errors

**Solution:**
```bash
# Reset database
docker-compose down -v
docker-compose up -d postgres
docker-compose exec django python manage.py migrate
```

### Issue: Streaming response not working

**Solution:**
- Disable any proxy buffering (nginx: `proxy_buffering off`)
- Check `X-Accel-Buffering: no` header is set
- Verify SSE client correctly handles event stream

## Future Enhancements

1. **Authentication & Authorization**
   - JWT-based authentication
   - Role-based access control (RBAC)
   - API key management

2. **Advanced Features**
   - Multi-turn conversation memory
   - Document update and deletion
   - Batch document processing
   - Custom embedding fine-tuning

3. **Scalability**
   - Horizontal scaling with load balancer
   - Redis cache layer
   - Celery for async task processing
   - Read replicas for PostgreSQL

4. **Observability**
   - Prometheus metrics export
   - Grafana dashboards
   - Distributed tracing with OpenTelemetry
   - Error tracking with Sentry

5. **User Experience**
   - WebSocket support for real-time updates
   - File preview before upload
   - Query history and favorites
   - Export conversation transcripts

## Key Takeaways

- **RAG System**: Combines document retrieval with LLM generation for accurate, context-aware responses
- **Agent Tools**: Two specialized tools (vector search + card blocking) selected dynamically by the agent
- **Flexible Response Format**: Supports both streaming (SSE) for real-time UX and normal JSON for traditional API clients
- **Containerized**: Fully dockerized with persistent storage for easy deployment
- **Production-Ready**: Comprehensive testing, error handling, and monitoring capabilities

## References

- [LlamaIndex Documentation](https://docs.llamaindex.ai/)
- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [OpenSearch Documentation](https://opensearch.org/docs/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)