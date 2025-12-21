import uuid
from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from bookingkelas.models import Booking  

class ProductOrder(models.Model):
    FLAT_SHIPPING = Decimal("10000.00") 

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="product_orders"
    )
    cart = models.ForeignKey(
        "cart.Cart", on_delete=models.SET_NULL, null=True, blank=True, related_name="orders"
    )

    receiver_name = models.CharField(max_length=120)
    receiver_phone = models.CharField(max_length=30)
    address_line1 = models.CharField(max_length=200)
    address_line2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100)
    province = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=60, default="Indonesia")

    subtotal = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal("0"),
        validators=[MinValueValidator(Decimal("0"))]
    )
    shipping_fee = models.DecimalField(
        max_digits=12, decimal_places=2, default=FLAT_SHIPPING,
        validators=[MinValueValidator(Decimal("0"))]
    )
    total = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal("0"),
        validators=[MinValueValidator(Decimal("0"))]
    )

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def recalc_totals(self):
        prod_sum = sum(i.line_total for i in self.items.all())
        self.subtotal = prod_sum
        self.shipping_fee = self.FLAT_SHIPPING
        self.total = self.subtotal + self.shipping_fee

    class Meta:
        indexes = [models.Index(fields=["user", "created_at"])]

    def __str__(self):
        return f"ProductOrder #{self.pk}"


class ProductOrderItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(ProductOrder, on_delete=models.CASCADE, related_name="items")

    product = models.ForeignKey("catalog.Product", on_delete=models.SET_NULL, null=True, blank=True)

    product_name = models.CharField(max_length=200)
    unit_price = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0"))]
    )
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    @property
    def line_total(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"


class BookingOrder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="booking_orders"
    )

    subtotal = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal("0"),
        validators=[MinValueValidator(Decimal("0"))]
    )
    total = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal("0"),
        validators=[MinValueValidator(Decimal("0"))]
    )

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def recalc_totals(self):
        s = sum(i.line_total for i in self.items.all())
        self.subtotal = s
        self.total = s

    class Meta:
        indexes = [models.Index(fields=["user", "created_at"])]

    def __str__(self):
        return f"BookingOrder #{self.pk}"

#tes
class BookingOrderItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(BookingOrder, on_delete=models.CASCADE, related_name="items")

    booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True, related_name="order_items")

    session_title = models.CharField(max_length=200)
    occurrence_date = models.DateField(null=True, blank=True)
    occurrence_start_time = models.TimeField(null=True, blank=True)
    unit_price = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0"))]
    )
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    @property
    def line_total(self):
        return self.unit_price * self.quantity

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["booking"], name="unique_booking_per_order_items"),
        ]

    def __str__(self):
        return f"{self.session_title} x {self.quantity}"
