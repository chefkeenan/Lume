from django.urls import path
from . import views

app_name = "bookingkelas"

urlpatterns = [
    path("", views.catalog, name="catalog"),
    path("json/", views.sessions_json, name="sessions_json"),
    path("add/", views.add_session, name="add_session"),
    
    # booking alur
    path("<int:session_id>/book/", views.book_class, name="book_class"),
    path("get-details/<str:base_title>/", views.get_session_details_json, name="get_session_details_json"),
    path("book-daily-session/", views.book_daily_session, name="book_daily_session"),

    # (opsional) CRUD simple
    path("classes/", views.class_list, name="class_list"),
    path("classes/<int:pk>/edit/", views.class_edit, name="class_edit"),
    path("classes/<int:pk>/delete/", views.class_delete, name="class_delete"),
    path("classes/<int:pk>/get-form/", views.get_edit_form, name="get_edit_form"),
]