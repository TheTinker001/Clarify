"""
URL configuration for clarify project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from tickets import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.HomeView.as_view(), name="home"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("log_in/", views.LogInView.as_view(), name="log_in"),
    path("log_out/", views.log_out, name="log_out"),
    path("password/", views.PasswordView.as_view(), name="password"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path(
        "profile/staffedit/",
        views.StaffPreferencesView.as_view(),
        name="profile_staff_edit",
    ),
    path("profile/edit/", views.ProfileUpdateView.as_view(), name="profile_edit"),
    path("sign_up/", views.SignUpView.as_view(), name="sign_up"),
    path(
        "ticket/<str:url_code>/", views.TicketDetailView.as_view(), name="ticket_detail"
    ),
    path(
        "ticket/<str:url_code>/internal-notes",
        views.InternalNoteEditView.as_view(),
        name="internal_note_edit",
    ),
    path("create_ticket/", views.CreateTicketView.as_view(), name="create_ticket"),
    path(
        "ticket/<str:url_code>/claim/",
        views.TicketClaimView.as_view(),
        name="ticket_claim",
    ),
    path(
        "ticket/<str:url_code>/unclaim/",
        views.TicketUnclaimView.as_view(),
        name="ticket_unclaim",
    ),
    path(
        "user/<str:username>/",
        views.ProfileOtherUserView.as_view(),
        name="profile_other_user",
    ),
    path(
        "ticket/<str:ticket_url_code>/edit-comment/<str:comment_url_code>/",
        views.EditCommentView.as_view(),
        name="edit_comment",
    ),
    path(
        "tasks/close-inactive/",
        views.CloseInactiveTicketsTaskView.as_view(),
        name="close_inactive_task",
    ),
    path(
        "tasks/check-inbox/",
        views.CheckInboxTaskView.as_view(),
        name="check_inbox_task",
    ),
    path("issues/", views.IssueGroupView.as_view(), name="issue_group"),
    path(
        "issues/create/",
        views.CreateIssueGroupView.as_view(),
        name="create_issue_group",
    ),
    path(
        "issues/<slug:slug>/",
        views.IssueGroupDetailView.as_view(),
        name="issue_group_detail",
    ),
    path(
        "issues/<slug:slug>/edit",
        views.UpdateIssueGroupView.as_view(),
        name="edit_issue_group",
    ),
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
