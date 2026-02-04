"""Tests for the dashboard view."""
from django.test import TestCase
from django.urls import reverse
from tickets.models import Ticket, User
from tickets.tests.helpers import MenuTesterMixin, reverse_with_next


class DashboardViewTestCase(TestCase, MenuTesterMixin):
    """Test suite for the dashboard view."""

    fixtures = ['tickets/tests/fixtures/default_user.json']

    def setUp(self):
        self.user = User.objects.get(username='@johndoe')
        self.url = reverse('dashboard')

    def test_dashboard_url(self):
        self.assertEqual(self.url, '/dashboard/')

    def test_get_dashboard_redirects_when_not_logged_in(self):
        redirect_url = reverse_with_next('log_in', self.url)
        response = self.client.get(self.url)
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)

    def test_get_dashboard_renders_tickets(self):
        ticket = Ticket.objects.create(
            title='Broken login',
            description='Cannot log in.',
            story_points=2,
            created_by=self.user,
        )
        self.client.login(username=self.user.username, password='Password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard.html')
        self.assertContains(response, ticket.title)
        ticket_url = reverse('ticket_detail', kwargs={'pk': ticket.pk})
        with self.assertHTML(response, f'a[href=\"{ticket_url}\"]'):
            pass
        self.assert_menu(response)
