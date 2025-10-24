
from django.contrib import admin
from .models import ClassSessions
from .models import Booking

@admin.register(ClassSessions)
class ClassSessionsAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "instructor", "room", "time", "price", "capacity_max")
    list_filter = ("category", "instructor", "room")
    search_fields = ("title", "instructor", "description")

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('session', 'user', 'day_selected', 'created_at', 'is_cancelled')
    list_filter = ('is_cancelled', 'day_selected', 'created_at')
    search_fields = ('user', 'session')