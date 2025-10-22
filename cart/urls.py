from django.urls import path
from . import views

app_name = "cart"

urlpatterns = [
    path("", views.cart_page, name="page"),
    path("item/<int:item_id>/inc/", views.increment_item, name="inc"),
    path("item/<int:item_id>/dec/", views.decrement_item, name="dec"),
    path("item/<int:item_id>/remove/", views.remove_item, name="remove"),
    path("clear/", views.clear_cart, name="clear"),
]
