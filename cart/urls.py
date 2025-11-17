from django.urls import path
from . import views
from . import api

app_name = "cart"

urlpatterns = [
    path("", views.cart_page, name="page"),

    # AJAX render
    path("json/", views.cart_json, name="json"),

    # actions
    path("item/<int:item_id>/set-qty/", views.set_quantity_ajax, name="set_qty"),
    path("item/<int:item_id>/remove/", views.remove_item_ajax, name="remove_ajax"),
    path("clear/", views.clear_cart_ajax, name="clear_ajax"),

    # selection
    path("item/<int:item_id>/toggle/", views.toggle_select_ajax, name="toggle_select"),
    path("select-all/", views.select_all_ajax, name="select_all"),
    path("unselect-all/", views.unselect_all_ajax, name="unselect_all"),

    # add to cart dari katalog
    path("add/<uuid:product_id>/", views.add_to_cart, name="add"),

    # API khusus Flutter
    path("flutter/list/", api.cart_list_flutter, name="flutter_list"),
    path("flutter/add/", api.add_to_cart_flutter, name="flutter_add"),
    path("flutter/set-qty/", api.set_quantity_flutter, name="flutter_set_qty"),
    path("flutter/remove/", api.remove_item_flutter, name="flutter_remove"),

]
