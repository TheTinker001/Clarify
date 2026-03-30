import secrets
from django.views import View
from django.http import JsonResponse, Http404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from tickets.helpers.email.ticket_maintenance import (
    send_reminder_emails,
    close_inactive_tickets_with_email,
)
from tickets.helpers.task_auth import authorized
from clarify.settings import (
    INACTIVE_TICKET_FIRST_REMINDER,
    INACTIVE_TICKET_FINAL_REMINDER,
)


@method_decorator(csrf_exempt, name="dispatch")
class CloseInactiveTicketsTaskView(View):
    """Close inactive tickets after a certain amount of time."""

    http_method_names = ["get", "post"]

    def dispatch(self, request, *args, **kwargs):
        token = request.headers.get("X-CRON-TOKEN") or request.GET.get("token", "")
        if not authorized(token):
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        reminders = send_reminder_emails(days=INACTIVE_TICKET_FIRST_REMINDER)
        closed = close_inactive_tickets_with_email(days=INACTIVE_TICKET_FINAL_REMINDER)
        return JsonResponse({"reminders_sent": reminders, "closed": closed})

    def post(self, request, *args, **kwargs):
        reminders = send_reminder_emails(days=INACTIVE_TICKET_FIRST_REMINDER)
        closed = close_inactive_tickets_with_email(days=INACTIVE_TICKET_FINAL_REMINDER)
        return JsonResponse({"reminders_sent": reminders, "closed": closed})
