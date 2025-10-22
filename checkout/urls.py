from django.urls import path
from . import views

app_name = "checkout"

urlpatterns = [
    # Produk (Cart)
    path("cart/", views.cart_checkout_page, name="cart_checkout_page"),
    path("cart/create/", views.checkout_cart_create, name="checkout_cart_create"),

    # Booking (single)
    path("booking/<uuid:booking_id>/", views.booking_checkout_page, name="booking_checkout_page"),
    path("booking/<uuid:booking_id>/create/", views.checkout_booking_now, name="checkout_booking_now"),

    # Order Confirmed (dipakai keduanya)
    path("confirmed/", views.order_confirmed, name="order_confirmed"),
]