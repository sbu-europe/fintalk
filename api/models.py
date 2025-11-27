from django.db import models


class CardHolder(models.Model):
    """
    CardHolder model storing cardholder information and credit card details.
    """
    CARD_STATUS_CHOICES = [
        ('active', 'Active'),
        ('blocked', 'Blocked'),
    ]
    
    username = models.CharField(max_length=100, unique=True)
    phone_number = models.CharField(max_length=20, unique=True)
    credit_card_number = models.CharField(max_length=19)
    card_status = models.CharField(
        max_length=10,
        choices=CARD_STATUS_CHOICES,
        default='active'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'cardholders'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.username} ({self.phone_number})"
