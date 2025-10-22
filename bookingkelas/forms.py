from django import forms
from django.forms import ModelForm
from django.utils.html import strip_tags
from bookingkelas.models import ClassSessions, WEEKDAYS

WEEKDAY_CHOICES = [(str(day[0]), day[1]) for day in WEEKDAYS]

class SessionsForm(ModelForm):
    days = forms.MultipleChoiceField(
        choices=WEEKDAY_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
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
        days = self.cleaned_data.get("days", [])
        try:
            instance.days = [int(d) for d in days]
        except Exception:
            instance.days = []
        if commit:
            instance.save()
        return instance
