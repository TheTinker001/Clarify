"""Seed the database with fixture users and demo tickets. Duplicate-creation errors are swallowed."""

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
    """Seed the DB with fixture users and Faker-generated users up to ``USER_COUNT``."""

    USER_COUNT = 200
    DEFAULT_PASSWORD = "Password123"
    help = "Seeds the database with sample data"

    def __init__(self, *args, **kwargs):
        """Initialize the command with a locale-specific Faker instance."""
        super().__init__(*args, **kwargs)
        self.faker = Faker("en_GB")

    def handle(self, *args, **options):

        self.create_users()
        self.create_tickets_for_fixture_users()
        self.users = User.objects.all()

    def create_users(self):
        self.generate_user_fixtures()
        self.generate_random_users()

    def generate_user_fixtures(self):
        """Attempt to create each predefined fixture user."""
        for data in user_fixtures:
            self.try_create_user(data)

    def generate_random_users(self):
        """Generate Faker users until the DB reaches USER_COUNT, printing progress."""
        user_count = User.objects.count()
        while user_count < self.USER_COUNT:
            print(f"Seeding user {user_count}/{self.USER_COUNT}", end="\r")
            self.generate_user()
            user_count = User.objects.count()
        print("User seeding complete.      ")

    def generate_user(self):
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
        """Attempt to create a user, silently ignoring any errors."""
        try:
            self.create_user(data)
        except:
            pass

    def create_user(self, data):
        """Create a user with the default password."""
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
        """
        Seed up to 20 tickets per fixture student across five states.

        States per student: 7 open, 2 in-progress (assigned to ``@staffuser``),
        2 need-response, 1 overdue (backdated), 2 closed. Students with ≥2
        existing tickets are skipped to keep repeat runs fast.
        """
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

            if user.user_type != User.USER_TYPE_STUDENT:
                continue

            existing = Ticket.objects.filter(student=user).count()
            if existing >= 2:
                continue

            remaining = 20 - existing
            if remaining <= 0:
                continue

            # Allocate the available slots across the five ticket states.
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

            # Any slots not consumed by the other states become additional open tickets.
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

            # IN PROGRESS tickets (assigned to the seed staff user)
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

            # OVERDUE tickets: created normally then backdated via a raw UPDATE
            # because auto_now_add prevents setting created_at through the ORM.
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

            # CLOSED tickets (priority stored but not surfaced in the UI for closed tickets)
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
                    priority=random.choice(PRIORITIES),
                )


def create_username(first_name, last_name):
    """Return ``@{firstname}{lastname}`` (lowercased)."""
    return "@" + first_name.lower() + last_name.lower()


def create_email(first_name, last_name):
    """Return ``{firstname}.{lastname}@example.org``."""
    return first_name + "." + last_name + "@example.org"
