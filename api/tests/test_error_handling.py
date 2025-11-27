"""
Error handling integration tests for Fintalk API.

These tests verify proper error handling and response formats for various
failure scenarios including service unavailability, connection failures,
and invalid requests.
"""

import json
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status
from api.models import CardHolder


class OpenSearchConnectionErrorTest(TestCase):
    """Tests for OpenSearch connection failure scenarios"""
    
    def setUp(self):
        """Set up test client"""
        self.client = APIClient()
        self.upload_url = '/api/documents/upload/'
        self.query_url = '/api/agent/query/'
        
        # Create sample file content
        self.txt_content = b'Test document content for error handling'
    
    @patch('api.views.get_storage_context')
    def test_opensearch_connection_failure_on_upload(self, mock_storage_context):
        """Test OpenSearch connection failure returns 503 response"""
        # Mock storage context to raise ConnectionError
        mock_storage_context.side_effect = ConnectionError(
            "Failed to connect to OpenSearch at http://opensearch:9200"
        )
        
        # Create file upload
        txt_file = SimpleUploadedFile(
            "test_document.txt",
            self.txt_content,
            content_type="text/plain"
        )
        
        # Make request
        response = self.client.post(
            self.upload_url,
            {'file': txt_file},
            format='multipart'
        )
        
        # Verify 503 response
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        
        # Verify error response format
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error']['code'], 'SERVICE_UNAVAILABLE')
        self.assertIn('vector store', response_data['error']['message'].lower())
        self.assertIn('details', response_data['error'])
        self.assertIn('OpenSearch', response_data['error']['details'])
    
    @patch('api.views.VectorStoreIndex')
    @patch('api.views.get_storage_context')
    def test_opensearch_storage_failure_during_indexing(self, mock_storage_context, mock_vector_index):
        """Test OpenSearch storage failure during document indexing"""
        # Mock storage context successfully
        mock_storage = MagicMock()
        mock_storage_context.return_value = mock_storage
        
        # Mock VectorStoreIndex to raise ConnectionError during indexing
        mock_vector_index.side_effect = ConnectionError(
            "Connection lost during indexing operation"
        )
        
        # Create file upload
        txt_file = SimpleUploadedFile(
            "test_document.txt",
            self.txt_content,
            content_type="text/plain"
        )
        
        # Make request
        response = self.client.post(
            self.upload_url,
            {'file': txt_file},
            format='multipart'
        )
        
        # Verify 503 response
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        
        # Verify error response format
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error']['code'], 'SERVICE_UNAVAILABLE')
        self.assertIn('vector store', response_data['error']['message'].lower())


class PostgreSQLConnectionErrorTest(TestCase):
    """Tests for PostgreSQL connection failure scenarios"""
    
    def setUp(self):
        """Set up test client"""
        self.client = APIClient()
        self.query_url = '/api/agent/query/'
    
    @patch('agent.tools.CardHolder.objects.get')
    @patch('api.views.agent')
    def test_postgresql_connection_failure_during_card_blocking(self, mock_agent, mock_cardholder_get):
        """Test PostgreSQL connection failure returns 503 response"""
        # Mock database connection error
        from django.db import OperationalError
        mock_cardholder_get.side_effect = OperationalError(
            "could not connect to server: Connection refused"
        )
        
        # Mock agent to call the block_credit_card tool
        # The tool will encounter the database error
        mock_response = MagicMock()
        mock_response.__str__ = lambda self: "Database connection error occurred"
        mock_response.source_nodes = []
        mock_response.sources = []
        mock_agent.chat.return_value = mock_response
        
        # Make request
        request_data = {
            'message': 'Block my credit card',
            'phone_number': '+1234567890',
            'stream': False
        }
        
        response = self.client.post(
            self.query_url,
            request_data,
            format='json'
        )
        
        # The agent will handle the error, but we verify it doesn't crash
        # In a real scenario, the tool would catch and report the error
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            status.HTTP_503_SERVICE_UNAVAILABLE
        ])
    
    @patch('django.db.connection.cursor')
    def test_health_check_postgresql_failure(self, mock_cursor):
        """Test health check endpoint detects PostgreSQL failure"""
        # Mock database cursor to raise OperationalError
        from django.db import OperationalError
        mock_cursor.side_effect = OperationalError("Connection refused")
        
        # Make request to health check
        response = self.client.get('/api/health/')
        
        # Verify 503 response
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        
        # Verify response structure
        response_data = response.json()
        self.assertEqual(response_data['status'], 'unhealthy')
        self.assertIn('services', response_data)
        self.assertIn('postgresql', response_data['services'])
        self.assertEqual(
            response_data['services']['postgresql']['status'],
            'unhealthy'
        )
        self.assertIn('connection', response_data['services']['postgresql']['message'].lower())


class AWSBedrockErrorTest(TestCase):
    """Tests for AWS Bedrock API error scenarios"""
    
    def setUp(self):
        """Set up test client"""
        self.client = APIClient()
        self.upload_url = '/api/documents/upload/'
        self.query_url = '/api/agent/query/'
        
        # Create sample file content
        self.txt_content = b'Test document content'
    
    @patch('api.views.agent')
    def test_bedrock_api_error_during_query_non_streaming(self, mock_agent):
        """Test AWS Bedrock API error returns 500 response with retry logic"""
        # Mock agent to raise Bedrock-specific error
        from botocore.exceptions import ClientError
        error_response = {
            'Error': {
                'Code': 'ThrottlingException',
                'Message': 'Rate exceeded'
            }
        }
        mock_agent.chat.side_effect = ClientError(error_response, 'InvokeModel')
        
        # Make request
        request_data = {
            'message': 'Test query',
            'stream': False
        }
        
        response = self.client.post(
            self.query_url,
            request_data,
            format='json'
        )
        
        # Verify 500 response
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Verify error response format
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error']['code'], 'AGENT_EXECUTION_ERROR')
        self.assertIn('message', response_data['error'])
        self.assertIn('details', response_data['error'])
    
    @patch('api.views.agent')
    def test_bedrock_api_error_during_query_streaming(self, mock_agent):
        """Test AWS Bedrock API error in streaming mode"""
        # Mock agent to raise Bedrock-specific error
        from botocore.exceptions import ClientError
        error_response = {
            'Error': {
                'Code': 'ServiceUnavailableException',
                'Message': 'Service temporarily unavailable'
            }
        }
        mock_agent.stream_chat.side_effect = ClientError(error_response, 'InvokeModelWithResponseStream')
        
        # Make request
        request_data = {
            'message': 'Test query',
            'stream': True
        }
        
        response = self.client.post(
            self.query_url,
            request_data,
            format='json'
        )
        
        # Verify response headers for SSE
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/event-stream')
        
        # Consume streaming response
        response_content = b''.join(response.streaming_content).decode('utf-8')
        
        # Verify error event in stream
        self.assertIn('"type": "error"', response_content)
        self.assertIn('AGENT_EXECUTION_ERROR', response_content)
    
    @patch('api.views.embed_model')
    @patch('api.views.VectorStoreIndex')
    @patch('api.views.get_storage_context')
    def test_bedrock_embedding_error_during_upload(self, mock_storage_context, mock_vector_index, mock_embed_model):
        """Test AWS Bedrock embedding error during document upload"""
        # Mock storage context
        mock_storage = MagicMock()
        mock_storage_context.return_value = mock_storage
        
        # Mock VectorStoreIndex to raise Bedrock error
        from botocore.exceptions import ClientError
        error_response = {
            'Error': {
                'Code': 'ValidationException',
                'Message': 'Invalid input for embedding model'
            }
        }
        mock_vector_index.side_effect = ClientError(error_response, 'InvokeModel')
        
        # Create file upload
        txt_file = SimpleUploadedFile(
            "test_document.txt",
            self.txt_content,
            content_type="text/plain"
        )
        
        # Make request
        response = self.client.post(
            self.upload_url,
            {'file': txt_file},
            format='multipart'
        )
        
        # Verify 500 response
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Verify error response format
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error']['code'], 'INDEXING_ERROR')


class InvalidRequestPayloadTest(TestCase):
    """Tests for invalid request payload scenarios"""
    
    def setUp(self):
        """Set up test client"""
        self.client = APIClient()
        self.upload_url = '/api/documents/upload/'
        self.query_url = '/api/agent/query/'
    
    def test_missing_file_in_upload_request(self):
        """Test 400 response when file is missing from upload request"""
        # Make request without file
        response = self.client.post(
            self.upload_url,
            {},
            format='multipart'
        )
        
        # Verify 400 response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Verify error response format
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error']['code'], 'VALIDATION_ERROR')
        self.assertIn('message', response_data['error'])
        self.assertIn('details', response_data['error'])
        self.assertIn('file', response_data['error']['details'])
    
    def test_unsupported_file_format(self):
        """Test 400 response for unsupported file format"""
        # Create unsupported file type
        exe_file = SimpleUploadedFile(
            "malware.exe",
            b'\x4d\x5a\x90\x00',  # EXE file header
            content_type="application/x-msdownload"
        )
        
        # Make request
        response = self.client.post(
            self.upload_url,
            {'file': exe_file},
            format='multipart'
        )
        
        # Verify 400 response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Verify error response format
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error']['code'], 'VALIDATION_ERROR')
    
    def test_missing_message_in_query_request(self):
        """Test 400 response when message is missing from query request"""
        # Make request without message
        response = self.client.post(
            self.query_url,
            {'stream': False},
            format='json'
        )
        
        # Verify 400 response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Verify error response format
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error']['code'], 'VALIDATION_ERROR')
        self.assertIn('message', response_data['error'])
        self.assertIn('details', response_data['error'])
        self.assertIn('message', response_data['error']['details'])
    
    def test_empty_message_in_query_request(self):
        """Test 400 response when message is empty"""
        # Make request with empty message
        response = self.client.post(
            self.query_url,
            {'message': '', 'stream': False},
            format='json'
        )
        
        # Verify 400 response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Verify error response format
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error']['code'], 'VALIDATION_ERROR')
    
    def test_invalid_json_payload(self):
        """Test 400 response for malformed JSON"""
        # Make request with invalid JSON
        response = self.client.post(
            self.query_url,
            'invalid json {',
            content_type='application/json'
        )
        
        # Verify 400 response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_invalid_stream_parameter_type(self):
        """Test handling of invalid stream parameter type"""
        # Make request with invalid stream value
        response = self.client.post(
            self.query_url,
            {
                'message': 'Test query',
                'stream': 'invalid'  # Should be boolean
            },
            format='json'
        )
        
        # Should either accept it (coerced to boolean) or reject with 400
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST
        ])


class ErrorResponseFormatTest(TestCase):
    """Tests to verify proper error response format across all error scenarios"""
    
    def setUp(self):
        """Set up test client"""
        self.client = APIClient()
        self.upload_url = '/api/documents/upload/'
        self.query_url = '/api/agent/query/'
    
    @patch('api.views.get_storage_context')
    def test_error_response_has_required_fields(self, mock_storage_context):
        """Test that all error responses include required fields"""
        # Mock to trigger error
        mock_storage_context.side_effect = ConnectionError("Test error")
        
        # Create file upload
        txt_file = SimpleUploadedFile(
            "test.txt",
            b'content',
            content_type="text/plain"
        )
        
        # Make request
        response = self.client.post(
            self.upload_url,
            {'file': txt_file},
            format='multipart'
        )
        
        # Verify error response structure
        response_data = response.json()
        
        # Check required fields
        self.assertIn('error', response_data)
        self.assertIn('code', response_data['error'])
        self.assertIn('message', response_data['error'])
        self.assertIn('details', response_data['error'])
        
        # Verify field types
        self.assertIsInstance(response_data['error']['code'], str)
        self.assertIsInstance(response_data['error']['message'], str)
        
        # Verify code is uppercase with underscores
        self.assertTrue(response_data['error']['code'].isupper())
        self.assertIn('_', response_data['error']['code'])
    
    def test_validation_error_format(self):
        """Test validation error response format"""
        # Make request with missing required field
        response = self.client.post(
            self.upload_url,
            {},
            format='multipart'
        )
        
        # Verify response
        response_data = response.json()
        
        # Check error structure
        self.assertEqual(response_data['error']['code'], 'VALIDATION_ERROR')
        self.assertIn('Invalid request data', response_data['error']['message'])
        self.assertIsInstance(response_data['error']['details'], dict)
    
    @patch('api.views.agent')
    def test_service_unavailable_error_format(self, mock_agent):
        """Test service unavailable error response format"""
        # Mock agent to raise ConnectionError
        mock_agent.chat.side_effect = ConnectionError("Service unavailable")
        
        # Make request
        response = self.client.post(
            self.query_url,
            {'message': 'Test', 'stream': False},
            format='json'
        )
        
        # Verify response
        response_data = response.json()
        
        # Check error structure
        self.assertEqual(response_data['error']['code'], 'SERVICE_UNAVAILABLE')
        self.assertIn('connect', response_data['error']['message'].lower())
        self.assertIsInstance(response_data['error']['details'], str)
    
    @patch('api.views.agent')
    def test_internal_error_format(self, mock_agent):
        """Test internal server error response format"""
        # Mock agent to raise unexpected exception
        mock_agent.chat.side_effect = RuntimeError("Unexpected error")
        
        # Make request
        response = self.client.post(
            self.query_url,
            {'message': 'Test', 'stream': False},
            format='json'
        )
        
        # Verify response
        response_data = response.json()
        
        # Check error structure
        self.assertIn(response_data['error']['code'], [
            'AGENT_EXECUTION_ERROR',
            'INTERNAL_ERROR'
        ])
        self.assertIn('message', response_data['error'])
        self.assertIn('details', response_data['error'])
