from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class Patient(models.Model):
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.phone})"


class Token(models.Model):
    WAITING = 'waiting'
    SERVING = 'serving'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (WAITING, 'Waiting'),
        (SERVING, 'Serving'),
        (COMPLETED, 'Completed'),
        (CANCELLED, 'Cancelled'),
    ]

    token_number = models.CharField(max_length=4, unique=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='tokens')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=WAITING)
    created_at = models.DateTimeField(auto_now_add=True)
    served_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['token_number']),
        ]

    def __str__(self):
        return self.token_number

    def mark_serving(self):
        """Transition token to SERVING status. Only valid from WAITING."""
        if self.status != self.WAITING:
            raise ValueError(f"Cannot mark token as serving when status is {self.status}")
        self.status = self.SERVING
        self.served_at = timezone.now()
        self.save(update_fields=['status', 'served_at'])

    def mark_completed(self):
        """Transition token to COMPLETED status. Valid from WAITING or SERVING."""
        if self.status not in [self.WAITING, self.SERVING]:
            raise ValueError(f"Cannot complete token when status is {self.status}")
        self.status = self.COMPLETED
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at'])

    def mark_cancelled(self):
        """Transition token to CANCELLED. Only valid from WAITING or SERVING."""
        if self.status not in [self.WAITING, self.SERVING]:
            raise ValueError(f"Cannot cancel token when status is {self.status}")
        self.status = self.CANCELLED
        self.save(update_fields=['status'])
    
    @property
    def can_be_completed(self):
        """Check if token can be marked as completed."""
        return self.status in [self.WAITING, self.SERVING]
    
    @property
    def can_be_cancelled(self):
        """Check if token can be cancelled."""
        return self.status in [self.WAITING, self.SERVING]


class QueueSettings(models.Model):
    clinic_name = models.CharField(max_length=120, default="Queue Cure Clinic")
    average_consultation_minutes = models.PositiveIntegerField(
        default=8,
        validators=[MinValueValidator(1)],
    )

    class Meta:
        verbose_name_plural = 'Queue settings'

    def __str__(self):
        return self.clinic_name

    @classmethod
    def load(cls):
        settings, _created = cls.objects.get_or_create(pk=1)
        return settings


class AuditLog(models.Model):
    """Track all queue actions for audit trail and debugging."""
    ACTION_CHOICES = [
        ('create_token', 'Create Token'),
        ('call_next', 'Call Next'),
        ('complete_token', 'Complete Token'),
        ('cancel_token', 'Cancel Token'),
        ('update_settings', 'Update Settings'),
        ('archive_tokens', 'Archive Tokens'),
    ]
    
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    token = models.ForeignKey(Token, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    details = models.TextField(blank=True, help_text="JSON details of the action")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['action', '-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.action} by {self.user} at {self.created_at}"
