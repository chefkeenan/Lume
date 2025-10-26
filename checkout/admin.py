from django.contrib import admin
from django.db.models import Count
from .models import ProductOrder, ProductOrderItem, BookingOrder, BookingOrderItem

class ReadOnlyAdmin(admin.ModelAdmin):
    """Admin base class untuk membuat model read-only di Django Admin."""

    def has_add_permission(self, request):
        return False  

    def has_change_permission(self, request, obj=None):
        return False  

    def has_delete_permission(self, request, obj=None):
        return False  


class ProductOrderItemInline(admin.TabularInline):
    model = ProductOrderItem
    extra = 0
    can_delete = False
    fields = ("product_name", "unit_price", "quantity")
    readonly_fields = ("product_name", "unit_price", "quantity")

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class BookingOrderItemInline(admin.TabularInline):
    model = BookingOrderItem
    extra = 0
    can_delete = False
    fields = ("session_title", "unit_price", "quantity")
    readonly_fields = ("session_title", "unit_price", "quantity")

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ProductOrder)
class ProductOrderAdmin(ReadOnlyAdmin):
    inlines = [ProductOrderItemInline]
    date_hierarchy = "created_at"
    list_display = ("id", "user", "receiver_name", "city", "total", "items_count", "created_at")
    list_filter = ("created_at", "city", "province", "country")
    search_fields = (
        "id",
        "user__username",
        "receiver_name",
        "receiver_phone",
        "address_line1",
        "city",
        "province",
    )
    readonly_fields = (
        "user", "cart", "receiver_name", "receiver_phone", "address_line1",
        "address_line2", "city", "province", "postal_code", "country",
        "subtotal", "shipping_fee", "total", "notes", "created_at"
    )
    ordering = ("-created_at",)
    list_select_related = ("user",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(_items_count=Count("items")).select_related("user")

    def items_count(self, obj):
        return getattr(obj, "_items_count", obj.items.count())
    items_count.short_description = "Items"


@admin.register(BookingOrder)
class BookingOrderAdmin(ReadOnlyAdmin):
    inlines = [BookingOrderItemInline]
    date_hierarchy = "created_at"
    list_display = ("id", "user", "total", "items_count", "created_at")
    list_filter = ("created_at",)
    search_fields = ("id", "user__username", "notes")
    readonly_fields = ("user", "subtotal", "total", "notes", "created_at")
    ordering = ("-created_at",)
    list_select_related = ("user",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(_items_count=Count("items")).select_related("user")

    def items_count(self, obj):
        return getattr(obj, "_items_count", obj.items.count())
    items_count.short_description = "Items"
