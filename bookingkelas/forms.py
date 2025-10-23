from django import forms
from django.forms import ModelForm
from django.utils.html import strip_tags
from bookingkelas.models import ClassSessions, WEEKDAYS

class SessionsForm(ModelForm):
    days = forms.MultipleChoiceField(
        choices=WEEKDAYS,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Pilih hari jika kategori 'Daily'.",
    )

    class Meta:
        model = ClassSessions
        fields = [
            "title",
            "category",
            "instructor",
            "capacity_max",
            "capacity_current",
            "description",
            "price",
            "room",
            "time",
        ]

    def clean_title(self):
        title = self.cleaned_data.get("title", "")
        return strip_tags(title).strip()

    def clean_description(self):
        description = self.cleaned_data.get("description", "")
        return strip_tags(description).strip()

    def clean(self):
        cleaned = super().clean()
        category = cleaned.get("category")
        days = cleaned.get("days", [])
        if category == "daily" and not days:
            self.add_error("days", "Untuk kategori 'Daily', pilih minimal satu hari.")
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Simpan sebagai list of string, sesuai model JSONField
        instance.days = [str(d) for d in self.cleaned_data.get("days", [])]
        if commit:
            instance.save()
        return instance
