from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import FileResponse, Http404
from django.views import View

from tickets.models.attachment import TicketAttachment
from tickets.models.user import User


class ServeAttachmentView(LoginRequiredMixin, View):
    def get(self, request, path):
        attachment = TicketAttachment.objects.filter(
            file=f"ticket_attachments/{path}"
        ).first()

        if attachment is None:
            raise Http404

        user = request.user

        if user.user_type == User.USER_TYPE_STAFF:
            pass
        elif user.user_type == User.USER_TYPE_STUDENT:
            if attachment.ticket is not None:
                owner = attachment.ticket.student
            elif attachment.comment is not None:
                owner = attachment.comment.ticket.student
            else:
                raise Http404

            if owner != user:
                raise Http404
        else:
            raise Http404

        return FileResponse(attachment.file.open("rb"))
