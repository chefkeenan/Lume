# bookingkelas/models.py
from django.db import models, transaction
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator
import uuid

WEEKDAYS = [
    (0, 'Monday'),
    (1, 'Tuesday'),
    (2, 'Wednesday'),
    (3, 'Thursday'),
    (4, 'Friday'),
    (5, 'Saturday'),
    (6, 'Sunday'),
]

CATEGORY_CHOICES = [
    ('daily', 'Daily'),
    ('weekly', 'Weekly'),
    ('private', 'Private'),
]


class Instructor(models.Model):
    name = models.CharField(max_length=100)
    bio = models.TextField(blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Room(models.Model):
    name = models.CharField(max_length=50)
    address = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.name


class ClassSession(models.Model):
    title = models.CharField(max_length=150)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    instructor = models.ForeignKey(Instructor, on_delete=models.SET_NULL, null=True, blank=True)
    room = models.ForeignKey(Room, on_delete=models.PROTECT)
    price = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    capacity = models.PositiveIntegerField(default=20)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.category})"

    def next_occurrences(self, limit=5):
        """Simple helper: next upcoming occurrences (queryset)."""
        return self.occurrences.filter(date__gte=timezone.localdate()).order_by('date', 'start_time')[:limit]


class ScheduleRule(models.Model):
    session = models.ForeignKey(ClassSession, related_name='schedule_rules', on_delete=models.CASCADE)
    weekday = models.IntegerField(choices=WEEKDAYS)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        unique_together = ('session', 'weekday', 'start_time')

    def __str__(self):
        return f"{self.session.title}: {self.get_weekday_display()} {self.start_time}-{self.end_time}"


class ClassOccurrence(models.Model):
    """
    One concrete occurrence (one meeting on a date).
    """
    session = models.ForeignKey(ClassSession, related_name='occurrences', on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    capacity = models.PositiveIntegerField(null=True, blank=True)  # default to session.capacity if null
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('session', 'date', 'start_time')
        ordering = ('date','start_time')

    def capacity_value(self):
        return self.capacity if self.capacity is not None else self.session.capacity

    def booked_count(self):
        # count only bookings that are not cancelled (uses is_cancelled flag in Booking)
        return self.bookings.filter(is_cancelled=False).count()

    def available_spots(self):
        return self.capacity_value() - self.booked_count()

    def is_in_future(self):
        dt = timezone.datetime.combine(self.date, self.start_time)
        dt = timezone.make_aware(dt) if timezone.is_naive(dt) else dt
        return dt > timezone.now()

    def __str__(self):
        return f"{self.session.title} on {self.date} {self.start_time}"


class Booking(models.Model):
    """
    Simple booking model: no verbose status string.
    The app flow you described:
      - user pilih kelas + jadwal
      - server buat Booking
      - redirect ke halaman checkout (payment handled by another service/person)
      - after payment, external party can mark booking as paid/confirm outside this model (or you can add a payment model later)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
    occurrence = models.ForeignKey(ClassOccurrence, related_name='bookings', on_delete=models.CASCADE, null=True, blank=True)
    session = models.ForeignKey(ClassSession, related_name='bookings', on_delete=models.CASCADE)
    requested_datetime = models.DateTimeField(null=True, blank=True)  # for private sessions
    is_cancelled = models.BooleanField(default=False)  # lightweight cancellation flag (optional)
    created_at = models.DateTimeField(auto_now_add=True)
    price_at_booking = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        ordering = ('-created_at',)
        unique_together = (('user', 'occurrence'),)  # optional: prevent duplicate user+occurrence bookings

    def __str__(self):
        return f"Booking {self.id} - {self.user} - {self.session.title}"

    def clean(self):
        # basic integrity checks
        from django.core.exceptions import ValidationError
        if self.occurrence and self.occurrence.session_id != self.session_id:
            raise ValidationError("Occurrence tidak sesuai dengan session.")
        if self.occurrence and not self.occurrence.is_in_future():
            raise ValidationError("Tidak bisa booking occurrence yang sudah lewat.")
        return super().clean()

    @staticmethod
    def create_for_occurrence(user, occurrence):
        """
        Create booking for an occurrence safely (prevents race condition using select_for_update).
        This DOES create the Booking immediately (no status). If payment is handled externally,
        the checkout flow should reference this booking (e.g. booking.id) so the payment side
        knows which booking it's for.
        """
        from django.core.exceptions import ValidationError
        with transaction.atomic():
            occ = ClassOccurrence.objects.select_for_update().select_related('session').get(pk=occurrence.pk)
            if not occ.is_in_future():
                raise ValidationError("Occurrence sudah lewat.")
            if occ.available_spots() <= 0:
                raise ValidationError("Kelas ini sudah penuh.")
            # prevent duplicate booking by same user on same occurrence (enforced by unique_together too)
            if Booking.objects.filter(user=user, occurrence=occ, is_cancelled=False).exists():
                raise ValidationError("Kamu sudah booking occurrence ini.")
            booking = Booking.objects.create(
                user=user,
                occurrence=occ,
                session=occ.session,
                price_at_booking=occ.session.price,
            )
            return booking

    @staticmethod
    def create_private(user, session, requested_datetime):
        """
        Create a private booking request (no occurrence).
        """
        return Booking.objects.create(
            user=user,
            occurrence=None,
            session=session,
            requested_datetime=requested_datetime,
            price_at_booking=session.price,
        )
