from django.urls import path
from . import views

app_name = "bookingkelas"

urlpatterns = [
    path("", views.catalog, name="catalog"),
    path("json/", views.sessions_json, name="sessions_json"),
    path("add/", views.add_session, name="add_session"),
    
    # booking alur
    path("<int:session_id>/book/", views.book_class, name="book_class"),
    path("<str:base_title>/choose-day/", views.choose_day, name="choose_day"),
    
    # (opsional) CRUD simple
    path("classes/", views.class_list, name="class_list"),
    path("classes/<int:pk>/edit/", views.class_edit, name="class_edit"),
    path("classes/<int:pk>/delete/", views.class_delete, name="class_delete"),



]

