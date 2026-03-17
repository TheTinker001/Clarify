from django.test import TestCase
from django.urls import reverse
from tickets.models import IssueGroup


class IssueGroupModelTests(TestCase):
    """Unit tests for the IssueGroup model."""

    def test_generated_slug(self):
        issue = IssueGroup.objects.create(name="Test Issue Group")
        self.assertEqual(issue.slug, "test-issue-group")

    def test_slug_is_unique(self):
        issue1 = IssueGroup.objects.create(name="Test Issue Group")
        issue2 = IssueGroup.objects.create(name="Test Issue Group")

        self.assertEqual(issue1.slug, "test-issue-group")
        self.assertEqual(issue2.slug, "test-issue-group-2")

    def test_get_absolute_url(self):
        issue = IssueGroup.objects.create(name="Test Issue Group")
        expected_url = reverse("issue_group_detail", kwargs={"slug": issue.slug})
        self.assertEqual(issue.get_absolute_url(), expected_url)

    def test_string_representation(self):
        issue = IssueGroup.objects.create(name="Test Issue Group")
        self.assertEqual(str(issue), "Test Issue Group")

    def test_is_archived_default_false(self):
        issue = IssueGroup.objects.create(name="Test Issue Group")
        self.assertFalse(issue.is_archived)

    def test_existing_slug_is_not_regenerated(self):
        issue = IssueGroup.objects.create(
            name="Test Issue Group",
            slug="custom-slug",
        )

        issue.name = "Updated Issue Group"
        issue.save()
        issue.refresh_from_db()

        self.assertEqual(issue.slug, "custom-slug")
