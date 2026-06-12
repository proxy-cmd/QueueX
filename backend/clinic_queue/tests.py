from django.test import TestCase

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
