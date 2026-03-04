"""
Management command to seed the database with demo data.

This command creates a small set of named fixture users and then fills up
to ``USER_COUNT`` total users using Faker-generated data. Existing records
are left untouched—if a create fails (e.g., due to duplicates), the error
is swallowed and generation continues.
"""

from datetime import timedelta
from faker import Faker
import random
from django.core.management.base import BaseCommand, CommandError
from tickets.models import User

from tickets.models import Ticket
from django.utils import timezone


user_fixtures = [
    {
        "username": "@johndoe",
        "email": "john.doe@example.org",
        "first_name": "John",
        "last_name": "Doe",
        "user_type": "student",
    },
    {
        "username": "@janedoe",
        "email": "jane.doe@example.org",
        "first_name": "Jane",
        "last_name": "Doe",
        "user_type": "student",
    },
    {
        "username": "@charlie",
        "email": "charlie.johnson@example.org",
        "first_name": "Charlie",
        "last_name": "Johnson",
        "user_type": "student",
    },
    {
        "username": "@student001",
        "email": "student001@example.org",
        "first_name": "Student",
        "last_name": "001",
        "user_type": "student",
    },
    {
        "username": "@staff001",
        "email": "staff001@example.org",
        "first_name": "Staff",
        "last_name": "001",
        "user_type": "staff",
        "is_staff": True,
        "is_superuser": True,
    },
    {
        "username": "@staff002",
        "email": "staff002@example.org",
        "first_name": "Staff",
        "last_name": "002",
        "user_type": "staff",
        "is_staff": True,
        "is_superuser": True,
    },
]


class Command(BaseCommand):
    """
    Build automation command to seed the database with data.

    This command inserts a small set of known users (``user_fixtures``) and then
    repeatedly generates additional random users until ``USER_COUNT`` total users
    exist in the database. Each generated user receives the same default password.

    Attributes:
        USER_COUNT (int): Target total number of users in the database.
        DEFAULT_PASSWORD (str): Default password assigned to all created users.
        help (str): Short description shown in ``manage.py help``.
        faker (Faker): Locale-specific Faker instance used for random data.
    """

    USER_COUNT = 200
    DEFAULT_PASSWORD = "Password123"
    help = "Seeds the database with sample data"

    def __init__(self, *args, **kwargs):
        """Initialize the command with a locale-specific Faker instance."""
        super().__init__(*args, **kwargs)
        self.faker = Faker("en_GB")

    def handle(self, *args, **options):
        """
        Django entrypoint for the command.

        Runs the full seeding workflow and stores ``self.users`` for any
        post-processing or debugging (not required for operation).
        """
        self.create_users()
        self.create_tickets_for_fixture_users()
        self.users = User.objects.all()

    def create_users(self):
        """
        Create fixture users and then generate random users up to USER_COUNT.

        The process is idempotent in spirit: attempts that fail (e.g., due to
        uniqueness constraints on username/email) are ignored and generation continues.
        """
        self.generate_user_fixtures()
        self.generate_random_users()

    def generate_user_fixtures(self):
        """Attempt to create each predefined fixture user."""
        for data in user_fixtures:
            self.try_create_user(data)

    def generate_random_users(self):
        """
        Generate random users until the database contains USER_COUNT users.

        Prints a simple progress indicator to stdout during generation.
        """
        user_count = User.objects.count()
        while user_count < self.USER_COUNT:
            print(f"Seeding user {user_count}/{self.USER_COUNT}", end="\r")
            self.generate_user()
            user_count = User.objects.count()
        print("User seeding complete.      ")

    def generate_user(self):
        """
        Generate a single random user and attempt to insert it.

        Uses Faker for first/last names, then derives a simple username/email.
        """
        first_name = self.faker.first_name()
        last_name = self.faker.last_name()
        email = create_email(first_name, last_name)
        username = create_username(first_name, last_name)
        self.try_create_user(
            {
                "username": username,
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
            }
        )

    def try_create_user(self, data):
        """
        Attempt to create a user and ignore any errors.

        Args:
            data (dict): Mapping with keys ``username``, ``email``,
                ``first_name``, and ``last_name``.
        """
        try:
            self.create_user(data)
        except:
            pass

    def create_user(self, data):
        """
        Create a user with the default password.

        Args:
            data (dict): Mapping with keys ``username``, ``email``,
                ``first_name``, and ``last_name``.
        """
        User.objects.create_user(
            username=data["username"],
            email=data["email"],
            password=Command.DEFAULT_PASSWORD,
            first_name=data["first_name"],
            last_name=data["last_name"],
            user_type=data.get("user_type", User.USER_TYPE_STUDENT),
            is_staff=data.get("is_staff", False),
            is_superuser=data.get("is_superuser", False),
        )

    def create_tickets_for_fixture_users(self):

        FACULTIES = [choice for choice, _ in Ticket.Faculty.choices if choice]
        STUDY_LEVELS = [choice for choice, _ in Ticket.StudyLevel.choices if choice]
        CATEGORIES = [choice for choice, _ in Ticket.Category.choices if choice]
        PRIORITIES = [choice for choice, _ in Ticket.Priority.choices if choice]

        staff_user = User.objects.create_user(
            first_name="Staff",
            last_name="User",
            username="@staffuser",
            email="staffuser@example.org",
            user_type=User.USER_TYPE_STAFF,
            is_staff=True,
            is_superuser=True,
            password="Password123",
        )
        overdue_cutoff = timezone.now() - timedelta(days=5)

        for data in user_fixtures:
            try:
                user = User.objects.get(username=data["username"])
            except User.DoesNotExist:
                continue

            # Only seed students
            if user.user_type != User.USER_TYPE_STUDENT:
                continue

            existing = Ticket.objects.filter(student=user).count()
            if existing >= 2:
                continue

            remaining = 20 - existing
            if remaining <= 0:
                continue

            # Define mix (adjust numbers if you want)
            open_count = min(7, remaining)
            remaining -= open_count

            in_progress_count = min(2, remaining) if staff_user else 0
            remaining -= in_progress_count

            need_response_count = min(2, remaining)
            remaining -= need_response_count

            overdue_count = min(1, remaining)
            remaining -= overdue_count

            closed_count = min(2, remaining)
            remaining -= closed_count

            # Anything left -> open tickets
            open_count += remaining

            # OPEN tickets
            for _ in range(open_count):
                Ticket.objects.create(
                    student=user,
                    faculty=random.choice(FACULTIES),
                    study_level=random.choice(STUDY_LEVELS),
                    category=random.choice(CATEGORIES),
                    subject=self.faker.sentence(nb_words=6),
                    body=self.faker.paragraph(nb_sentences=random.randint(3, 8)),
                    status=Ticket.Status.AWAITING_STAFF,
                    assigned_to=None,
                    priority=random.choice(PRIORITIES),
                )

            # IN PROGRESS tickets
            for _ in range(in_progress_count):
                Ticket.objects.create(
                    student=user,
                    faculty=random.choice(FACULTIES),
                    study_level=random.choice(STUDY_LEVELS),
                    category=random.choice(CATEGORIES),
                    subject=self.faker.sentence(nb_words=6),
                    body=self.faker.paragraph(nb_sentences=random.randint(3, 8)),
                    status=Ticket.Status.AWAITING_STAFF,
                    assigned_to=staff_user,
                    priority=random.choice(PRIORITIES),
                )

            # NEED RESPONSE tickets
            for _ in range(need_response_count):
                Ticket.objects.create(
                    student=user,
                    faculty=random.choice(FACULTIES),
                    study_level=random.choice(STUDY_LEVELS),
                    category=random.choice(CATEGORIES),
                    subject=self.faker.sentence(nb_words=6),
                    body=self.faker.paragraph(nb_sentences=random.randint(3, 8)),
                    status=Ticket.Status.AWAITING_STUDENT,
                    assigned_to=None,
                    priority=random.choice(PRIORITIES),
                )

            # OVERDUE tickets
            for _ in range(overdue_count):
                t = Ticket.objects.create(
                    student=user,
                    faculty=random.choice(FACULTIES),
                    study_level=random.choice(STUDY_LEVELS),
                    category=random.choice(CATEGORIES),
                    subject=self.faker.sentence(nb_words=6),
                    body=self.faker.paragraph(nb_sentences=random.randint(3, 8)),
                    status=Ticket.Status.AWAITING_STAFF,
                    assigned_to=None,
                    priority=random.choice(PRIORITIES),
                )
                Ticket.objects.filter(pk=t.pk).update(
                    created_at=overdue_cutoff - timedelta(days=1)
                )

            # CLOSED tickets
            for _ in range(closed_count):
                Ticket.objects.create(
                    student=user,
                    faculty=random.choice(FACULTIES),
                    study_level=random.choice(STUDY_LEVELS),
                    category=random.choice(CATEGORIES),
                    subject=self.faker.sentence(nb_words=6),
                    body=self.faker.paragraph(nb_sentences=random.randint(3, 8)),
                    status=Ticket.Status.CLOSED,
                    closed_reason=Ticket.ClosedReason.ANSWERED,
                    closed_at=timezone.now(),
                    priority=random.choice(
                        PRIORITIES
                    ),  # shouldnt be displayed even if it has a value
                )


def create_username(first_name, last_name):
    """
    Construct a simple username from first and last names.

    Args:
        first_name (str): Given name.
        last_name (str): Family name.

    Returns:
        str: A username in the form ``@{firstname}{lastname}`` (lowercased).
    """
    return "@" + first_name.lower() + last_name.lower()


def create_email(first_name, last_name):
    """
    Construct a simple example email address.

    Args:
        first_name (str): Given name.
        last_name (str): Family name.

    Returns:
        str: An email in the form ``{firstname}.{lastname}@example.org``.
    """
    return first_name + "." + last_name + "@example.org"
