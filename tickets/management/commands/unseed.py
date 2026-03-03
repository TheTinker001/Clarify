from django.core.management.base import BaseCommand
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "clarify.settings")
django.setup()

from django.core.management import call_command


class Command(BaseCommand):
    """
    Management command to remove (unseed) all data from the database.

    Attributes:
        help (str): Short description displayed when running
            `python manage.py help unseed`.
    """

    help = "Unseeds all data from the database"

    def handle(self, *args, **options):
        """
        Execute the unseeding process.

        Deletes all data from the database.
        Prints a confirmation message upon completion.
        """
        call_command("flush", interactive=False)
        print("Database flushed.")
