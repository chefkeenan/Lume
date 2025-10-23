from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from decimal import Decimal
from django.db import transaction
import re

from .models import ClassSessions, WEEKDAYS, Booking
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
            "instance_id": inst0.id,  # dipakai buat link book/choose-day
        })

    # buang duplikat daily (punyamu)
    daily_seen = set()
    filtered = []
    for g in grouped_sessions:
        if g["category"].lower() == "daily":
            if g["base_title"] not in daily_seen:
                filtered.append(g); daily_seen.add(g["base_title"])
        else:
            filtered.append(g)

    grouped_sessions = sorted(filtered, key=lambda x: (x["category"], x["time"], x["base_title"]))
    return render(request, "bookingkelas/show_class.html", {"sessions": grouped_sessions})

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
            "category_display": dict((k,v) for k,v in WEEKDAYS).get(s.category, s.category),
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

@login_required(login_url="/user/login/")
@transaction.atomic
def book_class(request, session_id):
    s = get_object_or_404(ClassSessions.objects.select_for_update(), id=session_id)

    if s.is_full:
        messages.error(request, "Kelas sudah penuh.")
        return redirect("bookingkelas:catalog")

    # larang double booking
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


def choose_day(request, base_title):
    
    sessions_in_group = ClassSessions.objects.filter(title__startswith=base_title)

    if not sessions_in_group.exists():
        messages.error(request, "Sesi kelas tidak ditemukan.")
        return redirect("bookingkelas:catalog")

    s_general = sessions_in_group.first()
    
    # TAMBAHKAN INI: Gunakan fungsi _base_title yang sudah ada
    base_title_cleaned = _base_title(s_general.title)
    
    weekday_map = _weekday_map()
    
    # 2. Buat day_options dari SEMUA sesi di grup itu
    day_options = []
    for s_item in sessions_in_group:
        # Asumsi s.days di database kamu itu ['mon'] atau ['tue']
        if s_item.days:
            day_key = s_item.days[0].lower().strip()
            day_label = weekday_map.get(day_key, day_key)
            
            # PENTING: Value-nya adalah session_id, Label-nya adalah nama hari
            # Kita juga kirim status is_full
            day_options.append({
                "value_id": s_item.id,
                "label": day_label,
                "is_full": s_item.is_full
            })

    if request.method == "POST":
        # 3. Yang di-POST sekarang bukan "day", tapi "session_id"
        selected_session_id = request.POST.get("session_id")
        if not selected_session_id:
            messages.error(request, "Pilih satu hari terlebih dahulu.")
            return redirect("bookingkelas:choose_day", base_title=base_title)
        
        # 4. Ambil sesi SPESIFIK yang dipilih user
        try:
            s_to_book = ClassSessions.objects.get(id=selected_session_id)
        except ClassSessions.DoesNotExist:
            messages.error(request, "Sesi yang dipilih tidak valid.")
            return redirect("bookingkelas:choose_day", base_title=base_title)
            
        # 5. Cek sisanya (is_full, sudah booking, dll)
        if s_to_book.is_full:
            messages.error(request, "Kelas pada hari tersebut sudah penuh.")
            return redirect("bookingkelas:choose_day", base_title=base_title)

        if Booking.objects.filter(user=request.user, session=s_to_book, is_cancelled=False).exists():
            messages.info(request, "Kamu sudah terdaftar di sesi ini.")
            return redirect("bookingkelas:catalog")

        # 6. Buat Booking
        new_booking = Booking.objects.create(
            user=request.user,
            session=s_to_book, # Pakai sesi yang spesifik
            day_selected=s_to_book.days[0], # Ambil hari dari sesi itu
            price_at_booking=Decimal(s_to_book.price),
        )
        s_to_book.capacity_current = s_to_book.bookings.filter(is_cancelled=False).count()
        s_to_book.save(update_fields=["capacity_current"])
        
        day_label_success = weekday_map.get(s_to_book.days[0], s_to_book.days[0])
        messages.success(request, f"Berhasil booking {s_to_book.title} ({day_label_success}).")
        return redirect("checkout:checkout_booking_now", booking_id=new_booking.id)

    # Kirim s_general untuk judul, dan day_options untuk pilihan radio
    return render(request, "bookingkelas/choose_day.html", {"session": s_general, "day_options": day_options,"base_title_cleaned": base_title_cleaned})

def class_list(request):
    classes = ClassSessions.objects.all().order_by("title")
    return render(request, "bookingkelas/class_list.html", {"classes": classes})

def class_edit(request, pk):
    kelas = get_object_or_404(ClassSessions, pk=pk)
    form = SessionsForm(request.POST or None, instance=kelas)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Sesi diperbarui.")
        return redirect("bookingkelas:class_list")
    return render(request, "bookingkelas/class_form.html", {"form": form})

def class_delete(request, pk):
    kelas = get_object_or_404(ClassSessions, pk=pk)
    kelas.delete()
    messages.success(request, "Sesi dihapus.")
    return redirect("bookingkelas:class_list")
