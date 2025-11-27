"""
Management command to populate the database with dummy cardholder data.
"""
from django.core.management.base import BaseCommand
from api.models import CardHolder


class Command(BaseCommand):
    help = 'Populates the database with 10 dummy cardholders for testing'

    def handle(self, *args, **options):
        # Clear existing cardholders
        CardHolder.objects.all().delete()
        self.stdout.write(self.style.WARNING('Cleared existing cardholders'))

        # Create 10 dummy cardholders
        dummy_users = [
            {
                'username': 'john_doe',
                'phone_number': '+1234567890',
                'credit_card_number': '4532-1234-5678-9010',
                'card_status': 'active'
            },
            {
                'username': 'jane_smith',
                'phone_number': '+1234567891',
                'credit_card_number': '5425-2345-6789-0123',
                'card_status': 'active'
            },
            {
                'username': 'bob_johnson',
                'phone_number': '+1234567892',
                'credit_card_number': '3782-3456-7890-1234',
                'card_status': 'blocked'
            },
            {
                'username': 'alice_williams',
                'phone_number': '+1234567893',
                'credit_card_number': '6011-4567-8901-2345',
                'card_status': 'active'
            },
            {
                'username': 'charlie_brown',
                'phone_number': '+1234567894',
                'credit_card_number': '4916-5678-9012-3456',
                'card_status': 'active'
            },
            {
                'username': 'diana_prince',
                'phone_number': '+1234567895',
                'credit_card_number': '5234-6789-0123-4567',
                'card_status': 'active'
            },
            {
                'username': 'edward_norton',
                'phone_number': '+1234567896',
                'credit_card_number': '3714-7890-1234-5678',
                'card_status': 'blocked'
            },
            {
                'username': 'fiona_gallagher',
                'phone_number': '+1234567897',
                'credit_card_number': '6011-8901-2345-6789',
                'card_status': 'active'
            },
            {
                'username': 'george_martin',
                'phone_number': '+1234567898',
                'credit_card_number': '4539-9012-3456-7890',
                'card_status': 'active'
            },
            {
                'username': 'hannah_montana',
                'phone_number': '+1234567899',
                'credit_card_number': '5412-0123-4567-8901',
                'card_status': 'active'
            },
        ]

        created_count = 0
        for user_data in dummy_users:
            cardholder = CardHolder.objects.create(**user_data)
            created_count += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f'Created cardholder: {cardholder.username} ({cardholder.phone_number}) - {cardholder.card_status}'
                )
            )

        self.stdout.write(
            self.style.SUCCESS(f'\nSuccessfully created {created_count} dummy cardholders')
        )
