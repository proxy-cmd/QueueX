from django.contrib import admin

from .models import Patient, QueueSettings, Token


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'created_at')
    search_fields = ('name', 'phone')
    ordering = ('-created_at',)


@admin.register(Token)
class TokenAdmin(admin.ModelAdmin):
    list_display = ('token_number', 'patient', 'status', 'created_at', 'served_at', 'completed_at')
    list_filter = ('status', 'created_at')
    search_fields = ('token_number', 'patient__name', 'patient__phone')
    ordering = ('-created_at',)


@admin.register(QueueSettings)
class QueueSettingsAdmin(admin.ModelAdmin):
    list_display = ('clinic_name', 'average_consultation_minutes')

# Register your models here.
