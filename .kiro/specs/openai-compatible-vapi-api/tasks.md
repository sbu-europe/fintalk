# Implementation Plan: OpenAI-Compatible API

- [ ] 1. Create OpenAI request/response serializers
  - Create `OpenAIMessageSerializer` to validate individual message objects with role and content fields
  - Create `OpenAIQuerySerializer` to validate the complete request including messages array, model, temperature, max_tokens, and stream parameters
  - Add validation logic to ensure at least one message exists and temperature/max_tokens are within valid ranges
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [ ] 2. Implement helper functions for message processing and response formatting
- [ ] 2.1 Create message extraction function
  - Write `_extract_query_and_context()` function to parse OpenAI messages array
  - Extract system messages, conversation history, and latest user message
  - Implement phone number extraction from message content using regex pattern `[phone: +1234567890]`
  - Combine all message components into a single query string for the agent
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 2.2 Create OpenAI response formatter
  - Write `_format_openai_response()` function to convert agent response to OpenAI format
  - Generate unique completion ID with format `chatcmpl-{uuid}`
  - Implement token count estimation (1 token ≈ 4 characters)
  - Build response structure with id, object, created, model, choices, and usage fields
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ] 2.3 Create error response formatter
  - Write `_format_openai_error()` function to format errors in OpenAI style
  - Support error types: invalid_request_error, authentication_error, server_error, service_unavailable_error
  - Include message, type, param, code, and details fields as appropriate
  - Return DRF Response with correct HTTP status code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 2.4 Create synchronous agent execution wrapper
  - Write `_execute_agent_sync()` function to execute agent and return response text
  - Reuse existing async agent execution logic from `agent_query` view
  - Add phone number context to query if provided
  - Handle agent initialization errors and execution failures
  - _Requirements: 4.2, 4.5_

- [ ] 3. Implement main OpenAI endpoint view
  - Create `openai_agent_query()` view function decorated with `@api_view(['POST'])`
  - Validate request using `OpenAIQuerySerializer`
  - Extract messages, temperature, max_tokens, and stream parameters
  - Call `_extract_query_and_context()` to process messages
  - Execute agent using `_execute_agent_sync()`
  - Format response using `_format_openai_response()`
  - Handle all error scenarios with appropriate OpenAI error responses
  - Add comprehensive logging for debugging and monitoring
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 4. Add URL routing for new endpoint
  - Add route `path('agent/query/openai/', views.openai_agent_query, name='openai_agent_query')` to `api/urls.py`
  - Ensure route is placed appropriately in the urlpatterns list
  - _Requirements: 1.1_

- [ ]* 5. Write comprehensive tests
- [ ]* 5.1 Create unit tests for serializers
  - Test `OpenAIMessageSerializer` with valid and invalid role values
  - Test `OpenAIQuerySerializer` with various message configurations
  - Test validation of temperature and max_tokens ranges
  - Test empty messages array validation
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [ ]* 5.2 Create unit tests for helper functions
  - Test `_extract_query_and_context()` with different message combinations
  - Test phone number extraction with various formats
  - Test `_format_openai_response()` output structure
  - Test token count estimation accuracy
  - Test `_format_openai_error()` with different error types
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ]* 5.3 Create integration tests for the endpoint
  - Test successful query with single user message
  - Test query with conversation history
  - Test query with system message
  - Test phone number extraction and credit card operations
  - Test error responses for invalid requests
  - Test agent execution failures
  - Test authentication requirements
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ]* 6. Create documentation and integration guide
  - Add endpoint documentation to README.md with request/response examples
  - Create Vapi.ai integration guide with configuration steps
  - Document phone number format for credit card operations
  - Add curl examples for testing the endpoint
  - _Requirements: 1.1, 2.1, 4.1_
