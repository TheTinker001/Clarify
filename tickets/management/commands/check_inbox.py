"""Management command to check the monitored email inbox and create tickets."""

import imaplib
import email
from email.header import decode_header

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand

from tickets.email_classifier import classify_email
from tickets.models import Ticket, User


def _decode_header_value(value):
    """Decode an email header into a plain string."""
    if value is None:
        return ""
    decoded_parts = decode_header(value)
    result = []
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            result.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            result.append(part)
    return "".join(result)


def _extract_body(msg):
    """Extract plain text body from an email message."""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))
            if content_type == "text/plain" and "attachment" not in content_disposition:
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    return payload.decode(charset, errors="replace")
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            return payload.decode(charset, errors="replace")
    return ""


def _extract_sender_email(msg):
    """Extract the sender's email address from the From header."""
    from_header = msg.get("From", "")
    if "<" in from_header and ">" in from_header:
        return from_header.split("<")[1].split(">")[0].strip().lower()
    return from_header.strip().lower()


def _send_missing_fields_reply(student_email, subject, missing_fields):
    """Send reply asking student to resend with missing fields."""
    fields_list = ", ".join(missing_fields)
    body = (
        "Dear Student,\n\n"
        "Thank you for your email. We were unable to automatically determine "
        "the following information from your message:\n\n"
        f"  Missing: {fields_list}\n\n"
        "Please reply to this email and include the following details so we "
        "can process your query:\n\n"
        "- Faculty (e.g. King's Business School, Engineering, Law, etc.)\n"
        "- Study Level (e.g. Undergraduate, Postgraduate Taught, PhD)\n"
        "- Category (e.g. Assessment, Health, Careers, Accommodation, etc.)\n\n"
        "Kind regards,\n"
        "Clarify Support Team"
    )
    send_mail(
        subject=f"Re: {subject} - Additional Information Required",
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER,
        recipient_list=[student_email],
        fail_silently=False,
    )


def process_email(msg):
    """
    Process a single email message.

    Returns a tuple of (action, detail) where action is one of:
    'created', 'missing_fields', 'ignored_not_student', 'ignored_no_subject'.
    """
    sender_email = _extract_sender_email(msg)
    subject = _decode_header_value(msg.get("Subject"))
    body = _extract_body(msg)

    try:
        student = User.objects.get(
            email__iexact=sender_email,
            user_type=User.USER_TYPE_STUDENT,
        )
    except User.DoesNotExist:
        return ("ignored_not_student", sender_email)

    if not subject.strip():
        return ("ignored_no_subject", sender_email)

    classification = classify_email(subject, body)
    missing = [
        field
        for field in ("faculty", "study_level", "category")
        if classification[field] is None
    ]

    if missing:
        try:
            _send_missing_fields_reply(sender_email, subject, missing)
        except Exception:
            pass
        return ("missing_fields", missing)

    Ticket.objects.create(
        student=student,
        subject=subject[:78],
        body=body or subject,
        faculty=classification["faculty"],
        study_level=classification["study_level"],
        category=classification["category"],
    )
    return ("created", subject)


class Command(BaseCommand):
    help = "Check the monitored email inbox and create tickets from incoming emails."

    def handle(self, *args, **options):
        imap_host = settings.IMAP_HOST
        imap_port = settings.IMAP_PORT
        imap_user = settings.IMAP_USER
        imap_password = settings.IMAP_PASSWORD

        if not imap_user or not imap_password:
            self.stderr.write("IMAP credentials not configured. Skipping.")
            return

        try:
            mail = imaplib.IMAP4_SSL(imap_host, imap_port)
            mail.login(imap_user, imap_password)
        except Exception as e:
            self.stderr.write(f"Failed to connect to IMAP: {e}")
            return

        try:
            mail.select("INBOX")
            status, data = mail.search(None, "UNSEEN")

            if status != "OK" or not data[0]:
                self.stdout.write("No new emails.")
                return

            email_ids = data[0].split()
            self.stdout.write(f"Found {len(email_ids)} unread email(s).")

            for eid in email_ids:
                status, msg_data = mail.fetch(eid, "(RFC822)")
                if status != "OK":
                    continue

                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)
                action, detail = process_email(msg)

                if action == "created":
                    self.stdout.write(f"  Ticket created: {detail}")
                elif action == "missing_fields":
                    self.stdout.write(f"  Missing fields {detail} - reply sent.")
                elif action == "ignored_not_student":
                    self.stdout.write(f"  Ignored (not a student): {detail}")
                elif action == "ignored_no_subject":
                    self.stdout.write(f"  Ignored (no subject): {detail}")

        finally:
            mail.logout()

        self.stdout.write("Done.")
