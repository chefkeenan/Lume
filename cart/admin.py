from django.contrib import admin
from .models import Cart, CartItem


class ReadOnlyAdmin(admin.ModelAdmin):

    def has_add_permission(self, request):
        return False  

    def has_change_permission(self, request, obj=None):
        return False 

    def has_delete_permission(self, request, obj=None):
        return False  


@admin.register(Cart)
class CartAdmin(ReadOnlyAdmin):
    list_display = (
        "cart_id",
        "user",
        "total_items_display",
    )
    # pencarian berdasarkan username, email, atau phone
    search_fields = (
        "user__username",
        "user__email",
        "user__phone",
    )
    ordering = ("user__username",)

    def total_items_display(self, obj: Cart):
        return obj.total_items()

    total_items_display.short_description = "Total Items"


@admin.register(CartItem)
class CartItemAdmin(ReadOnlyAdmin):
    list_display = (
        "id",
        "cart",
        "user_username",
        "product",
        "quantity",
        "is_selected",
    )
    list_filter = ("is_selected",)
    search_fields = (
        "cart__user__username",
        "cart__user__email",
        "cart__user__phone",
        "product__product_name",
    )
    ordering = ("cart__user__username", "product__product_name")

    def user_username(self, obj: CartItem):
        return obj.cart.user.username

    user_username.short_description = "User"
