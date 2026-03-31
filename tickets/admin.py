from django.contrib import admin
from tickets.models import *

admin.site.register(User)
admin.site.register(Ticket)
admin.site.register(TicketAttachment)
admin.site.register(Comment)
admin.site.register(IssueGroup)
admin.site.register(IssueUpdate)
