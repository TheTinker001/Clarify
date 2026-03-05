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
from tickets.models import Comment
from django.utils import timezone

from tickets.management.commands.realistic_ticket_data import generate_subject_and_body
from tickets.management.commands.realistic_ticket_data import (
    generate_standalone_student_comment,
)
from tickets.management.commands.realistic_ticket_data import (
    generate_comment_and_response_by_category,
)

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
        "is_superuser": True,
    },
    {
        "username": "@staff002",
        "email": "staff002@example.org",
        "first_name": "Staff",
        "last_name": "002",
        "user_type": "staff",
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

    FACULTIES = [choice for choice, _ in Ticket.Faculty.choices if choice]
    STUDY_LEVELS = [choice for choice, _ in Ticket.StudyLevel.choices if choice]
    CATEGORIES = [choice for choice, _ in Ticket.Category.choices if choice]
    PRIORITIES = [choice for choice, _ in Ticket.Priority.choices if choice]

    STAFF_COUNT = 100
    STUDENT_COUNT = 100
    TICKET_COUNT = 1000
    FIXTURE_TICKET_COUNT = 10
    STAFF_COMMENT_COUNT = 250
    STUDENT_COMMENT_COUNT = 250
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
        self.seed_for_random_users()
        self.seed_for_fixture_users()
        self.users = User.objects.all()

    def seed_for_random_users(self):
        """
        Generate random staff users up to STAFF_COUNT and random student users up to STUDENT_COUNT.
        """
        self.generate_random_users(self.STUDENT_COUNT, User.USER_TYPE_STUDENT)
        self.generate_random_users(self.STAFF_COUNT, User.USER_TYPE_STAFF)
        self.generate_random_tickets_for_random_users()
        self.generate_random_comments_for_random_tickets()

    def generate_random_users(self, count, type):
        """
        Generate random users until the database contains "type"-COUNT users.

        Prints a simple progress indicator to stdout during generation.
        """
        type_count = User.objects.filter(user_type=type).count()
        while type_count < count:
            print(f"Seeding {type} {type_count}/{count}", end="\r")
            self.generate_user(type=type)
            type_count = User.objects.filter(user_type=type).count()
        print(f"{type.capitalize()} seeding complete.      ")

    def generate_random_tickets_for_random_users(self):
        """
        Generate random tickets for existing users until TICKET_COUNT total tickets exist.

        The process is idempotent in spirit: attempts that fail (e.g., due to
        any validation errors) are ignored and generation continues.
        """
        existing_count = Ticket.objects.count()
        student_qs = User.objects.filter(user_type=User.USER_TYPE_STUDENT)
        current_student_count = student_qs.count()
        staff_qs = User.objects.filter(user_type=User.USER_TYPE_STAFF)
        ticket_types = ["OPEN", "IN_PROGRESS", "NEED_RESPONSE", "OVERDUE", "CLOSED"]

        while existing_count < self.TICKET_COUNT:
            print(f"Seeding tickets {existing_count}/{self.TICKET_COUNT}", end="\r")
            try:
                random_index = random.randint(0, current_student_count - 1)
                random_student = student_qs.all()[random_index]

                random_ticket_type = random.choice(ticket_types)
                self.create_random_ticket(random_ticket_type, random_student, staff_qs)

            except:
                pass  # Ignore any errors and continue
            existing_count = Ticket.objects.count()
        print(f"Ticket seeding complete.      ")

    def generate_random_comments_for_random_tickets(self):
        comment_count = Comment.objects.filter(
            author__user_type=User.USER_TYPE_STUDENT
        ).count()
        tickets = Ticket.objects.all()

        while comment_count < self.STUDENT_COMMENT_COUNT:
            print(
                f"Seeding student comments {comment_count}/{self.STUDENT_COMMENT_COUNT}",
                end="\r",
            )
            try:
                random_index = random.randint(0, tickets.count() - 1)
                random_ticket = tickets.all()[random_index]
                self.create_comment(
                    random_ticket,
                    random_ticket.student,
                    body=generate_standalone_student_comment(random_ticket.category),
                )
            except:
                print(
                    f"Seeding student comments {comment_count}/{self.STUDENT_COMMENT_COUNT} failed"
                )
            comment_count = Comment.objects.filter(
                author__user_type=User.USER_TYPE_STUDENT
            ).count()
        print("Student comment seeding complete.      ")

        comment_count = Comment.objects.filter(
            author__user_type=User.USER_TYPE_STAFF
        ).count()
        tickets = Ticket.objects.filter(assigned_to__isnull=False)

        while comment_count < self.STAFF_COMMENT_COUNT:
            print(
                f"Seeding staff comments + reply {comment_count}/{self.STAFF_COMMENT_COUNT}",
                end="\r",
            )
            try:
                random_index = random.randint(0, tickets.count() - 1)
                random_ticket = tickets.all()[random_index]
                staff_comment, student_comment = (
                    generate_comment_and_response_by_category(random_ticket.category)
                )
                self.create_comment(
                    random_ticket, random_ticket.assigned_to, body=staff_comment
                )
                if student_comment:
                    self.create_comment(
                        random_ticket, random_ticket.student, body=student_comment
                    )
            except:
                print(
                    f"Seeding staff comments {comment_count}/{self.STAFF_COMMENT_COUNT} failed"
                )
            comment_count = Comment.objects.filter(
                author__user_type=User.USER_TYPE_STAFF
            ).count()
        print()
        print("Staff comment seeding complete.      ")

    def seed_for_fixture_users(self):
        """
        Create predefined fixture users and generate tickets for them.

        The process is idempotent in spirit: attempts that fail (e.g., due to
        uniqueness constraints on username/email) are ignored and generation continues.
        """
        self.generate_user_fixtures()
        self.create_tickets_for_fixture_users()

    def generate_user_fixtures(self):
        """Attempt to create each predefined fixture user."""
        for data in user_fixtures:
            self.try_create_user(data)

    def create_tickets_for_fixture_users(self):
        fixture_staff = [
            User.objects.get(username="@staff001"),
            User.objects.get(username="@staff002"),
        ]

        for data in user_fixtures:
            try:
                user = User.objects.get(username=data["username"])
            except User.DoesNotExist:
                continue

            # Only seed students
            if user.user_type != User.USER_TYPE_STUDENT:
                continue

            ticket_types = ["OPEN", "IN_PROGRESS", "NEED_RESPONSE", "OVERDUE", "CLOSED"]

            created_count = 0
            while created_count < self.FIXTURE_TICKET_COUNT:
                print(
                    f"Seeding ticket {created_count}/{self.FIXTURE_TICKET_COUNT} for {user.username}",
                    end="\r",
                )
                try:
                    random_ticket_type = random.choice(ticket_types)
                    self.create_random_ticket(random_ticket_type, user, fixture_staff)
                except:
                    pass  # Ignore any errors and continue
                created_count = Ticket.objects.filter(student=user).count()
            print(f"Fixture ticket seeding for {user.username} complete.      ")

    def generate_user(self, type=None):
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
                "user_type": (
                    type
                    if type
                    else random.choice([User.USER_TYPE_STUDENT, User.USER_TYPE_STAFF])
                ),
                "is_staff": (True if type == User.USER_TYPE_STAFF else False),
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

    def create_random_ticket(self, random_ticket_type, student, staff_qs):
        t = None
        match random_ticket_type:
            case "OPEN":
                t = self.create_ticket(
                    student,
                    status=Ticket.Status.AWAITING_STAFF,
                    assigned_to=None,
                )
            case "IN_PROGRESS":
                random_staff = random.choice(staff_qs)
                t = self.create_ticket(
                    student,
                    status=Ticket.Status.AWAITING_STAFF,
                    assigned_to=random_staff,
                )
            case "NEED_RESPONSE":
                t = self.create_ticket(
                    student,
                    status=Ticket.Status.AWAITING_STUDENT,
                    assigned_to=None,
                )
            case "OVERDUE":
                t = self.create_ticket(
                    student,
                    status=Ticket.Status.AWAITING_STAFF,
                    assigned_to=None,
                )
                overdue_cutoff = timezone.now() - timedelta(days=5)
                Ticket.objects.filter(pk=t.pk).update(
                    created_at=overdue_cutoff - timedelta(days=1)
                )
            case "CLOSED":
                t = self.create_ticket(
                    student,
                    status=Ticket.Status.CLOSED,
                    assigned_to=None,
                    closed_reason=Ticket.ClosedReason.ANSWERED,
                    closed_at=timezone.now(),
                )
        return t

    def create_ticket(self, student, **overrides):
        random_faculty = random.choice(self.FACULTIES)
        random_study_level = random.choice(self.STUDY_LEVELS)
        random_category = random.choice(self.CATEGORIES)
        generated_subject, generated_body = generate_subject_and_body(
            faculty=random_faculty,
            study_level=random_study_level,
            category=random_category,
        )
        data = {
            "student": student,
            "faculty": random_faculty,
            "study_level": random_study_level,
            "category": random_category,
            "subject": generated_subject,
            "body": generated_body,
            "status": Ticket.Status.AWAITING_STAFF,
            "assigned_to": None,
            "priority": random.choice(self.PRIORITIES),
        }

        data.update(overrides)
        return Ticket.objects.create(**data)

    def create_comment(self, ticket, author, body):
        data = {
            "ticket": ticket,
            "author": author,
            "body": body,
        }
        return Comment.objects.create(**data)


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
