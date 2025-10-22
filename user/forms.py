from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class RegisterForm(UserCreationForm):
    phone = forms.CharField(max_length=30, required=False, help_text="Opsional")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "phone", "password1", "password2")

    def clean_phone(self):
        p = (self.cleaned_data.get("phone") or "").strip()
        return p

    def save(self, commit=True):
        user = super().save(commit=False)
        user.phone = self.cleaned_data.get("phone", "")
        if commit:
            user.save()
        return user