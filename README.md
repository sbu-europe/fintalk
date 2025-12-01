# Fintalk RAG API

A Django REST API implementing a Retrieval-Augmented Generation (RAG) system for financial document querying and credit card management. Built with LlamaIndex, AWS Bedrock, PostgreSQL, and OpenSearch.

## Features

- **Semantic Document Search**: Upload and query financial documents using natural language
- **Credit Card Management**: Block credit cards via phone number lookup
- **Real-time Streaming**: Get AI responses in real-time via Server-Sent Events (SSE)
- **Dual Response Modes**: Choose between streaming or complete JSON responses
- **Containerized Deployment**: Full Docker Compose setup with persistent storage

## Architecture

```
Client → Django REST API → LlamaIndex Agent → AWS Bedrock (LLM + Embeddings)
                    ↓                ↓
              PostgreSQL      OpenSearch (Vector Store)
```

## Prerequisites

- Docker and Docker Compose
- AWS Account with Bedrock access
- AWS credentials with permissions for:
  - `bedrock:InvokeModel`
  - `bedrock:InvokeModelWithResponseStream`

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd fintalk
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add your AWS credentials:

```bash
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
AWS_SESSION_TOKEN=your-aws-session-token  # Optional, for temporary credentials
AWS_REGION=us-east-1
```

### 3. Build and Start Services

```bash
docker-compose up --build -d
```

This will start:
- Django API (port 8000)
- PostgreSQL (port 5432)
- OpenSearch (port 9200)
- OpenSearch Dashboards (port 5601)

### 4. Run Database Migrations

```bash
docker-compose exec django python manage.py migrate
```

### 5. Load Dummy Data

```bash
docker-compose exec django python manage.py populate_dummy_users
```

This creates 10 test cardholders with phone numbers like `+1234567890`, `+1234567891`, etc.

### 6. Verify Deployment

```bash
curl http://localhost:8000/api/health/
```

Expected response:
```json
{
  "status": "healthy",
  "services": {
    "postgres": "connected",
    "opensearch": "connected",
    "bedrock": "available"
  }
}
```

## API Documentation

### Base URL

```
http://localhost:8000/api
```

### Endpoints

#### 1. Document Upload

Upload documents for semantic search.

**Endpoint:** `POST /api/documents/upload/`

**Supported Formats:** PDF, TXT, DOCX

**Request:**

```bash
curl -X POST http://localhost:8000/api/documents/upload/ \
  -F "file=@/path/to/document.pdf"
```

**Response:**

```json
{
  "status": "success",
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "chunks_created": 15,
  "filename": "document.pdf",
  "message": "Document uploaded and indexed successfully"
}
```

**Process:**
1. Document is validated and loaded
2. Content is chunked (512 tokens per chunk, 128 token overlap)
3. Embeddings are generated via AWS Bedrock
4. Chunks are stored in OpenSearch vector store

#### 2. Agent Query (Streaming Mode)

Send queries to the AI agent with real-time streaming responses.

**Endpoint:** `POST /api/agent/query/`

**Request (Streaming - Default):**

```bash
curl -X POST http://localhost:8000/api/agent/query/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the key points in the financial report?",
    "phone_number": "+1234567890",
    "stream": true
  }'
```

**Response (Server-Sent Events):**

```
Content-Type: text/event-stream

data: {"type": "token", "content": "Based"}

data: {"type": "token", "content": " on"}

data: {"type": "token", "content": " the"}

data: {"type": "token", "content": " uploaded"}

data: {"type": "done"}
```

#### 3. Agent Query (Non-Streaming Mode)

Get complete responses as JSON with metadata.

**Request (Non-Streaming):**

```bash
curl -X POST http://localhost:8000/api/agent/query/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the key points in the financial report?",
    "phone_number": "+1234567890",
    "stream": false
  }'
```

**Response:**

```json
{
  "status": "success",
  "response": "Based on the uploaded documents, the key points are: 1) Revenue increased by 15%, 2) Operating expenses decreased by 8%, 3) Net profit margin improved to 22%.",
  "sources": [
    {
      "filename": "financial_report.pdf",
      "chunk_index": 2,
      "relevance_score": 0.92
    }
  ],
  "tools_used": ["search_documents"],
  "timestamp": "2024-11-26T10:30:45Z"
}
```

#### 4. Credit Card Blocking

Block a credit card by including the phone number in your query.

**Request:**

```bash
curl -X POST http://localhost:8000/api/agent/query/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Block my credit card",
    "phone_number": "+1234567890",
    "stream": false
  }'
```

**Response:**

```json
{
  "status": "success",
  "response": "Successfully blocked credit card for phone number +1234567890. Card ending in: 1234. Username: john_doe. Blocked at: 2024-11-26T10:30:45Z",
  "sources": [],
  "tools_used": ["block_credit_card"],
  "timestamp": "2024-11-26T10:30:45Z"
}
```

#### 5. OpenAI-Compatible Chat Completions (for Vapi.ai)

Send queries in OpenAI Chat Completions format for integration with Vapi.ai and other OpenAI-compatible tools. Supports both streaming and non-streaming responses.

**Endpoint:** `POST /api/chat/completions/`

**Request (Streaming - Default):**

```bash
curl -X POST http://localhost:8000/api/chat/completions/ \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {
        "role": "system",
        "content": "You are a helpful banking assistant."
      },
      {
        "role": "user",
        "content": "What loan options are available?"
      }
    ],
    "temperature": 0.7,
    "stream": true
  }'
```

**Response (Streaming):**

```
Content-Type: text/event-stream

data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","created":1677652288,"model":"amazon.nova-lite-v1:0","choices":[{"index":0,"delta":{"content":"We"},"finish_reason":null}]}

data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","created":1677652288,"model":"amazon.nova-lite-v1:0","choices":[{"index":0,"delta":{"content":" offer"},"finish_reason":null}]}

data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","created":1677652288,"model":"amazon.nova-lite-v1:0","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}

data: [DONE]
```

**Request (Non-Streaming):**

```bash
curl -X POST http://localhost:8000/api/chat/completions/ \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {
        "role": "user",
        "content": "What loan options are available?"
      }
    ],
    "stream": false
  }'
```

**Response (Non-Streaming):**

```json
{
  "id": "chatcmpl-abc123def456",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "amazon.nova-lite-v1:0",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "We offer several loan options including personal loans, home loans, and auto loans. Personal loans can be used for various purposes with flexible repayment terms. Would you like more details about any specific loan type?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 45,
    "completion_tokens": 52,
    "total_tokens": 97
  }
}
```

**Features:**
- Full OpenAI Chat Completions API compatibility
- Streaming support with Server-Sent Events (SSE)
- Conversation history via `messages` array
- Phone number extraction using `[phone: +1234567890]` format
- Token usage estimation
- Error responses in OpenAI format

**Vapi.ai Integration:**

To integrate with Vapi.ai:

1. In Vapi.ai dashboard, create a new Custom LLM provider
2. Set the URL to: `https://your-domain.com/api/chat/completions/`
3. Add authentication header if needed
4. Configure voice settings and system prompt
5. Test the integration

Example Vapi.ai configuration:
```json
{
  "name": "Fintalk Banking Assistant",
  "model": {
    "provider": "custom-llm",
    "url": "https://your-domain.com/api/chat/completions/",
    "model": "amazon.nova-lite-v1:0"
  },
  "voice": {
    "provider": "11labs",
    "voiceId": "professional-female"
  },
  "firstMessage": "Hello! I'm your Fintalk banking assistant. How can I help you today?"
}
```

#### 6. Health Check

Check system health and service connectivity.

**Endpoint:** `GET /api/health/`

**Request:**

```bash
curl http://localhost:8000/api/health/
```

**Response:**

```json
{
  "status": "healthy",
  "services": {
    "postgres": "connected",
    "opensearch": "connected",
    "bedrock": "available"
  },
  "timestamp": "2024-11-26T10:30:45Z"
}
```

## Agent Capabilities

The LlamaIndex ReActAgent can:

1. **Search Documents**: Semantic search across uploaded documents
2. **Block Credit Cards**: Deactivate cards by phone number
3. **Multi-step Reasoning**: Combine multiple tools to answer complex queries
4. **Conversational Context**: Maintain context across multiple queries

### Example Queries

**Document Search:**
```
"What are the key financial metrics in the Q3 report?"
"Summarize the risk factors mentioned in the document"
"What revenue growth is projected for 2025?"
```

**Credit Card Management:**
```
"Block the credit card for phone number +1234567890"
"I lost my card, please block it. My number is +1234567891"
```

**Hybrid Queries:**
```
"What does the policy say about lost cards? Also block my card +1234567890"
```

For detailed prompting guidelines, see [AI_PROMPTING_GUIDELINES.md](AI_PROMPTING_GUIDELINES.md).

## Environment Variables

All configuration is managed through environment variables. See `.env.example` for a complete list with descriptions.

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `AWS_ACCESS_KEY_ID` | AWS access key for Bedrock | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key for Bedrock | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `AWS_REGION` | AWS region for Bedrock | `us-east-1` |
| `OPENSEARCH_PASSWORD` | OpenSearch admin password | `Rag-test-bs23@123` |
| `SECRET_KEY` | Django secret key | Generate with `python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AWS_SESSION_TOKEN` | AWS session token (for temporary credentials) | None |
| `DEBUG` | Enable Django debug mode | `False` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `BEDROCK_LLM_MODEL` | AWS Bedrock LLM model | `amazon.nova-lite-v1:0` |
| `BEDROCK_EMBEDDING_MODEL` | AWS Bedrock embedding model | `amazon.titan-embed-text-v2:0` |

## Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Framework | Django | 5.2.8 |
| API | Django REST Framework | 3.16.1 |
| Agent | LlamaIndex | 0.14.8 |
| Database | PostgreSQL | 15 |
| Vector Store | OpenSearch | 3 |
| AI Service | AWS Bedrock | - |
| Server | Uvicorn | 0.38.0 |

## Development

### Running Tests

```bash
# Run all tests
docker-compose exec django python manage.py test

# Run with coverage
docker-compose exec django coverage run --source='.' manage.py test
docker-compose exec django coverage report

# Run specific test module
docker-compose exec django python manage.py test api.tests.test_views
```

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Django only
docker-compose logs -f django

# PostgreSQL only
docker-compose logs -f postgres

# OpenSearch only
docker-compose logs -f opensearch
```

### Accessing Services

- **Django API**: http://localhost:8000
- **OpenSearch**: http://localhost:9200
- **OpenSearch Dashboards**: http://localhost:5601
- **PostgreSQL**: localhost:5432

### Database Management

```bash
# Create migrations
docker-compose exec django python manage.py makemigrations

# Apply migrations
docker-compose exec django python manage.py migrate

# Access Django shell
docker-compose exec django python manage.py shell

# Access PostgreSQL shell
docker-compose exec postgres psql -U fintalk_user -d fintalk
```

## Troubleshooting

### OpenSearch Connection Issues

**Problem:** `ConnectionError: Connection refused`

**Solutions:**

1. Check OpenSearch is running:
```bash
docker-compose ps opensearch
```

2. Check OpenSearch logs:
```bash
docker-compose logs opensearch
```

3. Restart OpenSearch:
```bash
docker-compose restart opensearch
```

4. Wait for OpenSearch to be healthy (can take 30-60 seconds):
```bash
curl http://localhost:9200/_cluster/health
```

5. Verify OpenSearch password in `.env` matches `OPENSEARCH_INITIAL_ADMIN_PASSWORD`

### AWS Bedrock Authentication Errors

**Problem:** `UnauthorizedError: The security token included in the request is invalid`

**Solutions:**

1. Verify AWS credentials in `.env`:
```bash
docker-compose exec django python -c "import os; print(os.getenv('AWS_ACCESS_KEY_ID'))"
```

2. Check AWS credentials have Bedrock permissions:
```bash
aws bedrock list-foundation-models --region us-east-1
```

3. If using temporary credentials, ensure `AWS_SESSION_TOKEN` is set and not expired

4. Verify the AWS region supports Bedrock:
```bash
# Bedrock is available in: us-east-1, us-west-2, ap-southeast-1, etc.
```

### PostgreSQL Connection Issues

**Problem:** `OperationalError: could not connect to server`

**Solutions:**

1. Check PostgreSQL is running:
```bash
docker-compose ps postgres
```

2. Check PostgreSQL logs:
```bash
docker-compose logs postgres
```

3. Verify database credentials in `.env` match `docker-compose.yml`

4. Restart PostgreSQL:
```bash
docker-compose restart postgres
```

### Document Upload Failures

**Problem:** `400 Bad Request: Unsupported file format`

**Solutions:**

1. Verify file format is PDF, TXT, or DOCX
2. Check file is not corrupted
3. Ensure file size is reasonable (< 10MB recommended)

**Problem:** `503 Service Unavailable: Vector store unavailable`

**Solutions:**

1. Check OpenSearch is running and healthy
2. Verify OpenSearch index exists:
```bash
curl http://localhost:9200/_cat/indices
```

3. Check OpenSearch has sufficient disk space

### Agent Query Timeouts

**Problem:** Agent queries timeout or hang

**Solutions:**

1. Check AWS Bedrock service status
2. Reduce query complexity
3. Increase timeout in Django settings
4. Check network connectivity to AWS

### Memory Issues

**Problem:** `OutOfMemoryError` or containers crashing

**Solutions:**

1. Increase Docker memory allocation (Settings → Resources → Memory)
2. Reduce OpenSearch heap size in `docker-compose.yml`:
```yaml
OPENSEARCH_JAVA_OPTS=-Xms256m -Xmx256m
```

3. Limit document chunk size in settings

### Port Conflicts

**Problem:** `Error: port is already allocated`

**Solutions:**

1. Check which process is using the port:
```bash
lsof -i :8000  # or :5432, :9200
```

2. Stop the conflicting process or change port in `docker-compose.yml`

### Streaming Response Not Working

**Problem:** Streaming responses not appearing in real-time

**Solutions:**

1. Ensure `stream: true` in request body
2. Check client supports Server-Sent Events (SSE)
3. Verify no proxy/CDN is buffering responses
4. Check `X-Accel-Buffering: no` header is set

## Production Deployment

### Security Checklist

- [ ] Set `DEBUG=False` in `.env`
- [ ] Generate strong `SECRET_KEY`
- [ ] Use AWS IAM roles instead of access keys
- [ ] Enable SSL/TLS for OpenSearch (`OPENSEARCH_USE_SSL=true`)
- [ ] Configure proper CORS origins
- [ ] Enable rate limiting
- [ ] Set up log aggregation
- [ ] Configure backup strategy for PostgreSQL and OpenSearch
- [ ] Use secrets management (AWS Secrets Manager, HashiCorp Vault)
- [ ] Enable container security scanning
- [ ] Set up monitoring and alerting

### Performance Optimization

1. **Database Connection Pooling**: Already configured in Django settings
2. **OpenSearch Index Optimization**: HNSW parameters tuned for performance
3. **Caching**: Consider adding Redis for frequently accessed data
4. **CDN**: Use CDN for static files
5. **Load Balancing**: Deploy multiple Django instances behind load balancer

### Monitoring

Set up monitoring for:
- API response times
- Agent query latency
- Vector search performance
- Database query performance
- AWS Bedrock API usage and costs
- Container resource usage (CPU, memory, disk)
- Error rates and types

## Cost Considerations

### AWS Bedrock Pricing

- **Amazon Nova Lite**: ~$0.00006 per 1K input tokens, ~$0.00024 per 1K output tokens
- **Amazon Titan Embeddings**: ~$0.0001 per 1K tokens

**Estimated Monthly Costs** (1000 queries/day):
- LLM: ~$10-20/month
- Embeddings: ~$5-10/month
- Total: ~$15-30/month

### Infrastructure Costs

- **Docker Hosting**: Varies by provider (AWS ECS, DigitalOcean, etc.)
- **Storage**: PostgreSQL + OpenSearch data volumes
- **Network**: Egress costs for API responses

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `docker-compose exec django python manage.py test`
5. Submit a pull request

## License

[Your License Here]

## Support

For issues and questions:
- GitHub Issues: [repository-url]/issues
- Documentation: See [AI_PROMPTING_GUIDELINES.md](AI_PROMPTING_GUIDELINES.md)
- Project Context: See [project-context.md](project-context.md)

## Acknowledgments

- Built with [LlamaIndex](https://www.llamaindex.ai/)
- Powered by [AWS Bedrock](https://aws.amazon.com/bedrock/)
- Uses [OpenSearch](https://opensearch.org/) for vector storage
