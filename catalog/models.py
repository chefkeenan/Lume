import uuid
from django.db import models

class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    prodcut_name = models.CharField(max_length=255)
    stock = models.PositiveIntegerField(default=1)
    thumbnail = models.URLField(blank=True, null=True)
    inStock = models.BooleanField(default=True)
    description = models.TextField
    price = models.PositiveIntegerField
    
    def __str__(self):
        return f"{self.product_name} {self.price}"