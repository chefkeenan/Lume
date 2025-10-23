from django.urls import path
from . import views

app_name = "cart"

urlpatterns = [
    # Page shell (template)
    path("", views.cart_page, name="page"),

    # Data JSON (filterable)
    path("json/", views.cart_json, name="json"),

    # Actions (AJAX)
    path("item/<int:item_id>/set-qty/", views.set_quantity_ajax, name="set_qty"),
    path("item/<int:item_id>/remove/", views.remove_item_ajax, name="remove_ajax"),
    path("clear/", views.clear_cart_ajax, name="clear_ajax"),

    # Selection
    path("item/<int:item_id>/toggle-select/", views.toggle_select_ajax, name="toggle_select"),
    path("select-all/", views.select_all_ajax, name="select_all"),
    path("unselect-all/", views.unselect_all_ajax, name="unselect_all"),

    # Forms (ModelForm)
    path("item/<int:item_id>/quantity-form/", views.quantity_form, name="qty_form"),
    path("item/<int:item_id>/quantity-form/submit/", views.quantity_form_submit, name="qty_form_submit"),
]
