from django.conf import settings
from django.db import models
from decimal import Decimal

WEEKDAYS = [
    ('mon', 'Monday'),
    ('tue', 'Tuesday'),
    ('wed', 'Wednesday'),
    ('thur', 'Thursday'),
    ('fri', 'Friday'),
    ('sat', 'Saturday'),
]

TIME_SLOTS = [
    ('10.00 AM - 11.30 AM', '10.00 AM - 11.30 AM'),
    ('12.00 PM - 13.30 PM', '12.00 PM - 13.30 PM'),
    ('14.00 PM - 15.30 PM', '14.00 PM - 15.30 PM'),
    ('16.00 PM - 17.30 PM', '16.00 PM - 17.30 PM'),
    ('18.00 PM - 19.30 PM', '18.00 PM - 19.30 PM')
]

CATEGORY_CHOICES = [
    ('daily', 'Daily'),
    ('weekly', 'Weekly'),
]

class ClassSessions(models.Model):
    title = models.CharField(max_length=255)  
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    instructor = models.CharField(max_length=15)
    capacity_current = models.PositiveIntegerField(default=0)
    capacity_max = models.PositiveIntegerField(default=20)   
    description = models.CharField(max_length=200, blank=True)  
    price = models.PositiveIntegerField() 
    room = models.CharField(max_length=5)
    days = models.JSONField(default=list, blank=True)
    time = models.CharField(max_length=255, choices=TIME_SLOTS)
    
    def __str__(self):
        return f"{self.title} - Rp{self.price:,}"
    
    @property
    def is_full(self):
        return self.capacity_current >= self.capacity_max

class Booking(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings")
    session = models.ForeignKey(ClassSessions, on_delete=models.CASCADE, related_name="bookings")
    day_selected = models.CharField(max_length=10, blank=True) 
    is_cancelled = models.BooleanField(default=False)
    price_at_booking = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.session.title} ({self.user.username})"


