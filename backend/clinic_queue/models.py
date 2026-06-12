from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


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
        self.status = self.SERVING
        self.served_at = timezone.now()
        self.save(update_fields=['status', 'served_at'])

    def mark_completed(self):
        self.status = self.COMPLETED
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at'])

    def mark_cancelled(self):
        self.status = self.CANCELLED
        self.save(update_fields=['status'])


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

# Create your models here.
