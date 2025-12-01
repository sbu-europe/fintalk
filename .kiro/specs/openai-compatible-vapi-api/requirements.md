# Requirements Document

## Introduction

This document specifies the requirements for an OpenAI-compatible API endpoint that will be integrated with Vapi.ai's custom URL feature. The API will receive requests in OpenAI's standard format, process them using the existing agent system, and return responses in OpenAI-compatible format.

## Glossary

- **API Endpoint**: The `/agent/query/` URL that receives HTTP requests
- **OpenAI Format**: The standard request/response structure used by OpenAI's Chat Completions API
- **Vapi.ai**: A voice AI platform that can integrate with custom APIs
- **Agent System**: The existing RAG-based agent that processes queries
- **Chat Completion**: An OpenAI API response containing generated text
- **Message Object**: A structured object containing role and content fields

## Requirements

### Requirement 1

**User Story:** As a Vapi.ai integration developer, I want to send requests to the API in OpenAI format, so that I can use standard OpenAI client libraries and tools.

#### Acceptance Criteria

1. WHEN a POST request arrives at `/agent/query/`, THE API Endpoint SHALL accept a JSON payload with `messages` array field
2. THE API Endpoint SHALL validate that each message in the `messages` array contains `role` and `content` fields
3. THE API Endpoint SHALL support `model` field in the request payload
4. THE API Endpoint SHALL support optional `temperature` field in the request payload
5. IF the request payload is missing required fields, THEN THE API Endpoint SHALL return a 400 status code with error details

### Requirement 2

**User Story:** As a Vapi.ai integration developer, I want to receive responses in OpenAI format, so that my integration works seamlessly with OpenAI-compatible tools.

#### Acceptance Criteria

1. THE API Endpoint SHALL return responses with `id`, `object`, `created`, `model`, and `choices` fields
2. THE API Endpoint SHALL include a `choices` array containing at least one choice object
3. WHEN processing is successful, THE API Endpoint SHALL set `choices[0].message.role` to "assistant"
4. THE API Endpoint SHALL include the agent's response text in `choices[0].message.content`
5. THE API Endpoint SHALL include `usage` object with token count information

### Requirement 3

**User Story:** As a system administrator, I want the API to handle errors gracefully, so that integration issues can be diagnosed quickly.

#### Acceptance Criteria

1. IF the Agent System fails to process a query, THEN THE API Endpoint SHALL return a 500 status code with error details
2. IF authentication fails, THEN THE API Endpoint SHALL return a 401 status code
3. THE API Endpoint SHALL log all requests and responses for debugging purposes
4. THE API Endpoint SHALL include descriptive error messages in the response body
5. WHEN an error occurs, THE API Endpoint SHALL return an error response in OpenAI-compatible format

### Requirement 4

**User Story:** As a Vapi.ai integration developer, I want the API to process conversation context, so that multi-turn conversations work correctly.

#### Acceptance Criteria

1. THE API Endpoint SHALL extract all messages from the `messages` array
2. THE API Endpoint SHALL pass conversation history to the Agent System
3. WHEN multiple messages exist, THE API Endpoint SHALL maintain message order
4. THE API Endpoint SHALL identify the most recent user message for processing
5. THE API Endpoint SHALL support system, user, and assistant role types

### Requirement 5

**User Story:** As a developer, I want the API to integrate with existing authentication, so that security is maintained consistently.

#### Acceptance Criteria

1. THE API Endpoint SHALL use the existing Django authentication mechanism
2. IF no valid authentication is provided, THEN THE API Endpoint SHALL return a 401 status code
3. THE API Endpoint SHALL support API key authentication via headers
4. THE API Endpoint SHALL validate user permissions before processing requests
5. THE API Endpoint SHALL associate requests with authenticated users for audit purposes
