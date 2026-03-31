from django.test import TestCase, override_settings
from unittest.mock import patch
from django.urls import reverse


class CheckInboxTaskViewTestCase(TestCase):
    """Tests for CheckInboxTaskView."""

    def setUp(self):
        self.url = reverse("check_inbox_task")

    @override_settings(CRON_TOKEN="secret-token")
    def test_get_returns_404_without_token(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    @override_settings(CRON_TOKEN="secret-token")
    def test_post_returns_404_without_token(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 404)

    @override_settings(CRON_TOKEN="secret-token")
    def test_get_returns_404_with_wrong_header_token(self):
        response = self.client.get(self.url, HTTP_X_CRON_TOKEN="wrong-token")
        self.assertEqual(response.status_code, 404)

    @override_settings(CRON_TOKEN="secret-token")
    def test_get_returns_404_with_wrong_query_token(self):
        response = self.client.get(self.url, {"token": "wrong-token"})
        self.assertEqual(response.status_code, 404)

    @override_settings(CRON_TOKEN="secret-token")
    @patch("tickets.views.check_inbox_task_view.call_command")
    def test_get_with_valid_header_token_runs_command_and_returns_json(
        self, mock_call_command
    ):
        def fake_call_command(name, stdout=None, **kwargs):
            self.assertEqual(name, "check_inbox")
            self.assertIsNotNone(stdout)
            stdout.write("hello from command")

        mock_call_command.side_effect = fake_call_command

        response = self.client.get(self.url, HTTP_X_CRON_TOKEN="secret-token")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

        data = response.json()
        self.assertEqual(data["ok"], True)
        self.assertEqual(data["output"], "hello from command")

        mock_call_command.assert_called_once()

    @override_settings(CRON_TOKEN="secret-token")
    @patch("tickets.views.check_inbox_task_view.call_command")
    def test_post_with_valid_query_token_runs_command_and_returns_json(
        self, mock_call_command
    ):
        def fake_call_command(name, stdout=None, **kwargs):
            stdout.write("posted")

        mock_call_command.side_effect = fake_call_command

        response = self.client.post(self.url + "?token=secret-token")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["ok"], True)
        self.assertEqual(data["output"], "posted")

        mock_call_command.assert_called_once()
