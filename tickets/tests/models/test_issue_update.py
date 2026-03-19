"""Tests for the issue update model."""

from django.core.exceptions import ValidationError
from django.test import TestCase
from tickets.models import IssueUpdate, IssueGroup, Ticket, User
from clarify.settings import BODY_LENGTH_MAX


class IssueUpdateModelTestCase(TestCase):
    """Test suite for the issue update model."""

    fixtures = [
        "tickets/tests/fixtures/default_user.json",
        "tickets/tests/fixtures/other_users.json",
    ]

    def setUp(self):
        self.issue_group = IssueGroup.objects.create(
            name="Wi-Fi outage",
            slug="wi-fi-outage",
        )
        self.staff_user = User.objects.create_user(
            username="staff",
            password="testpass123",
            user_type=User.USER_TYPE_STAFF,
        )

    def test_can_create_issue_update(self):
        update = IssueUpdate.objects.create(
            issue=self.issue_group,
            message="We are investigating the issue.",
            created_by=self.staff_user,
        )

        self.assertEqual(update.issue, self.issue_group)
        self.assertEqual(update.message, "We are investigating the issue.")
        self.assertEqual(update.created_by, self.staff_user)
        self.assertIsNotNone(update.created_at)

    def test_issue_update_ordering(self):
        older = IssueUpdate.objects.create(
            issue=self.issue_group,
            message="Older update",
            created_by=self.staff_user,
        )
        newer = IssueUpdate.objects.create(
            issue=self.issue_group,
            message="Newer update",
            created_by=self.staff_user,
        )

        updates = list(IssueUpdate.objects.all())

        self.assertEqual(updates[0].pk, newer.pk)
        self.assertEqual(updates[1].pk, older.pk)

    def test_comment_body_too_long(self):
        long_body = "a" * (BODY_LENGTH_MAX + 1)
        update = IssueUpdate.objects.create(
            issue=self.issue_group,
            message=long_body,
            created_by=self.staff_user,
        )
        with self.assertRaises(ValidationError):
            update.full_clean()

    def test_comment_body_at_max_length(self):
        body = "a" * BODY_LENGTH_MAX
        update = IssueUpdate.objects.create(
            issue=self.issue_group,
            message=body,
            created_by=self.staff_user,
        )
        update.full_clean()

    def test_clean_rejects_student_as_creator(self):
        student_user = User.objects.create_user(
            username="student",
            password="testpass123",
            user_type=User.USER_TYPE_STUDENT,
            email="test@gmail.com",
        )
        update = IssueUpdate.objects.create(
            issue=self.issue_group,
            message="test",
            created_by=student_user,
        )
        with self.assertRaises(ValidationError):
            update.full_clean()

    def test_clean_accepts_staff_as_creator(self):
        staff_user = User.objects.create_user(
            username="staff2",
            password="testpass123",
            user_type=User.USER_TYPE_STAFF,
            email="test@gmail.com",
        )
        update = IssueUpdate.objects.create(
            issue=self.issue_group,
            message="test",
            created_by=staff_user,
        )
        update.full_clean()
