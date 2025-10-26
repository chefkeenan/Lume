from django.urls import path
from . import views

app_name = "useradmin"

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("api/stats/", views.api_stats, name="api_stats"),
    path("api/users/", views.api_users, name="api_users"),
    path("api/orders/", views.api_orders, name="api_orders"),
    path("api/bookings/", views.api_bookings, name="api_bookings"),
    path("api/activity/", views.api_activity, name="api_activity"),
]
