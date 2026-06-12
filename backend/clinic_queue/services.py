from django.db import transaction
from django.utils import timezone

from .models import Patient, QueueSettings, Token


def next_token_number():
    last_token = Token.objects.order_by('-id').first()
    if not last_token:
        return 'A001'

    last_number = int(last_token.token_number[1:])
    return f"A{last_number + 1:03d}"


@transaction.atomic
def create_token(name, phone):
    patient = Patient.objects.create(name=name.strip(), phone=phone.strip())
    token = Token.objects.create(
        patient=patient,
        token_number=next_token_number(),
    )
    return token


@transaction.atomic
def call_next_token():
    current = Token.objects.select_for_update().filter(status=Token.SERVING).first()
    if current:
        current.mark_completed()

    token = (
        Token.objects.select_for_update()
        .filter(status=Token.WAITING)
        .order_by('created_at')
        .first()
    )
    if not token:
        return None

    token.mark_serving()
    return token


@transaction.atomic
def complete_token(token_id):
    token = Token.objects.select_for_update().get(id=token_id)
    if token.status != Token.COMPLETED:
        token.mark_completed()
    return token


@transaction.atomic
def cancel_token(token_id):
    token = Token.objects.select_for_update().get(id=token_id)
    if token.status in [Token.WAITING, Token.SERVING]:
        token.mark_cancelled()
    return token


def current_serving_token():
    return Token.objects.filter(status=Token.SERVING).order_by('served_at').first()


def waiting_tokens():
    return Token.objects.filter(status=Token.WAITING).order_by('created_at')


def people_ahead(token):
    if token.status != Token.WAITING:
        return 0

    return Token.objects.filter(
        status=Token.WAITING,
        created_at__lt=token.created_at,
    ).count()


def calculate_wait_time(token):
    settings = QueueSettings.load()
    return people_ahead(token) * settings.average_consultation_minutes


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
