# main/urls.py
from django.urls import path
from . import views

app_name = "main"

urlpatterns = [
    path("", views.landing_view, name="landing"),
    path("shop/", views.show_main, name="show_main"),   
]
