from django.contrib import admin
from django.utils.safestring import mark_safe
from django.http import HttpResponse
from django.db.models import Count
from .models import Product 
import csv

# helper kecil buat tampilan admin yang ramah operasional
def _rupiah(n):
    s = f"{n:,}"
    return "Rp" + s.replace(",", ".")

@admin.action(description="Export selected to CSV")
def export_as_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="product.csv"'
    writer = csv.writer(response)
    writer.writerow(["id", "product_name", "price", "stock", "inStock", "thumbnail", "description"])
    for p in queryset:
        writer.writerow([str(p.id), p.product_name, p.price, p.stock, p.inStock, p.thumbnail or "", p.description or ""])
    return response

class ReadOnlyAdmin(admin.ModelAdmin):
    """Base admin: allow viewing but forbid add/change/delete."""
    actions = (export_as_csv,)  

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return True

class ProductAdmin(ReadOnlyAdmin):
    list_display = ("thumb", "product_name", "price_fmt", "stock", "inStock", "desc_short", "id")
    list_display_links = ("product_name",)  
    search_fields = ("product_name", "description")
    list_filter = ("inStock",)
    ordering = ("-inStock", "-stock", "product_name")
    readonly_fields = (
        "id", "product_name", "price", "stock", "inStock",
        "thumbnail", "image_preview", "proxied_image_preview", "description"
    )
    actions = (export_as_csv,)
    fieldsets = (
        ("Info Produk", {"fields": ("id", "product_name", "price", "stock", "inStock")}),
        ("Media", {"fields": ("thumbnail", "image_preview", "proxied_image_preview")}),
        ("Deskripsi", {"fields": ("description",)}),
    )
    list_per_page = 25
    save_on_top = False  

    @admin.display(ordering="price", description="Price")
    def price_fmt(self, obj):
        return _rupiah(obj.price)

    @admin.display(description="Description")
    def desc_short(self, obj):
        text = (obj.description or "").strip()
        return (text[:60] + "…") if len(text) > 60 else text

    @admin.display(description="Thumb")
    def thumb(self, obj):
        url = getattr(obj, "normalized_thumbnail", None)
        if not url:
            return "-"
        return mark_safe(
            f'<img src="{url}" style="height:40px;width:40px;object-fit:cover;border-radius:6px;" />'
        )

    @admin.display(description="Thumbnail Preview")
    def image_preview(self, obj):
        url = getattr(obj, "normalized_thumbnail", None)
        if not url:
            return "No image"
        return mark_safe(f'<img src="{url}" style="max-width:320px;border-radius:12px;" />')

    @admin.display(description="Proxied Preview")
    def proxied_image_preview(self, obj):
        url = getattr(obj, "proxied_thumbnail", None)
        if not url:
            return "No image"
        return mark_safe(f'<img src="{url}" style="max-width:320px;border-radius:12px;" />')

admin.site.register(Product, ProductAdmin)
