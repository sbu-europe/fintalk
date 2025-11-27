"""
Unit tests for agent tools (search_documents and block_credit_card).

These tests verify the functionality of the LlamaIndex agent tools with
mocked external dependencies (OpenSearch and AWS Bedrock).
"""

from django.test import TestCase
from unittest.mock import Mock, patch, MagicMock
from api.models import CardHolder
from agent.tools import search_documents, block_credit_card
from django.utils import timezone


class SearchDocumentsToolTest(TestCase):
    """Unit tests for the search_documents tool"""
    
    @patch('agent.tools.get_vector_store')
    @patch('agent.tools.VectorStoreIndex')
    def test_search_documents_with_mocked_opensearch_returns_k5_results(self, mock_index_class, mock_get_vector_store):
        """Test search_documents returns top 5 results from OpenSearch"""
        # Mock vector store
        mock_vector_store = Mock()
        mock_get_vector_store.return_value = mock_vector_store
        
        # Mock index and query engine
        mock_index = Mock()
        mock_index_class.from_vector_store.return_value = mock_index
        
        mock_query_engine = Mock()
        mock_index.as_query_engine.return_value = mock_query_engine
        
        # Create mock response with 5 source nodes
        mock_response = Mock()
        mock_response.source_nodes = []
        
        for i in range(5):
            mock_node = Mock()
            mock_node.text = f"Document content {i+1}"
            mock_node.metadata = {'filename': f'document_{i+1}.pdf'}
            mock_node.score = 0.9 - (i * 0.1)  # Decreasing scores
            mock_response.source_nodes.append(mock_node)
        
        mock_query_engine.query.return_value = mock_response
        
        # Execute search
        result = search_documents("test query")
        
        # Verify query engine was called with similarity_top_k=5
        mock_index.as_query_engine.assert_called_once_with(similarity_top_k=5)
        
        # Verify query was executed
        mock_query_engine.query.assert_called_once_with("test query")
        
        # Verify result contains all 5 results
        self.assertIn("[Result 1]", result)
        self.assertIn("[Result 5]", result)
        self.assertIn("Document content 1", result)
        self.assertIn("document_1.pdf", result)
        self.assertIn("Similarity: 0.900", result)
    
    @patch('agent.tools.get_vector_store')
    @patch('agent.tools.VectorStoreIndex')
    def test_search_documents_with_no_results(self, mock_index_class, mock_get_vector_store):
        """Test search_documents when no relevant documents are found"""
        # Mock vector store
        mock_vector_store = Mock()
        mock_get_vector_store.return_value = mock_vector_store
        
        # Mock index and query engine
        mock_index = Mock()
        mock_index_class.from_vector_store.return_value = mock_index
        
        mock_query_engine = Mock()
        mock_index.as_query_engine.return_value = mock_query_engine
        
        # Create mock response with no source nodes
        mock_response = Mock()
        mock_response.source_nodes = []
        
        mock_query_engine.query.return_value = mock_response
        
        # Execute search
        result = search_documents("nonexistent query")
        
        # Verify appropriate message is returned
        self.assertEqual(result, "No relevant documents found for your query.")
    
    @patch('agent.tools.get_vector_store')
    @patch('agent.tools.VectorStoreIndex')
    def test_search_documents_handles_exceptions(self, mock_index_class, mock_get_vector_store):
        """Test search_documents handles exceptions gracefully"""
        # Mock vector store to raise exception
        mock_get_vector_store.side_effect = Exception("OpenSearch connection failed")
        
        # Execute search
        result = search_documents("test query")
        
        # Verify error message is returned
        self.assertIn("Error searching documents", result)
        self.assertIn("OpenSearch connection failed", result)


class BlockCreditCardToolTest(TestCase):
    """Unit tests for the block_credit_card tool"""
    
    def setUp(self):
        """Set up test data"""
        self.cardholder = CardHolder.objects.create(
            username='test_user',
            phone_number='+1234567890',
            credit_card_number='4532015112830366',
            card_status='active'
        )
    
    def test_block_credit_card_success_case(self):
        """Test successfully blocking a credit card with test database"""
        # Execute block operation
        result = block_credit_card('+1234567890')
        
        # Verify success message
        self.assertIn("Successfully blocked credit card", result)
        self.assertIn("+1234567890", result)
        self.assertIn("0366", result)  # Last 4 digits
        self.assertIn("test_user", result)
        self.assertIn("Blocked at:", result)
        
        # Verify database was updated
        self.cardholder.refresh_from_db()
        self.assertEqual(self.cardholder.card_status, 'blocked')
    
    def test_block_credit_card_with_nonexistent_phone_number(self):
        """Test block_credit_card with non-existent phone number"""
        # Execute block operation with non-existent phone
        result = block_credit_card('+9999999999')
        
        # Verify appropriate error message
        self.assertIn("No cardholder found", result)
        self.assertIn("+9999999999", result)
    
    def test_block_credit_card_when_already_blocked(self):
        """Test block_credit_card when card is already blocked"""
        # Block the card first
        self.cardholder.card_status = 'blocked'
        self.cardholder.save()
        
        # Attempt to block again
        result = block_credit_card('+1234567890')
        
        # Verify appropriate message
        self.assertIn("already blocked", result)
        self.assertIn("+1234567890", result)
        self.assertIn("0366", result)  # Last 4 digits
        self.assertIn("test_user", result)
    
    def test_block_credit_card_updates_timestamp(self):
        """Test that blocking a card updates the updated_at timestamp"""
        # Get original timestamp
        original_timestamp = self.cardholder.updated_at
        
        # Wait a moment to ensure timestamp difference
        import time
        time.sleep(0.1)
        
        # Execute block operation
        result = block_credit_card('+1234567890')
        
        # Verify timestamp was updated
        self.cardholder.refresh_from_db()
        self.assertGreater(self.cardholder.updated_at, original_timestamp)
        self.assertEqual(self.cardholder.card_status, 'blocked')
