from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from .models import ClassSession, ClassOccurrence, Booking
from .forms import BookingForm, PrivateBookingForm
from django.urls import reverse

@login_required
def class_session_detail(request, session_id):
    session = get_object_or_404(ClassSession, id=session_id)

    if session.category in ['daily', 'weekly']:
        form_class = BookingForm
    else:
        form_class = PrivateBookingForm

    if request.method == 'POST':
        if session.category in ['daily', 'weekly']:
            form = form_class(request.POST, session=session)
        else:
            form = form_class(request.POST)

        if form.is_valid():
            try:
                if session.category in ['daily', 'weekly']:
                    occ = form.cleaned_data['occurrence']
                    # Create booking immediately (create_for_occurrence melakukan select_for_update)
                    booking = Booking.create_for_occurrence(request.user, occ)

                    # Opsi A: redirect ke internal checkout route (temenmu bikin endpoint ini)
                    # contoh: 'checkout:start' menerima booking_id sebagai arg
                    try:
                        checkout_url = reverse('checkout:start', kwargs={'booking_id': booking.id})
                        return redirect(checkout_url)
                    except Exception:
                        # jika route internal belum ada, fallback ke Opsi B
                        pass

                    # Opsi B: jika temenmu butuh kamu return booking id via query param ke halaman checkout SPA
                    # misal frontend akan detect ?booking=... lalu panggil service checkout
                    # contoh redirect ke generic page yang menampilkan instruksi/atau external URL:
                    # return redirect(f"/checkout?booking_id={booking.id}")

                    # Jika checkout external (temenmu mengembalikan URL), kalian bisa:
                    # return redirect(external_checkout_url)

                else:
                    # private booking: buat booking request (no occurrence)
                    requested_dt = form.cleaned_data['requested_datetime']
                    booking = Booking.create_private(request.user, session, requested_dt)

                    # redirect ke halaman konfirmasi / checkout private
                    try:
                        checkout_url = reverse('checkout:start', kwargs={'booking_id': booking.id})
                        return redirect(checkout_url)
                    except Exception:
                        return redirect('class_session_detail', session_id=session.id)

                # fallback default
                messages.success(request, "Booking dibuat — lanjutkan ke halaman checkout.")
                return redirect('class_session_detail', session_id=session.id)

            except ValidationError as e:
                # tampilkan pesan validasi dari create_for_occurrence
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, "Terjadi kesalahan saat membuat booking. Coba lagi.")
    else:
        # GET
        if session.category in ['daily', 'weekly']:
            form = form_class(session=session)
        else:
            form = form_class()

    context = {
        'session': session,
        'form': form,
    }
    return render(request, 'bookingkelas/class_session_detail.html', context)
