import os
import io
import json
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status


class DocumentUploadIntegrationTest(TestCase):
    """Integration tests for document upload endpoint"""
    
    def setUp(self):
        """Set up test client and mock data"""
        self.client = APIClient()
        self.upload_url = '/api/documents/upload/'
        
        # Create sample PDF content (minimal valid PDF)
        self.pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/Resources <<\n/Font <<\n/F1 <<\n/Type /Font\n/Subtype /Type1\n/BaseFont /Helvetica\n>>\n>>\n>>\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(Test PDF) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n0000000317 00000 n\ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n410\n%%EOF'
        
        # Create sample TXT content
        self.txt_content = b'This is a test document for financial analysis.\nIt contains important information about loan schemes.'
    
    @patch('api.views.VectorStoreIndex')
    @patch('api.views.get_storage_context')
    @patch('api.views.embed_model')
    def test_successful_pdf_upload(self, mock_embed_model, mock_storage_context, mock_vector_index):
        """Test successful document upload with PDF file"""
        # Mock the storage context and vector index
        mock_storage = MagicMock()
        mock_storage_context.return_value = mock_storage
        
        mock_index_instance = MagicMock()
        mock_vector_index.return_value = mock_index_instance
        
        # Create a PDF file upload
        pdf_file = SimpleUploadedFile(
            "test_document.pdf",
            self.pdf_content,
            content_type="application/pdf"
        )
        
        # Make the request
        response = self.client.post(
            self.upload_url,
            {'file': pdf_file},
            format='multipart'
        )
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_data = response.json()
        self.assertEqual(response_data['status'], 'success')
        self.assertIn('document_id', response_data)
        self.assertIn('chunks_created', response_data)
        self.assertEqual(response_data['filename'], 'test_document.pdf')
        self.assertIn('message', response_data)
        self.assertGreater(response_data['chunks_created'], 0)
    
    @patch('api.views.VectorStoreIndex')
    @patch('api.views.get_storage_context')
    @patch('api.views.embed_model')
    def test_successful_txt_upload(self, mock_embed_model, mock_storage_context, mock_vector_index):
        """Test successful document upload with TXT file"""
        # Mock the storage context and vector index
        mock_storage = MagicMock()
        mock_storage_context.return_value = mock_storage
        
        mock_index_instance = MagicMock()
        mock_vector_index.return_value = mock_index_instance
        
        # Create a TXT file upload
        txt_file = SimpleUploadedFile(
            "test_document.txt",
            self.txt_content,
            content_type="text/plain"
        )
        
        # Make the request
        response = self.client.post(
            self.upload_url,
            {'file': txt_file},
            format='multipart'
        )
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_data = response.json()
        self.assertEqual(response_data['status'], 'success')
        self.assertIn('document_id', response_data)
        self.assertIn('chunks_created', response_data)
        self.assertEqual(response_data['filename'], 'test_document.txt')
        self.assertGreater(response_data['chunks_created'], 0)
    
    def test_unsupported_file_format_error(self):
        """Test file validation error for unsupported format"""
        # Create an unsupported file type (e.g., .jpg)
        jpg_file = SimpleUploadedFile(
            "test_image.jpg",
            b'\xff\xd8\xff\xe0\x00\x10JFIF',
            content_type="image/jpeg"
        )
        
        # Make the request
        response = self.client.post(
            self.upload_url,
            {'file': jpg_file},
            format='multipart'
        )
        
        # Verify error response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error']['code'], 'VALIDATION_ERROR')
        self.assertIn('details', response_data['error'])
    
    def test_missing_file_error(self):
        """Test validation error when file is missing"""
        # Make request without file
        response = self.client.post(
            self.upload_url,
            {},
            format='multipart'
        )
        
        # Verify error response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error']['code'], 'VALIDATION_ERROR')
    
    @patch('api.views.VectorStoreIndex')
    @patch('api.views.get_storage_context')
    @patch('api.views.embed_model')
    def test_response_includes_all_required_fields(self, mock_embed_model, mock_storage_context, mock_vector_index):
        """Test that successful response includes all required fields"""
        # Mock the storage context and vector index
        mock_storage = MagicMock()
        mock_storage_context.return_value = mock_storage
        
        mock_index_instance = MagicMock()
        mock_vector_index.return_value = mock_index_instance
        
        # Create a TXT file upload
        txt_file = SimpleUploadedFile(
            "financial_report.txt",
            self.txt_content,
            content_type="text/plain"
        )
        
        # Make the request
        response = self.client.post(
            self.upload_url,
            {'file': txt_file},
            format='multipart'
        )
        
        # Verify response structure
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_data = response.json()
        
        # Check all required fields are present
        required_fields = ['status', 'document_id', 'chunks_created', 'filename', 'message']
        for field in required_fields:
            self.assertIn(field, response_data, f"Missing required field: {field}")
        
        # Verify field types and values
        self.assertIsInstance(response_data['document_id'], str)
        self.assertIsInstance(response_data['chunks_created'], int)
        self.assertIsInstance(response_data['filename'], str)
        self.assertEqual(response_data['filename'], 'financial_report.txt')
    
    @patch('api.views.get_storage_context')
    def test_opensearch_connection_failure(self, mock_storage_context):
        """Test handling of OpenSearch connection failure"""
        # Mock storage context to raise ConnectionError
        mock_storage_context.side_effect = ConnectionError("Unable to connect to OpenSearch")
        
        # Create a TXT file upload
        txt_file = SimpleUploadedFile(
            "test_document.txt",
            self.txt_content,
            content_type="text/plain"
        )
        
        # Make the request
        response = self.client.post(
            self.upload_url,
            {'file': txt_file},
            format='multipart'
        )
        
        # Verify error response
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error']['code'], 'SERVICE_UNAVAILABLE')
        self.assertIn('vector store', response_data['error']['message'].lower())


class AgentQueryIntegrationTest(TestCase):
    """Integration tests for agent query endpoint"""
    
    def setUp(self):
        """Set up test client and mock data"""
        self.client = APIClient()
        self.query_url = '/api/agent/query/'
        
        # Import CardHolder model and create test user
        from api.models import CardHolder
        self.test_user = CardHolder.objects.create(
            username='testuser',
            phone_number='+1234567890',
            credit_card_number='4111111111111111',
            card_status='active'
        )
    
    @patch('api.views.agent')
    def test_streaming_response_format(self, mock_agent):
        """Test streaming response format with SSE headers and event structure"""
        # Mock streaming response
        mock_streaming_response = MagicMock()
        mock_streaming_response.response_gen = iter([
            "Based", " on", " the", " financial", " report", "..."
        ])
        mock_agent.stream_chat.return_value = mock_streaming_response
        
        # Make request with streaming enabled
        request_data = {
            'message': 'What are the key points in the financial report?',
            'stream': True
        }
        
        response = self.client.post(
            self.query_url,
            request_data,
            format='json'
        )
        
        # Verify response headers
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/event-stream')
        self.assertEqual(response['Cache-Control'], 'no-cache')
        self.assertEqual(response['X-Accel-Buffering'], 'no')
        
        # Verify SSE event format
        response_content = b''.join(response.streaming_content).decode('utf-8')
        
        # Check for token events
        self.assertIn('data: {"type": "token"', response_content)
        self.assertIn('"content": "Based"', response_content)
        self.assertIn('"content": " on"', response_content)
        
        # Check for completion event
        self.assertIn('data: {"type": "done"}', response_content)
        
        # Verify agent was called with correct query
        mock_agent.stream_chat.assert_called_once()
        call_args = mock_agent.stream_chat.call_args[0][0]
        self.assertIn('What are the key points', call_args)
    
    @patch('api.views.agent')
    def test_non_streaming_response_format(self, mock_agent):
        """Test non-streaming response format with JSON structure"""
        # Mock complete response
        mock_response = MagicMock()
        mock_response.__str__ = lambda self: "Based on the financial report, the key points are..."
        
        # Mock source nodes
        mock_source_node = MagicMock()
        mock_source_node.metadata = {
            'filename': 'financial_report.pdf',
            'chunk_index': 2
        }
        mock_source_node.score = 0.95
        mock_response.source_nodes = [mock_source_node]
        
        # Mock sources for tools_used
        mock_source = MagicMock()
        mock_source.tool_name = 'search_documents'
        mock_response.sources = [mock_source]
        
        mock_agent.chat.return_value = mock_response
        
        # Make request with streaming disabled
        request_data = {
            'message': 'What are the key points in the financial report?',
            'stream': False
        }
        
        response = self.client.post(
            self.query_url,
            request_data,
            format='json'
        )
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        response_data = response.json()
        
        # Check required fields
        self.assertEqual(response_data['status'], 'success')
        self.assertIn('response', response_data)
        self.assertIn('sources', response_data)
        self.assertIn('tools_used', response_data)
        self.assertIn('timestamp', response_data)
        
        # Verify response content
        self.assertIn('Based on the financial report', response_data['response'])
        
        # Verify sources structure
        self.assertEqual(len(response_data['sources']), 1)
        self.assertEqual(response_data['sources'][0]['filename'], 'financial_report.pdf')
        self.assertEqual(response_data['sources'][0]['chunk_index'], 2)
        self.assertEqual(response_data['sources'][0]['similarity_score'], 0.95)
        
        # Verify tools_used
        self.assertIn('search_documents', response_data['tools_used'])
        
        # Verify agent was called
        mock_agent.chat.assert_called_once()
    
    @patch('api.views.agent')
    def test_credit_card_blocking_via_agent(self, mock_agent):
        """Test credit card blocking through agent query"""
        # Mock response for credit card blocking
        mock_response = MagicMock()
        mock_response.__str__ = lambda self: (
            f"I have successfully blocked the credit card ending in 1111 "
            f"for user testuser (phone: +1234567890)."
        )
        mock_response.source_nodes = []
        
        # Mock sources for tools_used
        mock_source = MagicMock()
        mock_source.tool_name = 'block_credit_card'
        mock_response.sources = [mock_source]
        
        mock_agent.chat.return_value = mock_response
        
        # Make request to block credit card
        request_data = {
            'message': 'Please block my credit card',
            'phone_number': '+1234567890',
            'stream': False
        }
        
        response = self.client.post(
            self.query_url,
            request_data,
            format='json'
        )
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_data = response.json()
        self.assertEqual(response_data['status'], 'success')
        self.assertIn('blocked', response_data['response'].lower())
        self.assertIn('block_credit_card', response_data['tools_used'])
        
        # Verify agent was called with phone number context
        mock_agent.chat.assert_called_once()
        call_args = mock_agent.chat.call_args[0][0]
        self.assertIn('Please block my credit card', call_args)
        self.assertIn('+1234567890', call_args)
    
    @patch('api.views.agent')
    def test_document_search_via_agent(self, mock_agent):
        """Test document search through agent query"""
        # Mock response for document search
        mock_response = MagicMock()
        mock_response.__str__ = lambda self: (
            "According to the loan schemes document, there are three main types: "
            "agricultural loans, SME loans, and personal loans."
        )
        
        # Mock source nodes
        mock_source_node = MagicMock()
        mock_source_node.metadata = {
            'filename': 'loan_schemes.pdf',
            'chunk_index': 5
        }
        mock_source_node.score = 0.88
        mock_response.source_nodes = [mock_source_node]
        
        # Mock sources for tools_used
        mock_source = MagicMock()
        mock_source.tool_name = 'search_documents'
        mock_response.sources = [mock_source]
        
        mock_agent.chat.return_value = mock_response
        
        # Make request to search documents
        request_data = {
            'message': 'What types of loan schemes are available?',
            'stream': False
        }
        
        response = self.client.post(
            self.query_url,
            request_data,
            format='json'
        )
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_data = response.json()
        self.assertEqual(response_data['status'], 'success')
        self.assertIn('loan schemes', response_data['response'].lower())
        self.assertIn('search_documents', response_data['tools_used'])
        
        # Verify sources were included
        self.assertEqual(len(response_data['sources']), 1)
        self.assertEqual(response_data['sources'][0]['filename'], 'loan_schemes.pdf')
        
        # Verify agent was called
        mock_agent.chat.assert_called_once()
    
    @patch('api.views.agent')
    def test_streaming_with_phone_number_context(self, mock_agent):
        """Test that phone number is included in query context for streaming mode"""
        # Mock streaming response
        mock_streaming_response = MagicMock()
        mock_streaming_response.response_gen = iter(["Your", " card", " is", " blocked"])
        mock_agent.stream_chat.return_value = mock_streaming_response
        
        # Make request with phone number
        request_data = {
            'message': 'Block my card',
            'phone_number': '+1234567890',
            'stream': True
        }
        
        response = self.client.post(
            self.query_url,
            request_data,
            format='json'
        )
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Consume the streaming response to trigger the generator
        response_content = b''.join(response.streaming_content).decode('utf-8')
        
        # Verify agent was called with phone number in context
        mock_agent.stream_chat.assert_called_once()
        call_args = mock_agent.stream_chat.call_args[0][0]
        self.assertIn('Block my card', call_args)
        self.assertIn('+1234567890', call_args)
    
    def test_missing_message_validation_error(self):
        """Test validation error when message is missing"""
        # Make request without message
        request_data = {
            'stream': False
        }
        
        response = self.client.post(
            self.query_url,
            request_data,
            format='json'
        )
        
        # Verify error response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error']['code'], 'VALIDATION_ERROR')
        self.assertIn('message', response_data['error']['details'])
    
    @patch('api.views.agent', None)
    def test_agent_unavailable_streaming_mode(self):
        """Test error handling when agent is unavailable in streaming mode"""
        # Make request when agent is None
        request_data = {
            'message': 'Test query',
            'stream': True
        }
        
        response = self.client.post(
            self.query_url,
            request_data,
            format='json'
        )
        
        # Verify error response
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(response['Content-Type'], 'text/event-stream')
        
        # Verify error event in stream
        response_content = b''.join(response.streaming_content).decode('utf-8')
        self.assertIn('"type": "error"', response_content)
        self.assertIn('SERVICE_UNAVAILABLE', response_content)
    
    @patch('api.views.agent', None)
    def test_agent_unavailable_non_streaming_mode(self):
        """Test error handling when agent is unavailable in non-streaming mode"""
        # Make request when agent is None
        request_data = {
            'message': 'Test query',
            'stream': False
        }
        
        response = self.client.post(
            self.query_url,
            request_data,
            format='json'
        )
        
        # Verify error response
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error']['code'], 'SERVICE_UNAVAILABLE')
        self.assertIn('agent', response_data['error']['message'].lower())
    
    @patch('api.views.agent')
    def test_agent_execution_error_streaming(self, mock_agent):
        """Test error handling when agent execution fails in streaming mode"""
        # Mock agent to raise exception
        mock_agent.stream_chat.side_effect = Exception("Agent processing error")
        
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
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify error event in stream
        response_content = b''.join(response.streaming_content).decode('utf-8')
        self.assertIn('"type": "error"', response_content)
        self.assertIn('AGENT_EXECUTION_ERROR', response_content)
        self.assertIn('Agent processing error', response_content)
    
    @patch('api.views.agent')
    def test_agent_execution_error_non_streaming(self, mock_agent):
        """Test error handling when agent execution fails in non-streaming mode"""
        # Mock agent to raise exception
        mock_agent.chat.side_effect = Exception("Agent processing error")
        
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
        
        # Verify error response
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error']['code'], 'AGENT_EXECUTION_ERROR')
        self.assertIn('Agent processing error', response_data['error']['details'])
