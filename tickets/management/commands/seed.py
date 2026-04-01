"""Seed the database with fixture users and demo tickets. Duplicate-creation errors are swallowed."""

from django.utils import timezone
from datetime import timedelta
import random
from faker import Faker
from django.core.management.base import BaseCommand
from tickets.models import User, Ticket, Comment, IssueGroup, IssueUpdate
from clarify.settings import TICKET_STAFF_VISIBILITY_DELAY_MINUTES
from tickets.management.commands.user_fixtures import user_fixtures
from tickets.management.commands.realistic_ticket_data import (
    generate_subject_and_body,
    generate_standalone_student_comment,
    generate_comment_and_response_by_category,
    generate_internal_note_by_category,
    generate_issue_group_update,
)


class Command(BaseCommand):
    """Seed the DB with fixture users and Faker-generated users up to 'USER_COUNT'."""

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
    ISSUE_GROUP_UPDATE_COUNT = 50
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
        self.seed_issue_groups()
        self.seed_issue_group_updates()
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
        tickets = Ticket.objects.exclude(status=Ticket.Status.AWAITING_STUDENT)
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
        tickets = Ticket.objects.filter(assigned_to__isnull=False).distinct()

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
                    random_ticket, random_ticket.assigned_to.first(), body=staff_comment
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
        print("Staff comment seeding complete.         ")

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
            user_data = data.copy()  # don't modify the fixture

            if user_data.get("user_type") == User.USER_TYPE_STAFF:
                user_data["faculties"] = ",".join(self.FACULTIES)
                user_data["study_levels"] = ",".join(self.STUDY_LEVELS)
                user_data["categories"] = ",".join(self.CATEGORIES)

            self.try_create_user(user_data)

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
                    t = self.create_random_ticket(
                        random_ticket_type, user, fixture_staff
                    )
                    match random_ticket_type:
                        case "OPEN":
                            if random.random() < 0.5:
                                self.create_comment(
                                    t,
                                    user,
                                    body=generate_standalone_student_comment(
                                        t.category
                                    ),
                                )
                        case "IN_PROGRESS":
                            if random.random() < 0.5:
                                staff_comment, student_comment = (
                                    generate_comment_and_response_by_category(
                                        t.category
                                    )
                                )
                                self.create_comment(
                                    t, t.assigned_to.first(), body=staff_comment
                                )
                                if student_comment:
                                    self.create_comment(t, user, body=student_comment)
                        case "OVERDUE":
                            STUDENT_PLEAS = [
                                "Any updates on this ticket?",
                                "I just wanted to check in on this ticket.",
                                "Is there any update on this ticket?",
                                "I haven't heard back on this ticket in a while, just wanted to check in.",
                                "Could I please get an update on this ticket?",
                            ]
                            if random.random() < 0.5:
                                self.create_comment(
                                    t,
                                    user,
                                    body=random.choice(STUDENT_PLEAS),
                                )
                        case "CLOSED":
                            GENERIC_CLOSING_COMMENTS = [
                                "Please refer to the King's website for more information.",
                                "This ticket has been closed. If you have further questions, please open a new ticket referencing this one.",
                                "Closing this ticket now, but feel free to open a new one if you have any more questions!",
                                "This ticket is now closed. If you have any more questions, please open a new ticket and reference this one.",
                                "Closing this ticket. If you have any more questions, please open a new ticket and reference this one. Thanks!",
                            ]
                            self.create_comment(
                                t,
                                random.choice(fixture_staff),
                                body=random.choice(GENERIC_CLOSING_COMMENTS),
                            )

                except:
                    pass  # Ignore any errors and continue
                created_count += 1
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

        # User type
        if type:
            user_type = type
        else:
            user_type = User.USER_TYPE_STUDENT

        # Student ID
        if user_type == User.USER_TYPE_STUDENT:
            student_id = f"{self.faker.unique.random_int(min=10000000, max=99999999)}"
        else:
            student_id = ""

        # Student phone number
        if user_type == User.USER_TYPE_STUDENT and random.random() < 0.67:
            phone_number = self.faker.numerify(text="07#########")
        else:
            phone_number = ""

        # Student faculty
        if user_type == User.USER_TYPE_STUDENT:
            faculty = random.choice(self.FACULTIES)
        else:
            faculty = ""

        # Student study level
        if user_type == User.USER_TYPE_STUDENT:
            study_level = random.choice(self.STUDY_LEVELS)
        else:
            study_level = ""

        # Student graduation year
        if user_type == User.USER_TYPE_STUDENT:
            graduation_year = self.faker.random_int(min=2026, max=2030)
        else:
            graduation_year = None

        # Determine if user is staff
        if user_type == User.USER_TYPE_STAFF:
            is_staff = True
        else:
            is_staff = False

        # Staff faculties
        if user_type == User.USER_TYPE_STAFF:
            faculties = ",".join(self.FACULTIES)
        else:
            faculties = ""

        # Staff study levels
        if user_type == User.USER_TYPE_STAFF:
            study_levels = ",".join(self.STUDY_LEVELS)
        else:
            study_levels = ""

        # Staff categories
        if user_type == User.USER_TYPE_STAFF:
            categories = ",".join(self.CATEGORIES)
        else:
            categories = ""

        self.try_create_user(
            {
                "username": username,
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "preferred_name": first_name,
                "pronouns": random.choice(["he/him", "she/her", "they/them"]),
                "user_type": user_type,
                "student_id": student_id,
                "phone_number": phone_number,
                "faculty": faculty,
                "study_level": study_level,
                "graduation_year": graduation_year,
                "is_staff": is_staff,
                "faculties": faculties,
                "study_levels": study_levels,
                "categories": categories,
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
            preferred_name=data.get("preferred_name", data["first_name"]),
            pronouns=data.get("pronouns", "Prefer not to say"),
            user_type=data.get("user_type", User.USER_TYPE_STUDENT),
            student_id=data.get("student_id", ""),
            phone_number=data.get("phone_number", ""),
            faculty=data.get("faculty", ""),
            study_level=data.get("study_level", ""),
            graduation_year=data.get("graduation_year"),
            is_staff=data.get("is_staff", False),
            is_superuser=data.get("is_superuser", False),
            faculties=data.get("faculties", ""),
            study_levels=data.get("study_levels", ""),
            categories=data.get("categories", ""),
        )

    def create_random_ticket(self, random_ticket_type, student, staff_qs):
        t = None
        match random_ticket_type:
            case "OPEN":
                t = self.create_ticket(
                    student,
                    status=Ticket.Status.AWAITING_STAFF,
                )
            case "IN_PROGRESS":
                random_staff = random.choice(staff_qs)
                t = self.create_ticket(
                    student,
                    status=Ticket.Status.AWAITING_STAFF,
                    assigned_to=random_staff,
                )
            case "NEED_RESPONSE":
                random_staff = random.choice(staff_qs)
                t = self.create_ticket(
                    student,
                    status=Ticket.Status.AWAITING_STUDENT,
                    assigned_to=random_staff,
                )
                staff_comment, student_comment = (
                    generate_comment_and_response_by_category(t.category)
                )
                self.create_comment(
                    t,
                    random_staff,
                    body=staff_comment,
                )
            case "OVERDUE":
                t = self.create_ticket(
                    student,
                    status=Ticket.Status.AWAITING_STAFF,
                )
                overdue_cutoff = timezone.now() - timedelta(days=5)
                Ticket.objects.filter(pk=t.pk).update(
                    created_at=overdue_cutoff - timedelta(days=1)
                )
            case "CLOSED":
                t = self.create_ticket(
                    student,
                    status=Ticket.Status.CLOSED,
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
        assigned_to = overrides.pop("assigned_to", None)
        data = {
            "student": student,
            "faculty": random_faculty,
            "study_level": random_study_level,
            "category": random_category,
            "subject": generated_subject,
            "body": generated_body,
            "status": Ticket.Status.AWAITING_STAFF,
            "priority": random.choice(self.PRIORITIES),
        }

        if random.random() < 0.2:
            data.update(
                {"internal_notes": generate_internal_note_by_category(random_category)}
            )

        data.update(overrides)
        ticket = Ticket.objects.create(**data)

        if assigned_to is not None:
            if isinstance(assigned_to, (list, tuple)):
                ticket.assigned_to.add(*assigned_to)
            else:
                ticket.assigned_to.add(assigned_to)

        # Make seeded tickets visible immediately for staff/admin users
        Ticket.objects.filter(pk=ticket.pk).update(
            created_at=timezone.now()
            - timedelta(minutes=TICKET_STAFF_VISIBILITY_DELAY_MINUTES)
        )

        return ticket

    def create_comment(self, ticket, author, body):
        data = {
            "ticket": ticket,
            "author": author,
            "body": body,
        }
        return Comment.objects.create(**data)

    def seed_issue_groups(self):
        groups = {}
        for ticket in Ticket.objects.all():
            key = (ticket.faculty, ticket.study_level, ticket.category)
            groups.setdefault(key, []).append(ticket)

        count = 0
        for (faculty, study_level, category), tickets in groups.items():
            if len(tickets) < 2:
                continue
            count += 1
            print(f"Seeding issue group #{count}", end="\r")
            name = f"{faculty.upper()} · {study_level.replace('_',' ').title()} · {category.replace('_',' ').title()}"
            ig = IssueGroup.objects.create(name=name)
            for ticket in tickets:
                ticket.issue_group = ig
            Ticket.objects.bulk_update(tickets, ["issue_group"])
        print(f"Issue group seeding complete. Total:{count}        ")

    def seed_issue_group_updates(self):
        count = 0
        issue_groups = list(IssueGroup.objects.all())
        staff_users = list(User.objects.filter(user_type=User.USER_TYPE_STAFF))
        while count < self.ISSUE_GROUP_UPDATE_COUNT:
            count += 1
            print(
                f"Seeding issue group updates {count}/{self.ISSUE_GROUP_UPDATE_COUNT}",
                end="\r",
            )
            random_ig = random.choice(issue_groups)
            if random_ig.issue_updates.exists():
                continue
            random_staff = random.choice(staff_users)
            IssueUpdate.objects.create(
                issue_group=random_ig,
                message=generate_issue_group_update(),
                created_by=random_staff,
            )
        print("Issue group updates seeding complete.      ")


def create_username(first_name, last_name):
    """Return '@{firstname}{lastname}' (lowercased)."""
    return "@" + first_name.lower() + last_name.lower()


def create_email(first_name, last_name):
    """Return '{firstname}.{lastname}@example.org'."""
    return first_name + "." + last_name + "@example.org"
