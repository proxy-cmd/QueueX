from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import PatientForm, QueueSettingsForm
from .models import QueueSettings, Token
from .realtime import broadcast_queue
from .services import (
    call_next_token,
    cancel_token,
    complete_token,
    create_token,
    public_queue_snapshot,
    queue_stats,
    token_wait_details,
)


def _recent_action_blocked(request, key, seconds=2):
    now = timezone.now().timestamp()
    last_seen = request.session.get(key)
    request.session[key] = now
    return last_seen is not None and now - float(last_seen) < seconds


@login_required
def reception_dashboard(request):
    tokens = (
        Token.objects.select_related('patient')
        .exclude(status=Token.CANCELLED)
        .order_by('id')[:50]
    )

    context = {
        'patient_form': PatientForm(),
        'settings_form': QueueSettingsForm(instance=QueueSettings.load()),
        'tokens': tokens,
        'stats': queue_stats(),
    }
    return render(request, 'clinic_queue/reception_dashboard.html', context)


@login_required
@require_POST
def create_patient_token(request):
    if _recent_action_blocked(request, 'last_create_token'):
        messages.warning(request, 'Please wait a moment before generating another token.')
        return redirect('clinic_queue:reception_dashboard')

    form = PatientForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Please fix the patient details and try again.')
        return _dashboard_with_form(request, form)

    try:
        token = create_token(
            name=form.cleaned_data['name'],
            phone=form.cleaned_data['phone'],
        )
    except IntegrityError:
        messages.error(request, 'Token could not be created. Please try again.')
        return redirect('clinic_queue:reception_dashboard')

    broadcast_queue()
    messages.success(request, f'Token {token.token_number} created for {token.patient.name}.')
    return _action_response(request, f'Token {token.token_number} created for {token.patient.name}.')


@login_required
@require_POST
def call_next(request):
    if _recent_action_blocked(request, 'last_call_next'):
        messages.warning(request, 'Please wait a moment before calling the next token.')
        return redirect('clinic_queue:reception_dashboard')

    token = call_next_token()
    if token:
        messages.success(request, f'Now serving {token.token_number}.')
        broadcast_queue()
        return _action_response(request, f'Now serving {token.token_number}.')
    else:
        messages.info(request, 'No waiting patients right now.')

    return _action_response(request, 'No waiting patients right now.')


@login_required
@require_POST
def complete_patient_token(request, token_id):
    token = get_object_or_404(Token, id=token_id)
    complete_token(token.id)
    broadcast_queue()
    messages.success(request, f'Token {token.token_number} completed.')
    return _action_response(request, f'Token {token.token_number} completed.')


@login_required
@require_POST
def cancel_patient_token(request, token_id):
    token = get_object_or_404(Token, id=token_id)
    cancel_token(token.id)
    broadcast_queue()
    messages.success(request, f'Token {token.token_number} cancelled.')
    return _action_response(request, f'Token {token.token_number} cancelled.')


@login_required
def queue_settings(request):
    settings = QueueSettings.load()

    if request.method == 'POST':
        form = QueueSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            broadcast_queue()
            messages.success(request, 'Queue settings updated.')
            return _action_response(request, 'Queue settings updated.')

        messages.error(request, 'Please check the queue settings.')
        return _dashboard_with_form(request, settings_form=form)

    return HttpResponseNotAllowed(['POST'])


def _dashboard_with_form(request, patient_form=None, settings_form=None):
    tokens = (
        Token.objects.select_related('patient')
        .exclude(status=Token.CANCELLED)
        .order_by('id')[:50]
    )

    context = {
        'patient_form': patient_form or PatientForm(),
        'settings_form': settings_form or QueueSettingsForm(instance=QueueSettings.load()),
        'tokens': tokens,
        'stats': queue_stats(),
    }
    return render(request, 'clinic_queue/reception_dashboard.html', context, status=400)


def _action_response(request, message):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        from django.http import JsonResponse

        return JsonResponse({'ok': True, 'message': message})

    return redirect('clinic_queue:reception_dashboard')


def patient_status(request, token_number):
    token = get_object_or_404(
        Token.objects.select_related('patient'),
        token_number=token_number.upper(),
    )

    context = {
        **public_queue_snapshot(),
        **token_wait_details(token),
    }
    return render(request, 'clinic_queue/patient_status.html', context)


def display_board(request):
    return render(request, 'clinic_queue/display_board.html', public_queue_snapshot())
