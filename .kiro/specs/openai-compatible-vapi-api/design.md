# Design Document: OpenAI-Compatible API for Vapi.ai Integration

## Overview

This document outlines the design for an OpenAI-compatible API endpoint that will integrate with Vapi.ai's custom URL feature. The endpoint will accept requests in OpenAI's Chat Completions API format, process them through the existing RAG agent system, and return responses in OpenAI-compatible format.

The design leverages the existing Django REST Framework infrastructure and LlamaIndex agent while adding a translation layer to convert between OpenAI format and the internal agent format.

## Architecture

### High-Level Flow

```
┌─────────────┐
│   Vapi.ai   │
└──────┬──────┘
       │ POST /api/agent/query/openai/
       │ OpenAI Format Request
       ▼
┌──────────────────────────────────────┐
│  OpenAI Compatibility Layer          │
│  ┌────────────────────────────────┐  │
│  │ 1. Validate OpenAI Request     │  │
│  │ 2. Extract messages & context  │  │
│  │ 3. Convert to internal format  │  │
│  └────────────────────────────────┘  │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│  Existing Agent System                │
│  ┌────────────────────────────────┐  │
│  │ LlamaIndex ReActAgent          │  │
│  │ - Vector Search Tool           │  │
│  │ - Credit Card Blocker Tool     │  │
│  │ - Credit Card Enabler Tool     │  │
│  └────────────────────────────────┘  │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│  OpenAI Response Formatter            │
│  ┌────────────────────────────────┐  │
│  │ 1. Get agent response          │  │
│  │ 2. Format as OpenAI completion │  │
│  │ 3. Add metadata (id, tokens)   │  │
│  └────────────────────────────────┘  │
└──────────────┬───────────────────────┘
               │ OpenAI Format Response
               ▼
┌──────────────────────────────────────┐
│   Vapi.ai                             │
└──────────────────────────────────────┘
```

### Component Interaction

```
┌─────────────────────────────────────────────────────────────┐
│                    Django REST Framework                     │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  openai_agent_query() View                         │    │
│  │                                                     │    │
│  │  1. Parse OpenAI request                           │    │
│  │  2. Validate with OpenAIQuerySerializer            │    │
│  │  3. Extract conversation context                   │    │
│  │  4. Call existing agent                            │    │
│  │  5. Format response as OpenAI completion           │    │
│  └────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           ▼                                  │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Existing agent_query() Logic                      │    │
│  │  - Agent execution                                 │    │
│  │  - Tool selection                                  │    │
│  │  - Response generation                             │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. OpenAI Request Format

The endpoint will accept the standard OpenAI Chat Completions API format:

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
    },
    {
      "role": "assistant",
      "content": "We offer personal loans, home loans, and auto loans."
    },
    {
      "role": "user",
      "content": "Tell me more about personal loans"
    }
  ],
  "temperature": 0.7,
  "max_tokens": 2048,
  "stream": true
}
```

**Field Specifications:**
- `model` (string, optional): Model identifier (ignored, uses configured Bedrock model)
- `messages` (array, required): Array of message objects with `role` and `content`
- `temperature` (float, optional): Sampling temperature (0.0 to 2.0)
- `max_tokens` (integer, optional): Maximum tokens in response
- `stream` (boolean, optional): Whether to stream the response (default: false)

**Supported Roles:**
- `system`: System instructions (combined with user message)
- `user`: User messages
- `assistant`: Previous assistant responses (for context)

### 2. OpenAI Response Format

The endpoint will return responses in OpenAI Chat Completions format:

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
        "content": "Personal loans are unsecured loans that can be used for various purposes..."
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

**Field Specifications:**
- `id` (string): Unique identifier for the completion (format: `chatcmpl-{uuid}`)
- `object` (string): Always "chat.completion"
- `created` (integer): Unix timestamp of creation
- `model` (string): Model used (reflects actual Bedrock model)
- `choices` (array): Array of completion choices (always 1 element)
  - `index` (integer): Choice index (always 0)
  - `message` (object): The generated message
    - `role` (string): Always "assistant"
    - `content` (string): The response text
  - `finish_reason` (string): Reason for completion ("stop", "length", or "error")
- `usage` (object): Token usage statistics
  - `prompt_tokens` (integer): Estimated input tokens
  - `completion_tokens` (integer): Estimated output tokens
  - `total_tokens` (integer): Sum of prompt and completion tokens

### 3. Error Response Format

Errors will follow OpenAI's error format:

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

**Error Types:**
- `invalid_request_error`: Validation errors (400)
- `authentication_error`: Auth failures (401)
- `server_error`: Internal errors (500)
- `service_unavailable_error`: Service unavailable (503)

### 4. Serializer Design

**OpenAIMessageSerializer:**
```python
class OpenAIMessageSerializer(serializers.Serializer):
    """Serializer for individual OpenAI message objects"""
    role = serializers.ChoiceField(
        choices=['system', 'user', 'assistant'],
        required=True
    )
    content = serializers.CharField(required=True, allow_blank=False)
```

**OpenAIQuerySerializer:**
```python
class OpenAIQuerySerializer(serializers.Serializer):
    """Serializer for OpenAI Chat Completions API request"""
    model = serializers.CharField(required=False, default='amazon.nova-lite-v1:0')
    messages = OpenAIMessageSerializer(many=True, required=True)
    temperature = serializers.FloatField(
        required=False,
        default=0.7,
        min_value=0.0,
        max_value=2.0
    )
    max_tokens = serializers.IntegerField(
        required=False,
        default=2048,
        min_value=1,
        max_value=4096
    )
    stream = serializers.BooleanField(required=False, default=False)
    
    def validate_messages(self, messages):
        """Ensure at least one message exists"""
        if not messages:
            raise serializers.ValidationError("At least one message is required")
        return messages
```

### 5. View Implementation

**Endpoint:** `POST /api/agent/query/openai/`

**View Function Structure:**
```python
@api_view(['POST'])
def openai_agent_query(request):
    """
    OpenAI-compatible endpoint for Vapi.ai integration.
    
    Accepts requests in OpenAI Chat Completions format and returns
    responses in the same format, while using the existing RAG agent
    internally.
    """
    # 1. Validate request
    serializer = OpenAIQuerySerializer(data=request.data)
    if not serializer.is_valid():
        return _format_openai_error(
            message="Invalid request",
            error_type="invalid_request_error",
            status_code=400,
            details=serializer.errors
        )
    
    # 2. Extract and process messages
    messages = serializer.validated_data['messages']
    temperature = serializer.validated_data.get('temperature', 0.7)
    max_tokens = serializer.validated_data.get('max_tokens', 2048)
    stream = serializer.validated_data.get('stream', False)
    
    # 3. Convert to internal format
    query_text, phone_number = _extract_query_and_context(messages)
    
    # 4. Execute agent (reuse existing logic)
    try:
        if stream:
            # Note: Streaming not initially supported for OpenAI endpoint
            return _format_openai_error(
                message="Streaming not supported for OpenAI endpoint",
                error_type="invalid_request_error",
                status_code=400
            )
        else:
            agent_response = _execute_agent_sync(query_text, phone_number)
    except Exception as e:
        return _format_openai_error(
            message=f"Agent execution failed: {str(e)}",
            error_type="server_error",
            status_code=500
        )
    
    # 5. Format as OpenAI response
    openai_response = _format_openai_response(
        content=agent_response,
        model=serializer.validated_data.get('model', 'amazon.nova-lite-v1:0'),
        prompt_text=query_text
    )
    
    return Response(openai_response, status=status.HTTP_200_OK)
```

### 6. Helper Functions

**Message Processing:**
```python
def _extract_query_and_context(messages: list) -> tuple[str, str]:
    """
    Extract the user query and phone number context from OpenAI messages.
    
    Combines system messages, conversation history, and the latest user
    message into a single query string. Extracts phone number if present.
    
    Args:
        messages: List of OpenAI message objects
        
    Returns:
        Tuple of (query_text, phone_number)
    """
    system_messages = []
    conversation_history = []
    user_message = ""
    phone_number = ""
    
    for msg in messages:
        role = msg['role']
        content = msg['content']
        
        if role == 'system':
            system_messages.append(content)
        elif role == 'user':
            user_message = content
            # Extract phone number if present in format [phone: +1234567890]
            phone_match = re.search(r'\[phone:\s*([+\d\s-]+)\]', content)
            if phone_match:
                phone_number = phone_match.group(1).strip()
                # Remove phone tag from message
                user_message = re.sub(r'\[phone:\s*[+\d\s-]+\]', '', content).strip()
        elif role == 'assistant':
            conversation_history.append(f"Assistant: {content}")
    
    # Build complete query
    query_parts = []
    
    if system_messages:
        query_parts.append("System Instructions: " + " ".join(system_messages))
    
    if conversation_history:
        query_parts.append("Conversation History:\n" + "\n".join(conversation_history))
    
    query_parts.append(f"User: {user_message}")
    
    query_text = "\n\n".join(query_parts)
    
    return query_text, phone_number
```

**Response Formatting:**
```python
def _format_openai_response(
    content: str,
    model: str,
    prompt_text: str
) -> dict:
    """
    Format agent response as OpenAI Chat Completion.
    
    Args:
        content: The agent's response text
        model: Model identifier
        prompt_text: The input prompt (for token estimation)
        
    Returns:
        OpenAI-formatted response dictionary
    """
    import time
    import uuid
    
    # Generate unique completion ID
    completion_id = f"chatcmpl-{uuid.uuid4().hex[:24]}"
    
    # Estimate token counts (rough approximation: 1 token ≈ 4 characters)
    prompt_tokens = len(prompt_text) // 4
    completion_tokens = len(content) // 4
    total_tokens = prompt_tokens + completion_tokens
    
    return {
        "id": completion_id,
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens
        }
    }
```

**Error Formatting:**
```python
def _format_openai_error(
    message: str,
    error_type: str,
    status_code: int,
    param: str = None,
    code: str = None,
    details: dict = None
) -> Response:
    """
    Format error response in OpenAI format.
    
    Args:
        message: Error message
        error_type: Type of error (invalid_request_error, server_error, etc.)
        status_code: HTTP status code
        param: Parameter that caused the error (optional)
        code: Error code (optional)
        details: Additional error details (optional)
        
    Returns:
        DRF Response with OpenAI-formatted error
    """
    error_response = {
        "error": {
            "message": message,
            "type": error_type
        }
    }
    
    if param:
        error_response["error"]["param"] = param
    
    if code:
        error_response["error"]["code"] = code
    
    if details:
        error_response["error"]["details"] = details
    
    return Response(error_response, status=status_code)
```

**Agent Execution:**
```python
def _execute_agent_sync(query_text: str, phone_number: str = None) -> str:
    """
    Execute the agent synchronously and return the response text.
    
    Reuses the existing agent execution logic from agent_query view
    but returns only the response text.
    
    Args:
        query_text: The query to process
        phone_number: Optional phone number for credit card operations
        
    Returns:
        Agent response as string
        
    Raises:
        Exception: If agent execution fails
    """
    import asyncio
    from agent.agent import agent
    
    if agent is None:
        raise RuntimeError("Agent is not initialized")
    
    # Add phone number context if provided
    if phone_number:
        query_text = f"{query_text}\n\n[User phone number: {phone_number}]"
    
    # Run agent asynchronously
    async def run_agent():
        handler = agent.run(user_msg=query_text)
        response = await handler
        return response
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        response = loop.run_until_complete(run_agent())
        return str(response)
    finally:
        loop.close()
```

## Data Models

No new database models are required. The endpoint will use the existing `CardHolder` model for credit card operations.

## Error Handling

### Error Scenarios and Responses

| Scenario | HTTP Status | Error Type | Response |
|----------|-------------|------------|----------|
| Missing `messages` field | 400 | invalid_request_error | Missing required parameter |
| Empty `messages` array | 400 | invalid_request_error | At least one message required |
| Invalid `role` value | 400 | invalid_request_error | Invalid role (must be system/user/assistant) |
| Invalid `temperature` | 400 | invalid_request_error | Temperature must be between 0.0 and 2.0 |
| Invalid `max_tokens` | 400 | invalid_request_error | max_tokens must be positive |
| Authentication failure | 401 | authentication_error | Invalid or missing authentication |
| Agent not initialized | 503 | service_unavailable_error | Agent service unavailable |
| Agent execution error | 500 | server_error | Internal server error |
| Database connection error | 503 | service_unavailable_error | Database unavailable |

### Error Logging

All errors will be logged with appropriate context:
```python
logger.error(
    f"OpenAI endpoint error: {error_type}",
    extra={
        'request_data': request.data,
        'error_details': str(e),
        'user': request.user if request.user.is_authenticated else 'anonymous'
    }
)
```

## Testing Strategy

### Unit Tests

**Test File:** `api/tests/test_openai_views.py`

**Test Cases:**
1. **Valid Request Handling**
   - Test with single user message
   - Test with conversation history
   - Test with system message
   - Test with phone number extraction

2. **Request Validation**
   - Test missing `messages` field
   - Test empty `messages` array
   - Test invalid role values
   - Test invalid temperature values
   - Test invalid max_tokens values

3. **Response Formatting**
   - Verify OpenAI response structure
   - Verify completion ID format
   - Verify token count estimation
   - Verify finish_reason values

4. **Error Handling**
   - Test agent initialization failure
   - Test agent execution failure
   - Test database connection errors
   - Test authentication errors

5. **Context Extraction**
   - Test phone number extraction from messages
   - Test conversation history assembly
   - Test system message handling
   - Test multi-turn conversations

### Integration Tests

**Test Scenarios:**
1. End-to-end query with document search
2. End-to-end query with credit card blocking
3. Multi-turn conversation flow
4. Error recovery and graceful degradation

### Vapi.ai Integration Tests

**Manual Test Cases:**
1. Configure Vapi.ai with custom URL endpoint
2. Test voice-to-text query processing
3. Test text-to-voice response delivery
4. Test conversation state management
5. Test error handling in voice interface

## Security Considerations

### Authentication

The endpoint will use the existing Django authentication mechanism:
- API key authentication via `Authorization` header
- Session-based authentication for web clients
- Token-based authentication for mobile clients

### Input Validation

- All inputs validated through DRF serializers
- Message content sanitized to prevent injection attacks
- Phone number format validation
- Rate limiting: 100 requests/minute per user

### Data Privacy

- Credit card numbers never included in responses
- Phone numbers logged only in secure audit logs
- Conversation history not persisted (stateless)
- PII redacted from error messages

## Performance Considerations

### Response Time Targets

- P50: < 2 seconds
- P95: < 5 seconds
- P99: < 10 seconds

### Optimization Strategies

1. **Reuse Existing Agent Logic**
   - No duplication of agent execution code
   - Shared connection pools
   - Shared vector store connections

2. **Token Estimation**
   - Fast character-based estimation (not actual tokenization)
   - Acceptable accuracy for usage tracking

3. **Async Execution**
   - Reuse existing async agent execution
   - Non-blocking I/O for database and vector store

4. **Caching** (Future Enhancement)
   - Cache frequent queries
   - Cache cardholder lookups
   - TTL: 5 minutes

## Deployment Considerations

### Configuration

New environment variables (optional):
```bash
# OpenAI Endpoint Configuration
OPENAI_ENDPOINT_ENABLED=true
OPENAI_ENDPOINT_RATE_LIMIT=100  # requests per minute
```

### URL Routing

Add to `api/urls.py`:
```python
urlpatterns = [
    # ... existing routes ...
    path('agent/query/openai/', views.openai_agent_query, name='openai_agent_query'),
]
```

### Monitoring

- Log all OpenAI endpoint requests
- Track response times
- Monitor error rates
- Alert on high error rates (> 5%)

### Backward Compatibility

- Existing `/api/agent/query/` endpoint unchanged
- No breaking changes to existing functionality
- New endpoint is additive only

## Future Enhancements

### Phase 2 Features

1. **Streaming Support**
   - Implement Server-Sent Events for OpenAI endpoint
   - Stream tokens as they're generated
   - Compatible with OpenAI streaming format

2. **Function Calling**
   - Expose agent tools as OpenAI functions
   - Support function call format in responses
   - Enable Vapi.ai to trigger specific actions

3. **Conversation Memory**
   - Optional conversation state persistence
   - Session-based context management
   - Configurable memory window

4. **Enhanced Token Counting**
   - Use actual tokenizer for accurate counts
   - Support for different model tokenizers
   - Billing-accurate token tracking

5. **Multi-Model Support**
   - Route to different Bedrock models based on `model` parameter
   - Support for model aliases
   - Automatic fallback on model unavailability

## Vapi.ai Integration Guide

### Configuration Steps

1. **Create Custom LLM in Vapi.ai:**
   - Navigate to Vapi.ai dashboard
   - Go to "Custom LLM" settings
   - Add new custom LLM provider

2. **Configure Endpoint:**
   ```
   URL: https://your-domain.com/api/agent/query/openai/
   Method: POST
   Headers:
     - Authorization: Bearer YOUR_API_KEY
     - Content-Type: application/json
   ```

3. **Test Configuration:**
   - Use Vapi.ai's test interface
   - Send sample query
   - Verify response format

4. **Create Voice Assistant:**
   - Create new assistant in Vapi.ai
   - Select custom LLM as provider
   - Configure voice settings
   - Set system prompt

### Example Vapi.ai Configuration

```json
{
  "name": "Fintalk Banking Assistant",
  "model": {
    "provider": "custom-llm",
    "url": "https://your-domain.com/api/agent/query/openai/",
    "model": "amazon.nova-lite-v1:0"
  },
  "voice": {
    "provider": "11labs",
    "voiceId": "professional-female"
  },
  "firstMessage": "Hello! I'm your Fintalk banking assistant. How can I help you today?",
  "systemPrompt": "You are a professional banking call center agent for FinTalk, assisting customers with loan inquiries and credit card services."
}
```

## Appendix

### OpenAI API Reference

Official documentation: https://platform.openai.com/docs/api-reference/chat

### Vapi.ai Custom LLM Documentation

Official documentation: https://docs.vapi.ai/custom-llm

### Example Request/Response

**Request:**
```bash
curl -X POST https://your-domain.com/api/agent/query/openai/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {
        "role": "system",
        "content": "You are a helpful banking assistant."
      },
      {
        "role": "user",
        "content": "What loan options do you have? [phone: +1234567890]"
      }
    ],
    "temperature": 0.7
  }'
```

**Response:**
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
