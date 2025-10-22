from django.urls import path
from . import views

app_name = "checkout"

urlpatterns = [
    # CART / PRODUCTS
    path("cart/", views.cart_checkout_page, name="cart_checkout_page"),
    path("cart/create/", views.checkout_cart_create, name="checkout_cart_create"),

    # BOOKING CLASS (single booking -> langsung checkout)
    path("booking/checkout/<uuid:booking_id>/", views.checkout_booking_now, name="checkout_booking_now"),
]
