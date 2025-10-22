# bookingkelas/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from .models import ClassSessions, WEEKDAYS
from .forms import SessionsForm

def _weekday_map():
    """
    Kembalikan mapping key -> name dari WEEKDAYS model.
    Contoh: {'mon': 'Monday', 'tue': 'Tuesday', ...}
    """
    return dict(WEEKDAYS)

def catalog(request):
    """
    Tampilkan katalog semua kelas.
    Mengirimkan sessions sebagai list of dict: setiap item berisi object 'obj'
    dan 'days_names' (list nama hari yang readable).
    """
    qs = ClassSessions.objects.all().order_by("title")
    weekday_map = _weekday_map()

    sessions = []
    for s in qs:
        days = s.days if s.days else []
        # pastikan semua key jadi string sebelum lookup
        try:
            days_names = [weekday_map.get(str(d), str(d)) for d in days]
        except Exception:
            days_names = [str(d) for d in days]
        sessions.append({
            "obj": s,
            "days_names": days_names
        })

    context = {"sessions": sessions}
    return render(request, "bookingkelas/show_class.html", context)


def sessions_json(request):
    """
    Kembalikan JSON berisi semua session.
    days tetap disimpan dalam bentuk aslinya (list of keys), dan days_names
    berisi nama hari yang sudah di-convert.
    """
    qs = ClassSessions.objects.all().order_by("title")
    weekday_map = _weekday_map()

    data = []
    for s in qs:
        days = s.days if s.days else []
        try:
            days_names = [weekday_map.get(str(d), str(d)) for d in days]
        except Exception:
            days_names = [str(d) for d in days]

        data.append({
            "id": s.id,
            "title": s.title,
            "category": s.category,
            "category_display": s.get_category_display(),
            "instructor": s.instructor,
            "capacity_current": s.capacity_current,
            "capacity_max": s.capacity_max,
            "description": s.description,
            "price": s.price,
            "room": s.room,
            "days": days,
            "days_names": days_names,
            "time": s.time,
            "is_full": s.is_full,
        })

    return JsonResponse({"sessions": data}, safe=True)


def add_session(request):
    """
    Tambah session:
    - Jika POST: validasi form, ambil field days (bisa dari form.cleaned_data atau request.POST.getlist)
      lalu set ke instance.days dan simpan.
    - Jika GET: tampilkan form.
    Setelah sukses, redirect ke katalog.
    """
    if request.method == "POST":
        form = SessionsForm(request.POST)
        if form.is_valid():
            # Save instance without commit agar kita bisa set days
            instance = form.save(commit=False)

            # Ambil days dari form.cleaned_data jika ada
            days = []
            if "days" in form.cleaned_data:
                days = form.cleaned_data.get("days") or []
            else:
                # fallback: ambil dari POST (mis. ketika form manual mengirim checkbox list)
                days = request.POST.getlist("days")

            # normalisasi: simpan sebagai list of str
            try:
                instance.days = [str(d) for d in days]
            except Exception:
                instance.days = []

            instance.save()
            return redirect("bookingkelas:catalog")
        # jika form invalid, akan jatuh ke render ulang dengan errors
    else:
        form = SessionsForm()

    return render(request, "add_session.html", {"form": form})
