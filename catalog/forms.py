# catalog/forms.py
from django import forms
from django.forms import ModelForm
from django.utils.html import strip_tags
from .models import Product

# single source of truth for Tailwind-friendly input style
BASE_INPUT = {"class": "w-full rounded-lg border px-3 py-2"}

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
            "product_name": forms.TextInput(attrs=BASE_INPUT),
            "price": forms.NumberInput(attrs={**BASE_INPUT, "min": 0}),
            "stock": forms.NumberInput(attrs={**BASE_INPUT, "min": 0}),
            "thumbnail": forms.URLInput(attrs=BASE_INPUT),
            "description": forms.Textarea(attrs={**BASE_INPUT, "rows": 4}),
            "inStock": forms.CheckboxInput(attrs={"class": "h-4 w-4"}),
        }

    def clean_product_name(self):
        name = self.cleaned_data.get("product_name", "")
        return strip_tags(name).strip()  # buang HTML injection & whitespace

    def clean_description(self):
        description = self.cleaned_data.get("description", "")
        return strip_tags(description).strip()
