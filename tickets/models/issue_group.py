from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class IssueGroup(models.Model):
    """Model representing an issue group."""

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 2

            while IssueGroup.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("issue_group_detail", kwargs={"slug": self.slug})

    def __str__(self):
        return self.name
