from django.db import transaction
from django.utils import timezone
import json

from .models import Patient, QueueSettings, Token, AuditLog


def log_action(action, token=None, user=None, details=None):
    """Log an action to the audit trail."""
    try:
        AuditLog.objects.create(
            action=action,
            token=token,
            user=user,
            details=json.dumps(details or {})
        )
    except Exception as e:
        # Don't fail the main operation if logging fails
        print(f"Failed to log action {action}: {e}")


def next_token_number():
    last_token = Token.objects.order_by('-id').first()
    if not last_token:
        return 'A001'

    last_number = int(last_token.token_number[1:])
    return f"A{last_number + 1:03d}"


@transaction.atomic
def create_token(name, phone, user=None):
    patient = Patient.objects.create(name=name.strip(), phone=phone.strip())
    token = Token.objects.create(
        patient=patient,
        token_number=next_token_number(),
    )
    log_action('create_token', token=token, user=user, details={
        'patient_name': name,
        'patient_phone': phone,
    })
    return token


@transaction.atomic
def call_next_token(user=None):
    current = Token.objects.select_for_update().filter(status=Token.SERVING).first()
    if current:
        current.mark_completed()
        log_action('complete_token', token=current, user=user, details={'auto_complete': True})

    token = (
        Token.objects.select_for_update()
        .filter(status=Token.WAITING)
        .order_by('id')
        .first()
    )
    if not token:
        return None

    token.mark_serving()
    log_action('call_next', token=token, user=user)
    return token


@transaction.atomic
def complete_token(token_id, user=None):
    token = Token.objects.select_for_update().get(id=token_id)
    if token.status != Token.COMPLETED:
        token.mark_completed()
        log_action('complete_token', token=token, user=user)
    return token


@transaction.atomic
def cancel_token(token_id, user=None):
    token = Token.objects.select_for_update().get(id=token_id)
    if token.status in [Token.WAITING, Token.SERVING]:
        token.mark_cancelled()
        log_action('cancel_token', token=token, user=user)
    return token


def current_serving_token():
    return Token.objects.filter(status=Token.SERVING).order_by('served_at', 'id').first()


def waiting_tokens():
    return Token.objects.filter(status=Token.WAITING).order_by('id')


def people_ahead(token):
    if token.status != Token.WAITING:
        return 0

    return Token.objects.filter(
        status=Token.WAITING,
        id__lt=token.id,
    ).count()


def calculate_wait_time(token):
    settings = QueueSettings.load()
    return people_ahead(token) * settings.average_consultation_minutes


def token_wait_details(token):
    return {
        'token': token,
        'people_ahead': people_ahead(token),
        'estimated_wait': calculate_wait_time(token),
    }


def token_payload(token):
    wait_time = calculate_wait_time(token) if token.status == Token.WAITING else 0

    return {
        'id': token.id,
        'token_number': token.token_number,
        'patient_name': token.patient.name,
        'patient_phone': token.patient.phone,
        'status': token.status,
        'status_label': token.get_status_display(),
        'people_ahead': people_ahead(token),
        'estimated_wait': wait_time,
    }


def public_queue_snapshot():
    settings = QueueSettings.load()
    waiting = waiting_tokens().select_related('patient')
    queue_length = waiting.count()
    upcoming = list(waiting[:5])
    current = current_serving_token()

    return {
        'clinic': settings,
        'current_serving': current,
        'upcoming_tokens': upcoming,
        'queue_length': queue_length,
        'estimated_wait': queue_length * settings.average_consultation_minutes,
    }


def queue_payload():
    snapshot = public_queue_snapshot()
    stats = queue_stats()
    tokens = (
        Token.objects.select_related('patient')
        .exclude(status=Token.CANCELLED)
        .order_by('id')[:50]
    )

    return {
        'clinic_name': snapshot['clinic'].clinic_name,
        'current_serving': (
            token_payload(snapshot['current_serving'])
            if snapshot['current_serving']
            else None
        ),
        'upcoming_tokens': [token_payload(token) for token in snapshot['upcoming_tokens']],
        'queue_length': snapshot['queue_length'],
        'estimated_wait': snapshot['estimated_wait'],
        'stats': {
            'total_waiting': stats['total_waiting'],
            'completed_today': stats['completed_today'],
            'current_serving': (
                stats['current_serving'].token_number
                if stats['current_serving']
                else None
            ),
        },
        'tokens': [token_payload(token) for token in tokens],
    }


def queue_stats():
    today = timezone.localdate()

    return {
        'total_waiting': Token.objects.filter(status=Token.WAITING).count(),
        'completed_today': Token.objects.filter(
            status=Token.COMPLETED,
            completed_at__date=today,
        ).count(),
        'current_serving': current_serving_token(),
    }
