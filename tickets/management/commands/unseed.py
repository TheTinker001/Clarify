from django.core.management.base import BaseCommand
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
        """Flush the database and print a confirmation message."""
        call_command("flush", interactive=False)
        print("Database flushed.")
