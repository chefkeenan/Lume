from django.urls import path
from . import views

app_name = "catalog"

urlpatterns = [
    path("json/", views.show_json, name="json"),
    path("add/", views.add_product, name="add"),
    path("<uuid:id>/", views.product_detail, name="detail"),
    path("update/<uuid:id>/", views.update_product_ajax, name="update_ajax"),
    path("delete/<uuid:id>/", views.delete_product_ajax, name="delete_ajax"),
]
