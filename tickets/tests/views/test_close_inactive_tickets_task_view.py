from unittest.mock import patch

from django.test import TestCase, override_settings
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
        "tickets.views.close_inactive_tickets_task_view._close_inactive_tickets",
        return_value=3,
    )
    def test_get_with_header_token_calls_helper_and_returns_json(self, mock_close):
        response = self.client.get(
            self.url,
            **{"HTTP_X_CRON_TOKEN": "super-secret-token"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"closed": 3})
        mock_close.assert_called_once_with(days=14)

    @override_settings(CRON_TOKEN="super-secret-token")
    @patch(
        "tickets.views.close_inactive_tickets_task_view._close_inactive_tickets",
        return_value=7,
    )
    def test_get_with_query_token_calls_helper_and_returns_json(self, mock_close):
        response = self.client.get(self.url, {"token": "super-secret-token"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"closed": 7})
        mock_close.assert_called_once_with(days=14)

    @override_settings(CRON_TOKEN="super-secret-token")
    @patch(
        "tickets.views.close_inactive_tickets_task_view._close_inactive_tickets",
        return_value=5,
    )
    def test_post_with_header_token_calls_helper_and_returns_json(self, mock_close):
        response = self.client.post(
            self.url,
            **{"HTTP_X_CRON_TOKEN": "super-secret-token"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"closed": 5})
        mock_close.assert_called_once_with(days=14)

    @override_settings(CRON_TOKEN="super-secret-token")
    @patch(
        "tickets.views.close_inactive_tickets_task_view._close_inactive_tickets",
        return_value=9,
    )
    def test_post_with_header_token_calls_helper_and_returns_json(self, mock_close):
        response = self.client.post(
            self.url, **{"HTTP_X_CRON_TOKEN": "super-secret-token"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"closed": 9})
        mock_close.assert_called_once_with(days=14)
