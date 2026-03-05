from django.core.management.base import BaseCommand
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "clarify.settings")
django.setup()

from django.core.management import call_command


class Command(BaseCommand):
    """Management command to flush all data from the database."""

    help = "Unseeds all data from the database"

    def handle(self, *args, **options):
        """Flush the database and print a confirmation message."""
        call_command("flush", interactive=False)
        print("Database flushed.")
