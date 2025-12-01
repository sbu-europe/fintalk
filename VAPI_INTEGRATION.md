# Vapi.ai Integration Guide

This guide explains how to integrate the Fintalk RAG API with Vapi.ai using the OpenAI-compatible endpoint.

## Overview

The `/api/chat/completions/` endpoint provides a fully OpenAI Chat Completions API compatible interface with streaming support, allowing seamless integration with Vapi.ai's custom LLM feature.

## Quick Start

### 1. Test the Endpoint Locally

First, ensure your API is running:

```bash
docker-compose up -d
```

Test the OpenAI endpoint (non-streaming):

```bash
curl -X POST http://localhost:8000/api/chat/completions/ \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {
        "role": "system",
        "content": "You are a professional banking assistant."
      },
      {
        "role": "user",
        "content": "What loan options are available?"
      }
    ],
    "temperature": 0.7,
    "stream": false
  }'
```

Test with streaming:

```bash
curl -X POST http://localhost:8000/api/chat/completions/ \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "What loan options are available?"
      }
    ],
    "stream": true
  }'
```

Expected response format:

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
        "content": "We offer several loan options..."
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

### 2. Deploy to Production

Deploy your API to a publicly accessible server (AWS, DigitalOcean, Heroku, etc.) with HTTPS enabled.

Example production URL: `https://api.yourdomain.com/api/chat/completions/`

### 3. Configure Vapi.ai

#### Step 1: Create Custom LLM Provider

1. Log in to your Vapi.ai dashboard
2. Navigate to **Settings** → **Custom LLM**
3. Click **Add Custom LLM Provider**

#### Step 2: Configure Endpoint

Fill in the following details:

- **Name**: Fintalk Banking Assistant
- **Provider Type**: Custom LLM
- **Endpoint URL**: `https://api.yourdomain.com/api/chat/completions/`
- **HTTP Method**: POST
- **Headers**:
  ```
  Content-Type: application/json
  Authorization: Bearer YOUR_API_KEY (if authentication is enabled)
  ```

#### Step 3: Test Connection

Use Vapi.ai's test interface to send a sample query:

```json
{
  "model": "gpt-3.5-turbo",
  "messages": [
    {
      "role": "user",
      "content": "Hello, can you help me?"
    }
  ]
}
```

Verify you receive a proper response.

#### Step 4: Create Voice Assistant

1. Go to **Assistants** → **Create New Assistant**
2. Configure the assistant:

```json
{
  "name": "Fintalk Banking Assistant",
  "model": {
    "provider": "custom-llm",
    "url": "https://api.yourdomain.com/api/chat/completions/",
    "model": "amazon.nova-lite-v1:0"
  },
  "voice": {
    "provider": "11labs",
    "voiceId": "professional-female"
  },
  "firstMessage": "Hello! I'm your Fintalk banking assistant. How can I help you today?",
  "systemPrompt": "You are a professional banking call center agent for FinTalk, assisting customers with loan inquiries and credit card services. Speak naturally and professionally.",
  "endCallMessage": "Thank you for calling FinTalk. Have a great day!",
  "recordingEnabled": true
}
```

3. Save and test the assistant

## Features

### Conversation History

The endpoint supports multi-turn conversations through the `messages` array:

```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are a banking assistant."
    },
    {
      "role": "user",
      "content": "What loan options do you have?"
    },
    {
      "role": "assistant",
      "content": "We offer personal loans, home loans, and auto loans."
    },
    {
      "role": "user",
      "content": "Tell me more about personal loans"
    }
  ]
}
```

### Phone Number Context

To enable credit card operations, include the phone number in the user message:

```json
{
  "role": "user",
  "content": "I need to block my credit card [phone: +1234567890]"
}
```

The endpoint will extract the phone number and pass it to the agent for credit card operations.

### Document Search

The agent automatically searches uploaded documents when relevant:

```json
{
  "role": "user",
  "content": "What are the key points in the financial report?"
}
```

The agent will retrieve relevant document chunks and provide an answer based on the content.

## Request Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `model` | string | No | `amazon.nova-lite-v1:0` | Model identifier (informational only) |
| `messages` | array | Yes | - | Array of message objects with `role` and `content` |
| `temperature` | float | No | 0.7 | Sampling temperature (0.0 to 2.0) |
| `max_tokens` | integer | No | 2048 | Maximum tokens in response (1 to 4096) |
| `stream` | boolean | No | true | Enable streaming with Server-Sent Events |

## Response Format

### Success Response

```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "amazon.nova-lite-v1:0",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Response text here..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 45,
    "completion_tokens": 120,
    "total_tokens": 165
  }
}
```

### Error Response

```json
{
  "error": {
    "message": "Invalid request: missing required field 'messages'",
    "type": "invalid_request_error",
    "param": "messages",
    "code": "missing_required_parameter"
  }
}
```

## Error Types

| Error Type | HTTP Status | Description |
|------------|-------------|-------------|
| `invalid_request_error` | 400 | Invalid request parameters |
| `authentication_error` | 401 | Authentication failed |
| `server_error` | 500 | Internal server error |
| `service_unavailable_error` | 503 | Service temporarily unavailable |

## Testing Examples

### Basic Query

```bash
curl -X POST https://api.yourdomain.com/api/agent/query/openai/ \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "What loan options are available?"}
    ]
  }'
```

### Query with System Prompt

```bash
curl -X POST https://api.yourdomain.com/api/agent/query/openai/ \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "system", "content": "You are a helpful banking assistant."},
      {"role": "user", "content": "What are your interest rates?"}
    ],
    "temperature": 0.5
  }'
```

### Credit Card Blocking

```bash
curl -X POST https://api.yourdomain.com/api/agent/query/openai/ \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Block my credit card [phone: +1234567890]"}
    ]
  }'
```

### Multi-turn Conversation

```bash
curl -X POST https://api.yourdomain.com/api/agent/query/openai/ \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "What loan options do you have?"},
      {"role": "assistant", "content": "We offer personal loans, home loans, and auto loans."},
      {"role": "user", "content": "What are the rates for personal loans?"}
    ]
  }'
```

## Vapi.ai Voice Flow Example

Here's how a typical voice conversation flows:

1. **User calls** → Vapi.ai answers with `firstMessage`
2. **User speaks**: "What loan options are available?"
3. **Vapi.ai** converts speech to text
4. **Vapi.ai** sends request to your OpenAI endpoint:
   ```json
   {
     "messages": [
       {"role": "system", "content": "You are a banking assistant."},
       {"role": "user", "content": "What loan options are available?"}
     ]
   }
   ```
5. **Your API** processes with RAG agent
6. **Your API** returns OpenAI-formatted response
7. **Vapi.ai** converts response to speech
8. **User hears** the response

## Best Practices

### 1. System Prompts

Use clear system prompts to guide the agent's behavior:

```json
{
  "role": "system",
  "content": "You are a professional banking call center agent. Be concise, friendly, and helpful. Always verify customer identity before performing sensitive operations."
}
```

### 2. Phone Number Handling

For credit card operations, ensure phone numbers are included:

```json
{
  "role": "user",
  "content": "I lost my card, please block it [phone: +1234567890]"
}
```

### 3. Error Handling

Handle errors gracefully in your Vapi.ai configuration:

- Set up fallback responses for service unavailability
- Configure retry logic for transient errors
- Log all errors for debugging

### 4. Rate Limiting

Implement rate limiting to prevent abuse:

- Set reasonable limits per user/IP
- Return 429 status code when limits are exceeded
- Include retry-after headers

### 5. Monitoring

Monitor key metrics:

- Response times
- Error rates
- Token usage
- Agent tool usage (document search vs credit card operations)

## Troubleshooting

### Issue: "Connection refused" error

**Solution**: Ensure your API is publicly accessible and HTTPS is enabled.

```bash
# Test connectivity
curl -I https://api.yourdomain.com/api/agent/query/openai/
```

### Issue: "Invalid request" error

**Solution**: Verify the request format matches OpenAI's specification.

```bash
# Check request structure
curl -X POST https://api.yourdomain.com/api/agent/query/openai/ \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "test"}]}' \
  -v
```

### Issue: Slow responses

**Solution**: 
- Check AWS Bedrock latency
- Optimize document chunking
- Consider caching frequent queries
- Monitor OpenSearch performance

### Issue: Agent not finding documents

**Solution**:
- Verify documents are uploaded: `POST /api/documents/upload/`
- Check OpenSearch index exists
- Test document search directly: `POST /api/agent/query/`

## Security Considerations

### 1. Authentication

Add API key authentication:

```python
# In Django settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
}
```

### 2. HTTPS

Always use HTTPS in production:

```nginx
server {
    listen 443 ssl;
    server_name api.yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8000;
    }
}
```

### 3. Rate Limiting

Implement rate limiting:

```python
# Install django-ratelimit
# pip install django-ratelimit

from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='100/h')
@api_view(['POST'])
def openai_agent_query(request):
    # ... existing code
```

### 4. Input Validation

The endpoint already validates:
- Message structure
- Role values (system, user, assistant)
- Temperature range (0.0 to 2.0)
- Max tokens range (1 to 4096)

### 5. PII Protection

- Phone numbers are extracted but not logged in plain text
- Credit card numbers are never returned in responses
- Conversation history is not persisted

## Cost Optimization

### Token Usage

Monitor token usage to control costs:

```python
# Track token usage per request
logger.info(f"Token usage: {response['usage']['total_tokens']}")
```

### Caching

Implement caching for frequent queries:

```python
from django.core.cache import cache

cache_key = f"query:{hash(query_text)}"
cached_response = cache.get(cache_key)
if cached_response:
    return Response(cached_response)
```

### Batch Processing

For high-volume scenarios, consider batch processing:

- Queue requests during peak times
- Process in batches to optimize AWS Bedrock usage
- Return cached responses for duplicate queries

## Support

For issues and questions:

- **API Issues**: Check logs with `docker-compose logs django`
- **Vapi.ai Issues**: Contact Vapi.ai support
- **Integration Help**: See main README.md

## Additional Resources

- [OpenAI API Reference](https://platform.openai.com/docs/api-reference/chat)
- [Vapi.ai Documentation](https://docs.vapi.ai/)
- [LlamaIndex Documentation](https://docs.llamaindex.ai/)
- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)

## Example Vapi.ai Assistant Configuration

Complete example for copy-paste:

```json
{
  "name": "Fintalk Banking Assistant",
  "model": {
    "provider": "custom-llm",
    "url": "https://api.yourdomain.com/api/agent/query/openai/",
    "model": "amazon.nova-lite-v1:0",
    "temperature": 0.7,
    "maxTokens": 2048
  },
  "voice": {
    "provider": "11labs",
    "voiceId": "professional-female",
    "stability": 0.5,
    "similarityBoost": 0.75
  },
  "firstMessage": "Hello! Thank you for calling FinTalk. I'm your banking assistant. How can I help you today?",
  "systemPrompt": "You are a professional banking call center agent for FinTalk. You assist customers with loan inquiries and credit card services. Always be polite, professional, and helpful. For credit card operations, always ask for the customer's phone number. Speak naturally and conversationally.",
  "endCallMessage": "Thank you for calling FinTalk. Have a great day!",
  "endCallPhrases": ["goodbye", "bye", "that's all", "thank you"],
  "recordingEnabled": true,
  "maxDurationSeconds": 600,
  "silenceTimeoutSeconds": 30,
  "responseDelaySeconds": 1,
  "interruptionsEnabled": true
}
```

This configuration provides a complete, production-ready voice assistant for banking services.
