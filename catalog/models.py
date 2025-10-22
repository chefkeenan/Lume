# catalog/models.py
import uuid
from urllib.parse import quote

from django.db import models

class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product_name = models.CharField(max_length=255)
    stock = models.PositiveIntegerField(default=1)
    thumbnail = models.URLField(blank=True, null=True)
    inStock = models.BooleanField(default=True)
    description = models.TextField()
    price = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.product_name} - Rp{self.price:,}"

    @property
    def normalized_thumbnail(self) -> str:
        """Bersihkan kutip/whitespace & pastikan ada protokol."""
        url = (self.thumbnail or "").strip().strip('"').strip("'")
        if not url:
            return ""
        if url.startswith("//"):
            url = "https:" + url
        elif url.startswith("www."):
            url = "https://" + url
        return url

    @property
    def proxied_thumbnail(self) -> str:
        """
        Pakai images.weserv.nl biar lolos hotlink/CORS.
        Kita kirim host+path saja (tanpa skema), di-encode aman.
        """
        url = self.normalized_thumbnail
        if not url:
            return ""
        # hapus skema, encode
        no_scheme = url.replace("https://", "").replace("http://", "")
        return (
            "https://images.weserv.nl/?url="
            + quote(no_scheme, safe="")
            + "&w=1200&h=800&fit=cover&we&il"
        )
