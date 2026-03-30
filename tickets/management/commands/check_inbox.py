"""Management command to check the monitored email inbox and create tickets."""

from django.core.management.base import BaseCommand
import imaplib
import email
from django.conf import settings
from tickets.helpers.email.inbox_processing import process_email


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
