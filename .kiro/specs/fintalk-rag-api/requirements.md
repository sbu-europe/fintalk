# Requirements Document

## Introduction

Fintalk is a Django REST API that provides an AI-powered agent for financial document querying and credit card management. The system uses Retrieval-Augmented Generation (RAG) with LlamaIndex to enable users to query financial documents and perform credit card blocking operations through natural language interactions. The system leverages AWS Bedrock for AI capabilities, PostgreSQL for user data storage, and OpenSearch for vector-based document retrieval.

## Glossary

- **Fintalk System**: The complete Django REST API application including all components
- **RAG Agent**: The LlamaIndex-based agent that processes user queries using retrieval-augmented generation
- **Vector Store**: OpenSearch database storing document embeddings for semantic search
- **User Database**: PostgreSQL database storing user credentials and credit card information
- **Document Chunk**: A segmented portion of an uploaded document stored as a vector embedding
- **AWS Bedrock Service**: Amazon's managed service providing LLM and embedding models
- **Credit Card Blocking Tool**: Agent tool that deactivates credit cards in the database
- **Vector Retriever Tool**: Agent tool that searches document chunks using semantic similarity
- **Streaming Response**: Real-time token-by-token response delivery from the LLM

## Requirements

### Requirement 1

**User Story:** As a system administrator, I want to deploy the application using Docker containers, so that the environment is consistent and reproducible across different deployments

#### Acceptance Criteria

1. THE Fintalk System SHALL provide a Docker Compose configuration that orchestrates Django, PostgreSQL, and OpenSearch containers
2. THE Fintalk System SHALL configure persistent volumes for PostgreSQL data storage
3. THE Fintalk System SHALL configure persistent volumes for OpenSearch data storage
4. THE Fintalk System SHALL expose the Django API on a configurable host port
5. WHERE Docker Compose is executed, THE Fintalk System SHALL initialize all services with proper networking between containers

### Requirement 2

**User Story:** As a developer, I want to store user data securely in PostgreSQL, so that credit card information and user credentials are persisted reliably

#### Acceptance Criteria

1. THE Fintalk System SHALL define a User model containing username, phone number, and credit card number fields
2. THE Fintalk System SHALL define a credit card status field with active and blocked states
3. THE Fintalk System SHALL create database migrations for the User model
4. WHEN the database is initialized, THE Fintalk System SHALL populate the User Database with at least 10 dummy user records
5. THE Fintalk System SHALL ensure phone numbers are stored in a consistent format

### Requirement 3

**User Story:** As a user, I want to upload documents to the system, so that I can query their content using the AI agent

#### Acceptance Criteria

1. THE Fintalk System SHALL provide a REST API endpoint accepting document file uploads
2. WHEN a document is uploaded, THE Fintalk System SHALL chunk the document into segments suitable for embedding
3. WHEN a document is chunked, THE Fintalk System SHALL generate embeddings using AWS Bedrock embedding model
4. WHEN embeddings are generated, THE Fintalk System SHALL store the Document Chunks in the Vector Store
5. THE Fintalk System SHALL return a success response with document metadata after successful upload

### Requirement 4

**User Story:** As a developer, I want to configure OpenSearch as the vector database, so that document embeddings can be stored and retrieved efficiently

#### Acceptance Criteria

1. THE Fintalk System SHALL initialize an OpenSearch vector index with appropriate dimension settings for AWS Bedrock embeddings
2. THE Fintalk System SHALL configure LlamaIndex to use OpenSearch as the vector store backend
3. THE Fintalk System SHALL ensure the Vector Store supports similarity search operations
4. THE Fintalk System SHALL handle OpenSearch connection errors with appropriate error messages

### Requirement 5

**User Story:** As a developer, I want to create a LlamaIndex agent with specialized tools, so that users can query documents and manage credit cards through natural language

#### Acceptance Criteria

1. THE Fintalk System SHALL implement the Vector Retriever Tool that searches Document Chunks based on semantic similarity
2. THE Fintalk System SHALL implement the Credit Card Blocking Tool that accepts a phone number parameter
3. WHEN the Credit Card Blocking Tool is invoked with a phone number, THE Fintalk System SHALL update the corresponding user record status to blocked in the User Database
4. THE Fintalk System SHALL configure the RAG Agent with both tools available for dynamic selection
5. WHEN the RAG Agent receives a query, THE Fintalk System SHALL enable the agent to autonomously select and invoke appropriate tools based on query intent
6. THE Fintalk System SHALL configure the RAG Agent to use AWS Bedrock LLM for reasoning and response generation

### Requirement 6

**User Story:** As a user, I want to send natural language queries to the agent, so that I can retrieve information from documents or perform credit card operations

#### Acceptance Criteria

1. THE Fintalk System SHALL provide a REST API endpoint accepting agent query requests with a message body
2. WHEN a query is received, THE Fintalk System SHALL pass the query to the RAG Agent for processing
3. THE Fintalk System SHALL enable streaming responses from AWS Bedrock Service
4. WHEN the agent generates a response, THE Fintalk System SHALL stream tokens to the client in real-time
5. IF the agent invokes the Credit Card Blocking Tool, THEN THE Fintalk System SHALL extract the phone number from the request body and pass it to the tool

### Requirement 7

**User Story:** As a developer, I want to integrate AWS Bedrock for embeddings and LLM capabilities, so that the system uses managed AI services without hosting models locally

#### Acceptance Criteria

1. THE Fintalk System SHALL configure AWS Bedrock credentials from environment variables
2. THE Fintalk System SHALL use AWS Bedrock embedding model for document vectorization
3. THE Fintalk System SHALL use AWS Bedrock LLM for agent reasoning and response generation
4. THE Fintalk System SHALL support streaming mode for LLM responses
5. THE Fintalk System SHALL handle AWS Bedrock API errors with appropriate error responses

### Requirement 8

**User Story:** As a quality assurance engineer, I want comprehensive tests for all functionality, so that I can verify the system works correctly and catch regressions

#### Acceptance Criteria

1. THE Fintalk System SHALL include unit tests for the User model and database operations
2. THE Fintalk System SHALL include integration tests for the document upload endpoint
3. THE Fintalk System SHALL include integration tests for the agent query endpoint
4. THE Fintalk System SHALL include tests for the Credit Card Blocking Tool functionality
5. THE Fintalk System SHALL include tests for the Vector Retriever Tool functionality
6. THE Fintalk System SHALL include tests verifying AWS Bedrock integration with mocked responses

### Requirement 9

**User Story:** As a system administrator, I want proper error handling throughout the application, so that failures are logged and communicated clearly to clients

#### Acceptance Criteria

1. IF a document upload fails, THEN THE Fintalk System SHALL return an error response with a descriptive message
2. IF an agent query fails, THEN THE Fintalk System SHALL return an error response with a descriptive message
3. IF the Vector Store is unavailable, THEN THE Fintalk System SHALL return a service unavailable error
4. IF the User Database is unavailable, THEN THE Fintalk System SHALL return a service unavailable error
5. THE Fintalk System SHALL log all errors with sufficient context for debugging

### Requirement 10

**User Story:** As a developer, I want clear API documentation, so that I can understand how to interact with the endpoints

#### Acceptance Criteria

1. THE Fintalk System SHALL document the document upload endpoint including accepted file formats and request structure
2. THE Fintalk System SHALL document the agent query endpoint including request body schema and streaming response format
3. THE Fintalk System SHALL document required environment variables for AWS Bedrock configuration
4. THE Fintalk System SHALL document the Docker Compose setup and initialization steps
5. THE Fintalk System SHALL provide example requests for both endpoints
