from django.urls import path
from . import views

app_name = "bookingkelas"

urlpatterns = [
    path("", views.catalog, name="catalog"),
    path("json/", views.sessions_json, name="sessions_json"),
    path("add/", views.add_session, name="add_session"),
]
