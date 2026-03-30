import secrets
from io import StringIO
from django.views import View
from django.http import JsonResponse, Http404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.core.management import call_command
from django.conf import settings


def _authorized(token: str) -> bool:
    return bool(token) and secrets.compare_digest(token, settings.CRON_TOKEN)


@method_decorator(csrf_exempt, name="dispatch")
class CheckInboxTaskView(View):
    http_method_names = ["get", "post"]

    def dispatch(self, request, *args, **kwargs):
        token = request.headers.get("X-CRON-TOKEN") or request.GET.get("token", "")
        if not _authorized(token):
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return self._run_check_inbox()

    def post(self, request, *args, **kwargs):
        return self._run_check_inbox()

    def _run_check_inbox(self):
        out = StringIO()
        call_command("check_inbox", stdout=out)
        return JsonResponse({"ok": True, "output": out.getvalue()})
