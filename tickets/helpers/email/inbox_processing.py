"""Inbox processing helper functions."""

from email.header import decode_header
from tickets.helpers.email.email_notifications import send_missing_fields_reply
from tickets.helpers.email.email_classifier import classify_email
from tickets.models import User, Ticket


def decode_header_value(value):
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


def extract_body(msg):
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


def extract_sender_email(msg):
    """Extract the sender's email address from the From header."""
    from_header = msg.get("From", "")
    if "<" in from_header and ">" in from_header:
        return from_header.split("<")[1].split(">")[0].strip().lower()
    return from_header.strip().lower()


def process_email(msg):
    """
    Process a single email message.

    Returns a tuple of (action, detail) where action is one of:
    'created', 'missing_fields', 'ignored_not_student', 'ignored_no_subject'.
    """
    sender_email = extract_sender_email(msg)
    subject = decode_header_value(msg.get("Subject"))
    body = extract_body(msg)

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
            send_missing_fields_reply(sender_email, subject, missing)
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
