from django import forms
from .models import CartItem

class CartItemQuantityForm(forms.ModelForm):
    class Meta:
        model = CartItem
        fields = ["quantity"]
        widgets = {
            "quantity": forms.NumberInput(attrs={"min": 0})
        }

    def clean_quantity(self):
        q = self.cleaned_data.get("quantity")
        if q is None or q < 0:
            q = 0
        return q
