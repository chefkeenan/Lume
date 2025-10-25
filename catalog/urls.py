from django.urls import path
from . import views

app_name = "catalog"

urlpatterns = [
    path("products/", views.product_list, name="product_list"),
    path("products/add/", views.product_create, name="product_add"),
    path("products/add-modal/", views.product_add_modal, name="product_add_modal"),
    path("products/create-modal/", views.product_create_modal, name="product_create_modal"),

    # pakai uuid
    path("products/<uuid:pk>/edit-modal/", views.product_edit_modal, name="product_edit_modal"),
    path("products/<uuid:pk>/edit/",       views.product_update,     name="product_edit"),
    path("products/<uuid:pk>/delete/", views.product_delete, name="product_delete"),

    # route detail untuk kartu produk
    path("products/<uuid:id>/", views.product_detail, name="detail"),
]
