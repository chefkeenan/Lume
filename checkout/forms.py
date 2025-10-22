from django import forms

class CartCheckoutForm(forms.Form):
    # contact
    receiver_name = forms.CharField(max_length=120, label="Receiver name")
    receiver_phone = forms.CharField(max_length=30, label="Receiver phone")

    # address (snapshot)
    address_line1 = forms.CharField(max_length=200, label="Address line 1")
    address_line2 = forms.CharField(max_length=200, label="Address line 2", required=False)
    city = forms.CharField(max_length=100)
    province = forms.CharField(max_length=100)
    postal_code = forms.CharField(max_length=20, label="Postal code")
    country = forms.CharField(max_length=60, initial="Indonesia")

    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))
