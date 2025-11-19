from django.urls import path
from . import views, api

app_name = "catalog"

urlpatterns = [
    path("products/", views.product_list, name="product_list"),
    path("products/add/", views.product_create, name="product_add"),
    path("products/add-modal/", views.product_add_modal, name="product_add_modal"),
    path("products/create-modal/", views.product_create, name="product_create_modal"),

    path("products/<uuid:pk>/edit-modal/", views.product_edit_modal, name="product_edit_modal"),
    path("products/<uuid:pk>/edit/",       views.product_update,     name="product_edit"),
    path("products/<uuid:pk>/delete/", views.product_delete, name="product_delete"),
    path("products/<uuid:id>/", views.product_detail, name="detail"),
    
    path("api/products/", api.api_products, name="api_products"),
    path("api/products/<uuid:pk>/", api.api_product_detail, name="api_product_detail"),
    path("api/products/create/", api.api_product_create, name="api_product_create"),
    path("api/products/<uuid:pk>/update/", api.api_product_update, name="api_product_update"),
    path("api/products/<uuid:pk>/delete/", api.api_product_delete, name="api_product_delete"),

]
