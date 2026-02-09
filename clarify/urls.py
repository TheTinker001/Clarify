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
    path("dashboard/", views.dashboard, name="dashboard"),
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
    path("ticket/<str:url_code>/", views.ticket_detail, name="ticket_detail"),
    path("create_ticket/", views.CreateTicketView.as_view(), name="create_ticket"),
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
