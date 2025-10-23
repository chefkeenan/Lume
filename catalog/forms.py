from django import forms
from django.forms import ModelForm
from django.utils.html import strip_tags
from .models import Product

class ProductForm(ModelForm):
    class Meta:
        model = Product
        fields = ["product_name", "description", "price", "thumbnail", "stock", "inStock"]
        labels = {
            "product_name": "Product Name",
            "description": "Description",
            "price": "Price (Rp)",
            "thumbnail": "Image URL",
            "stock": "Stock",
            "inStock": "In Stock",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def clean_product_name(self):
        name = self.cleaned_data.get("product_name", "")
        return strip_tags(name).strip()

    def clean_description(self):
        description = self.cleaned_data.get("description", "")
        return strip_tags(description).strip()
