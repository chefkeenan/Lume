from django.urls import path
from . import views

app_name = "checkout"

urlpatterns = [
    path("cart/", views.cart_checkout_page, name="cart_checkout_page"),
    path("cart/create/", views.checkout_cart_create, name="checkout_cart_create"),
    path("cart/summary/", views.cart_summary_json, name="cart_summary_json"),

    path("booking/<int:booking_id>/", views.booking_checkout, name="booking_checkout"),

    path("confirmed/", views.order_confirmed, name="order_confirmed"),
]
