# bookingkelas/forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Booking, ClassSession, ClassOccurrence

class BookingForm(forms.ModelForm):
    """Form buat booking kelas umum (daily/weekly)."""
    class Meta:
        model = Booking
        fields = ['occurrence']
        widgets = {
            'occurrence': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, session: ClassSession = None, **kwargs):
        """
        Terima session supaya kita bisa batasi queryset occurrence hanya untuk session tsb.
        """
        super().__init__(*args, **kwargs)
        self.session = session
        if session:
            qs = session.occurrences.filter(date__gte=timezone.localdate()).order_by('date', 'start_time')
            self.fields['occurrence'].queryset = qs

    def clean_occurrence(self):
        occ = self.cleaned_data.get('occurrence')
        if not occ:
            raise ValidationError("Pilih jadwal terlebih dahulu.")
        if self.session and occ.session_id != self.session.id:
            raise ValidationError("Pilihan jadwal tidak valid untuk sesi ini.")
        if not occ.is_in_future():
            raise ValidationError("Jadwal sudah lewat.")
        if occ.available_spots() <= 0:
            raise ValidationError("Kelas ini sudah penuh.")
        return occ


class PrivateBookingForm(forms.Form):
    """Form untuk booking private class."""
    requested_date = forms.DateField(widget=forms.SelectDateWidget)
    requested_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}))

    def clean(self):
        cleaned = super().clean()
        date = cleaned.get('requested_date')
        time = cleaned.get('requested_time')

        if not date or not time:
            raise ValidationError("Tanggal dan jam harus diisi.")

        dt = timezone.datetime.combine(date, time)
        dt = timezone.make_aware(dt) if timezone.is_naive(dt) else dt
        if dt < timezone.now():
            raise ValidationError("Tidak bisa booking di masa lalu.")

        cleaned['requested_datetime'] = dt
        return cleaned
