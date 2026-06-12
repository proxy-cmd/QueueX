from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from .models import QueueSettings, Token
from .services import (
    calculate_wait_time,
    call_next_token,
    cancel_token,
    complete_token,
    create_token,
    people_ahead,
    queue_stats,
)


class QueueServiceTests(TestCase):
    def test_create_token_generates_patient_and_token(self):
        token = create_token('Riya Sharma', '9876543210')

        self.assertEqual(token.token_number, 'A001')
        self.assertEqual(token.patient.name, 'Riya Sharma')
        self.assertEqual(token.status, Token.WAITING)

    def test_token_numbers_increment(self):
        first = create_token('Riya Sharma', '9876543210')
        second = create_token('Aman Khan', '9876543211')

        self.assertEqual(first.token_number, 'A001')
        self.assertEqual(second.token_number, 'A002')

    def test_call_next_token_marks_old_serving_completed(self):
        first = create_token('Riya Sharma', '9876543210')
        second = create_token('Aman Khan', '9876543211')

        called_first = call_next_token()
        called_second = call_next_token()
        first.refresh_from_db()

        self.assertEqual(called_first.id, first.id)
        self.assertEqual(called_second.id, second.id)
        self.assertEqual(first.status, Token.COMPLETED)
        self.assertEqual(called_second.status, Token.SERVING)

    def test_wait_time_uses_people_ahead_and_settings(self):
        QueueSettings.objects.create(average_consultation_minutes=10)
        create_token('Riya Sharma', '9876543210')
        create_token('Aman Khan', '9876543211')
        third = create_token('Noor Ali', '9876543212')

        self.assertEqual(people_ahead(third), 2)
        self.assertEqual(calculate_wait_time(third), 20)

    def test_complete_and_cancel_token(self):
        first = create_token('Riya Sharma', '9876543210')
        second = create_token('Aman Khan', '9876543211')

        completed = complete_token(first.id)
        cancelled = cancel_token(second.id)

        self.assertEqual(completed.status, Token.COMPLETED)
        self.assertEqual(cancelled.status, Token.CANCELLED)

    def test_queue_stats(self):
        create_token('Riya Sharma', '9876543210')
        completed = create_token('Aman Khan', '9876543211')
        complete_token(completed.id)

        stats = queue_stats()

        self.assertEqual(stats['total_waiting'], 1)
        self.assertEqual(stats['completed_today'], 1)
        self.assertIsNone(stats['current_serving'])


class ReceptionViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='reception',
            password='strong-test-password',
        )

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('clinic_queue:reception_dashboard'))

        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])

    def test_dashboard_loads_for_receptionist(self):
        self.client.login(username='reception', password='strong-test-password')

        response = self.client.get(reverse('clinic_queue:reception_dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Queue Cure Reception')

    def test_create_patient_token_from_dashboard(self):
        self.client.login(username='reception', password='strong-test-password')

        response = self.client.post(
            reverse('clinic_queue:create_patient_token'),
            {'name': 'Riya Sharma', 'phone': '9876543210'},
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Token.objects.filter(token_number='A001').exists())

    def test_create_patient_token_rejects_bad_phone(self):
        self.client.login(username='reception', password='strong-test-password')

        response = self.client.post(
            reverse('clinic_queue:create_patient_token'),
            {'name': 'Riya Sharma', 'phone': 'bad phone'},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Token.objects.count(), 0)

    def test_call_next_requires_post(self):
        self.client.login(username='reception', password='strong-test-password')

        response = self.client.get(reverse('clinic_queue:call_next'))

        self.assertEqual(response.status_code, 405)

    def test_call_next_from_dashboard(self):
        self.client.login(username='reception', password='strong-test-password')
        token = create_token('Riya Sharma', '9876543210')

        response = self.client.post(reverse('clinic_queue:call_next'))
        token.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(token.status, Token.SERVING)
