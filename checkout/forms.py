from django import forms

class CartCheckoutForm(forms.Form):
    address_line1 = forms.CharField(max_length=200, label="Address")
    address_line2 = forms.CharField(max_length=200, required=False)
    city = forms.CharField(max_length=100)
    province = forms.CharField(max_length=100)
    postal_code = forms.CharField(max_length=20, label="Postal code")
    country = forms.CharField(max_length=60, initial="Indonesia")
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))