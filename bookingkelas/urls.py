from django.urls import path
from . import views

app_name = "bookingkelas"

urlpatterns = [
    path('class/<int:session_id>/', views.class_session_detail, name='class_session_detail'),
]
