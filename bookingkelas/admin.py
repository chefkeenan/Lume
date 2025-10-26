
from django.contrib import admin
from .models import ClassSessions
from .models import Booking


class readOnlyAdmin(admin.ModelAdmin):

    def has_add_permission(self, request):
        return False  

    def has_change_permission(self, request, obj=None):
        return False 

    def has_delete_permission(self, request, obj=None):
        return False
    
@admin.register(ClassSessions)
class ClassSessionsAdmin(readOnlyAdmin):
    list_display = ("title", "category", "instructor", "room", "time", "price", "capacity_max")
    list_filter = ("category", "instructor", "room")
    search_fields = ("title", "instructor", "description")

@admin.register(Booking)
class BookingAdmin(readOnlyAdmin):
    list_display = ('session', 'user', 'day_selected', 'created_at', 'is_cancelled')
    list_filter = ('is_cancelled', 'day_selected', 'created_at')
    search_fields = ('user__username', 'session__title')