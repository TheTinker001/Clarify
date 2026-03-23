import secrets
from django.conf import settings
from django.http import JsonResponse, Http404
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from tickets.conditional_emails import close_inactive_tickets_with_email, send_reminder_emails


def _authorized(token):
    return bool(token) and secrets.compare_digest(token, settings.CRON_TOKEN)


@method_decorator(csrf_exempt, name="dispatch")
class CloseInactiveTicketsTaskView(View):
    http_method_names = ["get", "post"]

    def dispatch(self, request, *args, **kwargs):
        token = request.headers.get("X-CRON-TOKEN") or request.GET.get("token", "")
        if not _authorized(token):
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        reminders = send_reminder_emails(days=7)
        closed = close_inactive_tickets_with_email(days=14)
        return JsonResponse({"reminders_sent": reminders, "closed": closed})

    def post(self, request, *args, **kwargs):
        reminders = send_reminder_emails(days=7)
        closed = close_inactive_tickets_with_email(days=14)
        return JsonResponse({"reminders_sent": reminders, "closed": closed})
