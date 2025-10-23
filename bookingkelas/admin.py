
from django.contrib import admin
from .models import ClassSessions

@admin.register(ClassSessions)
class ClassSessionsAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "instructor", "room", "time", "price", "capacity_max")
    list_filter = ("category", "instructor", "room")
    search_fields = ("title", "instructor", "description")
