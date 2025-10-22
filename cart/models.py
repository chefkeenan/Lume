from django.db import models
from django.conf import settings
from django.db.models import Sum
import uuid


class Cart(models.Model):
    cart_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cart",
    )

    def __str__(self):
        return f"Cart({self.user.username})"

    def add(self, product, qty: int = 1):
        """
        Tambah produk ke cart dari katalog
        - Jika item sudah ada -> tambah quantity
        - Jika belum ada -> buat item baru
        """
        if qty < 1:
            qty = 1
        item, created = self.items.get_or_create(product=product, defaults={"quantity": qty})
        if not created:
            item.quantity += qty
            item.save(update_fields=["quantity"])
        return item

    def set_quantity(self, product, qty: int):
        """
        Ubah jumlah (quantity) produk yang SUDAH ADA di cart
        - Kalau produk belum ada -> tidak dibuat
        - Kalau qty <= 0 -> hapus produk dari cart
        """
        try:
            item = self.items.get(product=product)
        except CartItem.DoesNotExist:
            return None

        if qty <= 0:
            item.delete()
            return None

        item.quantity = qty
        item.save(update_fields=["quantity"])
        return item

    def remove_product(self, product):
        """Hapus produk dari cart sepenuhnya."""
        self.items.filter(product=product).delete()

    def clear(self):
        """Kosongkan seluruh isi cart (biasanya setelah checkout)"""
        self.items.all().delete()

    # buat tampilan 
    def total_items(self) -> int:
        """Jumlah total item (bukan produk unik, tapi total quantity)"""
        return self.items.aggregate(total=Sum("quantity"))["total"] or 0

class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        "catalog.Product",  
        on_delete=models.CASCADE,
        related_name="cart_items",
    )
    quantity = models.PositiveIntegerField(default=1)  

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "product"],
                name="uniq_product_per_cart",
            )
        ]

    def __str__(self):
        return f"{getattr(self.product, 'product_name', str(self.product))} x {self.quantity}"
