from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.http import Http404
from django.core.paginator import Paginator
from django.db.models import Q
from tickets.helpers import get_page_slots
from tickets.models import User, IssueGroup
from clarify.settings import ITEMS_PER_PAGE


class IssueGroupView(LoginRequiredMixin, TemplateView):
    """Display existing issue groups to staff users."""

    template_name = "issue_group.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
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

        cur = page_obj.number
        max_pages = paginator.num_pages
        page_slots = get_page_slots(cur, max_pages)

        params = self.request.GET.copy()
        params.pop("page", None)
        querystring = params.urlencode()

        context.update(
            {
                "issue_groups": page_obj,
                "page_obj": page_obj,
                "paginator": paginator,
                "cur": cur,
                "max_pages": max_pages,
                "page_slots": page_slots,
                "querystring": querystring,
            }
        )

        return context

    def get_qs_by_search_term(self, context, qs):
        search_term = self.request.GET.get("searchTermForIG", "").strip()
        context["searchTermForIG"] = search_term
        if search_term:
            qs = qs.filter(Q(name__icontains=search_term))
        return qs.order_by("name")
