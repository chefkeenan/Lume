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

    # helpers (dipanggil dari views)
    def add(self, product, qty: int = 1):
        if qty < 1:
            qty = 1
        item, created = self.items.get_or_create(
            product=product,
            defaults={"quantity": qty, "is_selected": True},
        )
        if not created:
            item.quantity += qty
            item.save(update_fields=["quantity"])
        return item

    def set_quantity(self, product, qty: int):
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
        self.items.filter(product=product).delete()

    def clear(self):
        self.items.all().delete()

    def total_items(self) -> int:
        return self.items.aggregate(total=Sum("quantity"))["total"] or 0


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        "catalog.Product", on_delete=models.CASCADE, related_name="cart_items"
    )
    quantity = models.PositiveIntegerField(default=1)
    # NEW: untuk pilih item mana yang mau di-checkout
    is_selected = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "product"], name="uniq_product_per_cart"
            )
        ]

    def __str__(self):
        return f"{getattr(self.product, 'product_name', str(self.product))} x {self.quantity}"
