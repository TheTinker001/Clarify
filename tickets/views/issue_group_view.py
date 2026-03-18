from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.views.generic import TemplateView
from tickets.models import User, IssueGroup
from django.core.paginator import Paginator
from django.db.models import Q

from clarify.settings import ITEMS_PER_PAGE


class IssueGroupView(LoginRequiredMixin, TemplateView):
    """Display existing issue groups to staff users."""

    template_name = "issue_group.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.user_type != User.USER_TYPE_STAFF:
            raise Http404

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        qs = IssueGroup.objects.all()
        qs = self.get_qs_by_search_term(context, qs)

        paginator = Paginator(qs, ITEMS_PER_PAGE)
        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context["issue_groups"] = page_obj
        context["page_obj"] = page_obj
        context["paginator"] = paginator

        return context

    def get_qs_by_search_term(self, context, qs):
        search_term = self.request.GET.get("searchTermForIG", "").strip()
        context["searchTermForIG"] = search_term
        if search_term:
            qs = qs.filter(Q(name__icontains=search_term))
        return qs.order_by("name")
