# cart/urls.py
from django.urls import path
from . import views

app_name = "cart"

urlpatterns = [
    # Page
    path("", views.cart_page, name="page"),

    # Data (JSON) untuk AJAX render
    path("json/", views.cart_json, name="json"),

    # Actions (AJAX)
    path("item/<int:item_id>/set-qty/", views.set_quantity_ajax, name="set_qty"),
    path("item/<int:item_id>/remove/", views.remove_item_ajax, name="remove_ajax"),
    path("clear/", views.clear_cart_ajax, name="clear_ajax"),

    # Selection (AJAX)
    path("item/<int:item_id>/toggle/", views.toggle_select_ajax, name="toggle_select"),
    path("select-all/", views.select_all_ajax, name="select_all"),
    path("unselect-all/", views.unselect_all_ajax, name="unselect_all"),

    # (opsional) add to cart dari katalog
    path("add/<uuid:product_id>/", views.add_to_cart, name="add"),
]
