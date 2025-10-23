from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from decimal import Decimal
from django.db import transaction
import re
from .models import ClassSessions, WEEKDAYS, Booking, CATEGORY_CHOICES
from .forms import SessionsForm

def _weekday_map():
    return dict(WEEKDAYS)

def _base_title(title):
    m = re.match(r"^(.*?)(?:\s*-\s*(mon|tue|wed|thur|fri|sat))?$", title, flags=re.I)
    return m.group(1).strip() if m else title

def catalog(request):
    qs = ClassSessions.objects.all().order_by("title")
    weekday_map = _weekday_map()

    category_filter = request.GET.get("category")
    if category_filter and category_filter != "all":
        qs = qs.filter(category__iexact=category_filter)

    # group daily/weekly (punyamu)
    groups = {}
    for s in qs:
        base = _base_title(s.title)
        key = (base, s.time, s.category)

        days = s.days or []
        days_names = [weekday_map.get(str(d), str(d)) for d in days]

        if key not in groups:
            groups[key] = {
                "base_title": base,
                "category": s.category,
                "instructor": s.instructor,
                "time": s.time,
                "room": s.room,
                "price": s.price,
                "capacity_max": s.capacity_max,
                "days_keys": set(days),
                "days_names": set(days_names),
                "instances": [s],
            }
        else:
            groups[key]["instances"].append(s)
            groups[key]["days_keys"].update(days)
            groups[key]["days_names"].update(days_names)

    grouped_sessions = []
    for (base, time, category), info in groups.items():
        inst0 = info["instances"][0]
        grouped_sessions.append({
            "base_title": info["base_title"],
            "category": info["category"],
            "instructor": info["instructor"],
            "time": info["time"],
            "room": info["room"],
            "price": info["price"],
            "capacity_current": inst0.capacity_current,
            "capacity_max": info["capacity_max"],
            "days_keys": sorted(list(info["days_keys"])),
            "days_names": sorted(list(info["days_names"])),
            "instance_id": inst0.id,  
        })
    grouped_sessions = sorted(grouped_sessions, key=lambda x: (x["category"], x["time"], x["base_title"]))
    return render(request, "bookingkelas/show_class.html", {"sessions": grouped_sessions})

@login_required(login_url="/user/login/")
def sessions_json(request):
    qs = ClassSessions.objects.all().order_by("title")
    weekday_map = _weekday_map()
    data = []
    for s in qs:
        days = s.days or []
        data.append({
            "id": s.id,
            "title": s.title,
            "category": s.category,
            "category_display": dict(CATEGORY_CHOICES).get(s.category, s.category),
            "instructor": s.instructor,
            "capacity_current": s.capacity_current,
            "capacity_max": s.capacity_max,
            "description": s.description,
            "price": s.price,
            "room": s.room,
            "days": days,
            "days_names": [weekday_map.get(str(d), str(d)) for d in days],
            "time": s.time,
            "is_full": s.is_full,
        })
    return JsonResponse({"sessions": data})

@login_required(login_url="/user/login/")
def add_session(request):
    if request.method == "POST":
        form = SessionsForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Sesi berhasil dibuat.")
            return redirect("bookingkelas:catalog")
    else:
        form = SessionsForm()
    return render(request, "bookingkelas/add_session.html", {"form": form})

def get_session_details_json(request, base_title):
    sessions_in_group = ClassSessions.objects.filter(title__startswith=base_title)
    
    if not sessions_in_group.exists():
        return JsonResponse({"error": "Sesi tidak ditemukan"}, status=404)

    s_general = sessions_in_group.first()
    base_title_cleaned = _base_title(s_general.title)
    weekday_map = _weekday_map()
    
    # 1. Buat day_options
    day_options = []
    for s_item in sessions_in_group:
        if s_item.days:
            day_key = s_item.days[0].lower().strip()
            day_label = weekday_map.get(day_key, day_key)
            day_options.append({
                "value_id": s_item.id,
                "label": day_label,
                "is_full": s_item.is_full
            })

    # 2. Siapkan data untuk dikirim sebagai JSON
    data = {
        "base_title_cleaned": base_title_cleaned,
        "instructor": s_general.instructor,
        "time": s_general.time,
        "room": s_general.room,
        "price": s_general.price,
        "description": s_general.description, # <-- Asumsi kamu mau nambahin ini
        "day_options": day_options
    }
    
    return JsonResponse(data)

@login_required(login_url="/user/login/")
@transaction.atomic
def book_class(request, session_id):
    s = get_object_or_404(ClassSessions.objects.select_for_update(), id=session_id)

    if s.is_full:
        messages.error(request, "Kelas sudah penuh.")
        return redirect("bookingkelas:catalog")

    if Booking.objects.filter(user=request.user, session=s, is_cancelled=False).exists():
        messages.info(request, "Kamu sudah terdaftar di sesi ini.")
        return redirect("bookingkelas:catalog")

    Booking.objects.create(
        user=request.user,
        session=s,
        price_at_booking=Decimal(s.price),
    )
    s.capacity_current = s.bookings.filter(is_cancelled=False).count()
    s.save(update_fields=["capacity_current"])

    messages.success(request, f"Berhasil booking {s.title}.")
    return redirect("checkout:checkout_booking_now", booking_id=s.bookings.latest('created_at').id)

@login_required(login_url="/user/login/")
def book_daily_session(request):
    
    # Logic POST kita pindah ke sini
    if request.method == "POST":
        selected_session_id = request.POST.get("session_id")
        if not selected_session_id:
            messages.error(request, "Pilih satu hari terlebih dahulu.")
            # Jika error, kembali ke katalog (karena modalnya sudah ditutup)
            return redirect("bookingkelas:catalog") 
        
        try:
            s_to_book = ClassSessions.objects.get(id=selected_session_id)
        except ClassSessions.DoesNotExist:
            messages.error(request, "Sesi yang dipilih tidak valid.")
            return redirect("bookingkelas:catalog")
            
        if s_to_book.is_full:
            messages.error(request, "Kelas pada hari tersebut sudah penuh.")
            return redirect("bookingkelas:catalog") # <-- Redirect ke katalog

        if Booking.objects.filter(user=request.user, session=s_to_book, is_cancelled=False).exists():
            messages.info(request, "Kamu sudah terdaftar di sesi ini.")
            return redirect("bookingkelas:catalog")

        # Buat Booking (sudah benar)
        new_booking = Booking.objects.create(
            user=request.user,
            session=s_to_book,
            day_selected=s_to_book.days[0],
            price_at_booking=Decimal(s_to_book.price),
        )
        s_to_book.capacity_current = s_to_book.bookings.filter(is_cancelled=False).count()
        s_to_book.save(update_fields=["capacity_current"])
        
        weekday_map = _weekday_map()
        day_label_success = weekday_map.get(s_to_book.days[0], s_to_book.days[0])
        messages.success(request, f"Berhasil booking {s_to_book.title} ({day_label_success}).")
        return redirect("checkout:checkout_booking_now", booking_id=new_booking.id)

    # Jika ada yang akses via GET, lempar ke katalog
    return redirect("bookingkelas:catalog")


@login_required(login_url="/user/login/")
def class_list(request):
    classes = ClassSessions.objects.all().order_by("title")
    return render(request, "bookingkelas/class_list.html", {"classes": classes})

@login_required(login_url="/user/login/")
def class_edit(request, pk):
    kelas = get_object_or_404(ClassSessions, pk=pk)
    form = SessionsForm(request.POST or None, instance=kelas)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Sesi diperbarui.")
        return redirect("bookingkelas:class_list")
    return render(request, "bookingkelas/class_form.html", {"form": form})

@login_required(login_url="/user/login/")
def class_delete(request, pk):
    kelas = get_object_or_404(ClassSessions, pk=pk)
    kelas.delete()
    messages.success(request, "Sesi dihapus.")
    return redirect("bookingkelas:class_list")
