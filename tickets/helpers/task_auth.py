"""Authorization helper functions."""

import secrets
from django.conf import settings


def authorized(token):
    return bool(token) and secrets.compare_digest(token, settings.CRON_TOKEN)
