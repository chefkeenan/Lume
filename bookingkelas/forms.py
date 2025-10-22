from django.forms import ModelForm
from bookingkelas.models import ClassSessions
from django.utils.html import strip_tags

class SessionsForm(ModelForm):
    class Meta:
        model = ClassSessions
        fields = ["title", "category", "capacity", "instructor", "description", "price", "room", "time"]
        
    def clean_title(self):
        name = self.cleaned_data["name"]
        return strip_tags(name)

    def clean_content(self):
        description = self.cleaned_data["description"]
        return strip_tags(description)