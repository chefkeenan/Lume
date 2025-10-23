from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
from django import forms
from django.contrib.auth import get_user_model

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

User = get_user_model()

class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "phone"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "input", "autocomplete": "off"}),
            "phone": forms.TextInput(attrs={"class": "input", "autocomplete": "tel"}),
        }

    def clean_username(self):
        u = self.cleaned_data["username"].strip()
        if not u:
            raise forms.ValidationError("Username cannot be empty.")
        
        qs = User.objects.filter(username=u)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Username already taken.")
        return u

    def clean_phone(self):
        p = (self.cleaned_data.get("phone") or "").strip()
        return p
