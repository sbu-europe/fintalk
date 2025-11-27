"""
Unit tests for CardHolder model.

These tests verify the functionality of the CardHolder model including
field validation, uniqueness constraints, and status transitions.
"""

from django.test import TestCase
from django.db import IntegrityError
from api.models import CardHolder


class CardHolderModelTest(TestCase):
    """Unit tests for CardHolder model"""
    
    def setUp(self):
        """Set up test data"""
        self.valid_cardholder_data = {
            'username': 'john_doe',
            'phone_number': '+1234567890',
            'credit_card_number': '4532015112830366',
            'card_status': 'active'
        }
    
    def test_cardholder_creation_with_all_required_fields(self):
        """Test creating a cardholder with all required fields"""
        cardholder = CardHolder.objects.create(**self.valid_cardholder_data)
        
        self.assertEqual(cardholder.username, 'john_doe')
        self.assertEqual(cardholder.phone_number, '+1234567890')
        self.assertEqual(cardholder.credit_card_number, '4532015112830366')
        self.assertEqual(cardholder.card_status, 'active')
        self.assertIsNotNone(cardholder.created_at)
        self.assertIsNotNone(cardholder.updated_at)
    
    def test_phone_number_uniqueness_constraint(self):
        """Test that phone numbers must be unique"""
        CardHolder.objects.create(**self.valid_cardholder_data)
        
        # Attempt to create another cardholder with the same phone number
        duplicate_data = self.valid_cardholder_data.copy()
        duplicate_data['username'] = 'jane_doe'
        
        with self.assertRaises(IntegrityError):
            CardHolder.objects.create(**duplicate_data)
    
    def test_card_status_transition_from_active_to_blocked(self):
        """Test transitioning card status from active to blocked"""
        cardholder = CardHolder.objects.create(**self.valid_cardholder_data)
        
        # Verify initial status
        self.assertEqual(cardholder.card_status, 'active')
        
        # Update status to blocked
        cardholder.card_status = 'blocked'
        cardholder.save()
        
        # Refresh from database and verify
        cardholder.refresh_from_db()
        self.assertEqual(cardholder.card_status, 'blocked')
    
    def test_username_uniqueness_constraint(self):
        """Test that usernames must be unique"""
        CardHolder.objects.create(**self.valid_cardholder_data)
        
        # Attempt to create another cardholder with the same username
        duplicate_data = self.valid_cardholder_data.copy()
        duplicate_data['phone_number'] = '+9876543210'
        
        with self.assertRaises(IntegrityError):
            CardHolder.objects.create(**duplicate_data)
