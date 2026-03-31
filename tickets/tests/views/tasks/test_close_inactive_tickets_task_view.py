from django.test import TestCase, override_settings
from unittest.mock import patch
from django.urls import reverse


class CloseInactiveTicketsTaskViewTestCase(TestCase):
    """Tests for CloseInactiveTicketsTaskView."""

    def setUp(self):
        self.url = reverse("close_inactive_task")

    def test_get_returns_404_without_token(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_post_returns_404_without_token(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 404)

    @override_settings(CRON_TOKEN="super-secret-token")
    def test_get_returns_404_with_wrong_header_token(self):
        response = self.client.get(self.url, **{"HTTP_X_CRON_TOKEN": "wrong"})
        self.assertEqual(response.status_code, 404)

    @override_settings(CRON_TOKEN="super-secret-token")
    def test_get_returns_404_with_wrong_query_token(self):
        response = self.client.get(self.url, {"token": "wrong"})
        self.assertEqual(response.status_code, 404)

    @override_settings(CRON_TOKEN="super-secret-token")
    @patch(
        "tickets.views.close_inactive_tickets_task_view.send_reminder_emails",
        return_value=2,
    )
    @patch(
        "tickets.views.close_inactive_tickets_task_view.close_inactive_tickets_with_email",
        return_value=3,
    )
    def test_get_with_header_token_returns_json(self, mock_close, mock_reminders):
        response = self.client.get(
            self.url,
            **{"HTTP_X_CRON_TOKEN": "super-secret-token"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"reminders_sent": 2, "closed": 3})
        mock_reminders.assert_called_once_with(days=7)
        mock_close.assert_called_once_with(days=14)

    @override_settings(CRON_TOKEN="super-secret-token")
    @patch(
        "tickets.views.close_inactive_tickets_task_view.send_reminder_emails",
        return_value=4,
    )
    @patch(
        "tickets.views.close_inactive_tickets_task_view.close_inactive_tickets_with_email",
        return_value=7,
    )
    def test_get_with_query_token_returns_json(self, mock_close, mock_reminders):
        response = self.client.get(self.url, {"token": "super-secret-token"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"reminders_sent": 4, "closed": 7})
        mock_reminders.assert_called_once_with(days=7)
        mock_close.assert_called_once_with(days=14)

    @override_settings(CRON_TOKEN="super-secret-token")
    @patch(
        "tickets.views.close_inactive_tickets_task_view.send_reminder_emails",
        return_value=1,
    )
    @patch(
        "tickets.views.close_inactive_tickets_task_view.close_inactive_tickets_with_email",
        return_value=5,
    )
    def test_post_with_header_token_returns_json(self, mock_close, mock_reminders):
        response = self.client.post(
            self.url,
            **{"HTTP_X_CRON_TOKEN": "super-secret-token"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"reminders_sent": 1, "closed": 5})
        mock_reminders.assert_called_once_with(days=7)
        mock_close.assert_called_once_with(days=14)

    @override_settings(CRON_TOKEN="super-secret-token")
    @patch(
        "tickets.views.close_inactive_tickets_task_view.send_reminder_emails",
        return_value=6,
    )
    @patch(
        "tickets.views.close_inactive_tickets_task_view.close_inactive_tickets_with_email",
        return_value=9,
    )
    def test_post_with_query_token_returns_json(self, mock_close, mock_reminders):
        response = self.client.post(f"{self.url}?token=super-secret-token")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"reminders_sent": 6, "closed": 9})
        mock_reminders.assert_called_once_with(days=7)
        mock_close.assert_called_once_with(days=14)
