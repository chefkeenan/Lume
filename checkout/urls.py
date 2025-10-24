from django.urls import path
from . import views

app_name = "checkout"

urlpatterns = [
    # Produk (Cart)
    path("cart/", views.cart_checkout_page, name="cart_checkout_page"),
    path("cart/create/", views.checkout_cart_create, name="checkout_cart_create"),

    # Booking (single)
    path("booking/<int:booking_id>/", views.booking_checkout, name="booking_checkout"),

    # Order Confirmed (dipakai keduanya)
    path("confirmed/", views.order_confirmed, name="order_confirmed"),
]
