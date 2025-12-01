# OpenAI Endpoint Quick Reference

## Endpoint

```
POST /api/chat/completions/
```

## Minimal Request (Streaming - Default)

```bash
curl -X POST http://localhost:8000/api/chat/completions/ \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Your question here"}
    ]
  }'
```

## Non-Streaming Request

```bash
curl -X POST http://localhost:8000/api/chat/completions/ \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Your question here"}
    ],
    "stream": false
  }'
```

## Full Request Example

```json
{
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
  "max_tokens": 2048
}
```

## Response Example

```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "amazon.nova-lite-v1:0",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "We offer personal loans, home loans, and auto loans..."
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 45,
    "completion_tokens": 120,
    "total_tokens": 165
  }
}
```

## Special Features

### Phone Number for Credit Card Operations

```json
{
  "messages": [
    {
      "role": "user",
      "content": "Block my credit card [phone: +1234567890]"
    }
  ]
}
```

### Multi-turn Conversation

```json
{
  "messages": [
    {"role": "user", "content": "What loans do you offer?"},
    {"role": "assistant", "content": "We offer personal, home, and auto loans."},
    {"role": "user", "content": "Tell me about personal loans"}
  ]
}
```

## Parameters

| Parameter | Type | Required | Default | Range |
|-----------|------|----------|---------|-------|
| `messages` | array | Yes | - | 1+ messages |
| `model` | string | No | `amazon.nova-lite-v1:0` | Any string |
| `temperature` | float | No | 0.7 | 0.0 - 2.0 |
| `max_tokens` | integer | No | 2048 | 1 - 4096 |
| `stream` | boolean | No | true | Enable SSE streaming |

## Message Roles

- `system` - System instructions
- `user` - User messages
- `assistant` - Previous assistant responses

## Error Codes

| HTTP Status | Error Type | Description |
|-------------|------------|-------------|
| 400 | `invalid_request_error` | Invalid parameters |
| 401 | `authentication_error` | Auth failed |
| 500 | `server_error` | Internal error |
| 503 | `service_unavailable_error` | Service down |

## Testing

```bash
# Run test suite
./test_openai_endpoint.sh

# Test streaming
curl -X POST http://localhost:8000/api/chat/completions/ \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello"}], "stream": true}'

# Test non-streaming
curl -X POST http://localhost:8000/api/chat/completions/ \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello"}], "stream": false}'
```

## Vapi.ai Configuration

```json
{
  "model": {
    "provider": "custom-llm",
    "url": "https://your-domain.com/api/chat/completions/",
    "model": "amazon.nova-lite-v1:0"
  }
}
```

## Files

- `api/views.py` - Main endpoint implementation
- `api/serializers.py` - Request validation
- `api/urls.py` - URL routing
- `VAPI_INTEGRATION.md` - Full integration guide
- `test_openai_endpoint.sh` - Test script

## Common Issues

**Issue**: Connection refused
**Fix**: Ensure API is running: `docker-compose up -d`

**Issue**: Invalid request error
**Fix**: Check messages array format

**Issue**: Agent not initialized
**Fix**: Check AWS credentials in `.env`

**Issue**: Slow responses
**Fix**: Check AWS Bedrock latency and OpenSearch performance

## Support

- Main docs: `README.md`
- Integration guide: `VAPI_INTEGRATION.md`
- Summary: `OPENAI_ENDPOINT_SUMMARY.md`
