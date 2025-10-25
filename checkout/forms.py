from django import forms

# base style untuk semua input
BASE_INPUT_STYLE = (
    "w-full rounded-2xl border border-[#D9DBD0] px-3 py-2 bg-white/90 "
    "placeholder:text-[#9BA091] focus:outline-none focus:ring-2 focus:ring-[#C9CCBF]"
)

class CartCheckoutForm(forms.Form):
    address_line1 = forms.CharField(max_length=200, label="Address")
    address_line2 = forms.CharField(max_length=200, required=False, label="Address Line 2")
    city = forms.CharField(max_length=100, label="City")
    province = forms.CharField(max_length=100, label="Province")
    postal_code = forms.CharField(max_length=20, label="Postal Code")
    country = forms.CharField(max_length=60, initial="Indonesia", label="Country")
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        label="Notes",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # placeholder opsional
        placeholders = {
            "address_line1": "Street address, house no.",
            "address_line2": "Apartment, unit, etc. (optional)",
            "city": "City",
            "province": "Province",
            "postal_code": "Postal code",
            "country": "Country",
            "notes": "Notes for courier (optional)",
        }

        for name, field in self.fields.items():
            field.widget.attrs.update({
                "class": BASE_INPUT_STYLE,
                "placeholder": placeholders.get(name, ""),
            })
