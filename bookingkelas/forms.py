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
        instance.days = [str(d) for d in self.cleaned_data.get("days", [])]
        if commit:
            instance.save()
        return instance

class AdminSessionsForm(ModelForm):
    days = forms.MultipleChoiceField(
        choices=WEEKDAYS,
        required=False,  
        widget=forms.CheckboxSelectMultiple,
        help_text="Pilih hari (hanya jika kategori 'Weekly')."
    )

    class Meta:
        model = ClassSessions
        exclude = ['description', 'capacity_current']

    def clean_title(self):
        title = self.cleaned_data.get("title", "")
        return strip_tags(title).strip()

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get("category")
        days = cleaned_data.get("days", [])

        if category and category.lower() == "weekly" and not days:
            self.add_error("days", "Untuk kategori 'Weekly', pilih minimal satu hari.")
        
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        category = self.cleaned_data.get("category")
        
        if category and category.lower() == 'daily':
            instance.days = ['0', '1', '2', '3', '4', '5']
        else:
            instance.days = [str(d) for d in self.cleaned_data.get("days", [])]

        if commit:
            instance.save()
        
        return instance