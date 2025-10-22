# bookingkelas/models.py
from django.db import models

WEEKDAYS = [
    (0, 'Monday'),
    (1, 'Tuesday'),
    (2, 'Wednesday'),
    (3, 'Thursday'),
    (4, 'Friday'),
    (5, 'Saturday'),
]

TIME_SLOTS = [
    ('Afternoon', '14.00 PM  - 15.30 PM'),
    ('Noon', '16.00 PM - 17.30'),
    ('Evening', '18.00 PM - 19.30 PM')
]

CATEGORY_CHOICES = [
    ('daily', 'Daily'),
    ('weekly', 'Weekly'),
]

class ClassSessions(models.Model):
    title = models.CharField(max_length=255)  
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    instructor = models.CharField(max_length=100)
    capacity_current = models.PositiveIntegerField(default=0)
    capacity_max = models.PositiveIntegerField(default=20)   
    description = models.TextField()  
    price = models.PositiveIntegerField() 
    room = models.CharField(max_length=100)
    days = models.JSONField(default=list, blank=True)
    time = models.CharField(max_length=20, choices=TIME_SLOTS)
    
    def _str_(self):
        return f"{self.title} - Rp{self.price:,}"
    
    @property
    def is_full(self):
        return self.capacity_current >= self.capacity_max




