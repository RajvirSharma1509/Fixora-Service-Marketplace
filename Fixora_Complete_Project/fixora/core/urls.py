from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("search/", views.search, name="search"),
    path("providers/<int:pk>/", views.provider_detail, name="provider_detail"),
    path("services/<int:pk>/book/", views.book_service, name="book_service"),
    path("register/", views.register, name="register"),
    path("accounts/login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("bookings/<int:pk>/", views.booking_detail, name="booking_detail"),
    path("bookings/<int:pk>/cancel/", views.cancel_booking, name="cancel_booking"),
    path("provider/bookings/<int:pk>/<str:action>/", views.provider_update_booking, name="provider_update_booking"),
]
