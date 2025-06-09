from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    email = models.EmailField(unique=True, db_index=True)
    is_premium = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['is_premium'],
                         name='premium_customer_idx',
                         condition=Q(is_premium=True))
        ]

class TicketCategory(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        indexes = [
            models.Index(fields=['name'])
        ]

class Ticket(models.Model):
    STATUS_CHOICES = [('O', 'Open'), ('P', 'In Progress'), ('C', 'Closed')]
    PRIORITY_CHOICES = [('H', 'High'), ('M', 'Medium'), ('L', 'Low')]

    id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, db_index=True)
    subject = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='O')
    priority = models.CharField(max_length=1, choices=PRIORITY_CHOICES)
    category = models.ForeignKey(TicketCategory, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sentiment_score = models.FloatField(null=True)

    class Meta:
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['created_at']),
            # Use regular B-tree indexes instead of GIN
            models.Index(fields=['subject']),
            models.Index(fields=['status'],
                         condition=Q(status='O'),
                         name='open_tickets_idx')
        ]

class KnowledgeBase(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200)
    content = models.TextField()
    embedding = models.JSONField()
    categories = models.ManyToManyField(TicketCategory)

    class Meta:
        indexes = [
            # Use regular B-tree indexes
            models.Index(fields=['title'])
        ]