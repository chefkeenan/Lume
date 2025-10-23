from django.contrib import admin
from .models import Cart, CartItem

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("user", "total_items")
    search_fields = ("user__username",)
    readonly_fields = ("cart_id",)

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("cart", "product", "quantity", "is_selected")
    search_fields = ("cart__user__username", "product__product_name")
    list_filter = ("is_selected",)
