from django.core.management.base import BaseCommand, CommandError
from tickets.models import User, Ticket


class Command(BaseCommand):
    """
    Management command to remove (unseed) user data from the database.

    This command deletes all non-staff users from the database. It is designed
    to complement the corresponding "seed" command, allowing developers to
    reset the database to a clean state without removing administrative users.

    Attributes:
        help (str): Short description displayed when running
            `python manage.py help unseed`.
    """

    help = "Seeds the database with sample data"

    def handle(self, *args, **options):
        """
        Execute the unseeding process.

        Deletes all `User` records where `is_staff` is False, preserving
        administrative accounts. Prints a confirmation message upon completion.

        Args:
            *args: Positional arguments passed by Django (not used here).
            **options: Keyword arguments passed by Django (not used here).

        Returns:
            None
        """
        ticket_count = Ticket.objects.count()
        user_count = User.objects.count()

        Ticket.objects.all().delete()
        User.objects.all().delete()

        print(
            f"Unseed complete: deleted {ticket_count} tickets and {user_count} users."
        )
