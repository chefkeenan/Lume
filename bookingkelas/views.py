from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from .models import ClassSessions, WEEKDAYS
from .forms import SessionsForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from decimal import Decimal
from .models import Booking
import re

def _weekday_map():
    return dict(WEEKDAYS)

def _base_title(title):
    m = re.match(r"^(.*?)(?:\s*-\s*(mon|tue|wed|thur|fri|sat))?$", title, flags=re.I)
    if m:
        return m.group(1).strip()
    return title

def catalog(request):
    qs = ClassSessions.objects.all().order_by("title")
    weekday_map = _weekday_map()

    category_filter = request.GET.get("category")
    if category_filter and category_filter != "all":
        qs = qs.filter(category__iexact=category_filter)

    groups = {}
    for s in qs:
        base = _base_title(s.title)
        key = (base, s.time, s.category)

        
        days = s.days if s.days else []
        days_names = []
        for d in days:
            days_names.append(weekday_map.get(str(d), str(d)))

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
        grouped_sessions.append({
            "base_title": info["base_title"],
            "category": info["category"],
            "instructor": info["instructor"],
            "time": info["time"],
            "room": info["room"],
            "price": info["price"],
            "capacity_max": info["capacity_max"],
            "days_keys": sorted(list(info["days_keys"])),
            "days_names": sorted(list(info["days_names"])),
            "instances": info["instances"],  
        })

    daily_seen = set()
    filtered_sessions = []
    for s in grouped_sessions:
        if s["category"].lower() == "daily":
            base = s["base_title"]
            if base not in daily_seen:
                filtered_sessions.append(s)
                daily_seen.add(base)
        else:
            filtered_sessions.append(s)

    grouped_sessions = sorted(filtered_sessions, key=lambda x: (x["category"], x["time"], x["base_title"]))

    return render(request, "bookingkelas/show_class.html", {"sessions": grouped_sessions})


def sessions_json(request):
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
    if request.method == "POST":
        form = SessionsForm(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)

            days = []
            if "days" in form.cleaned_data:
                days = form.cleaned_data.get("days") or []
            else:
                days = request.POST.getlist("days")

            try:
                instance.days = [str(d) for d in days]
            except Exception:
                instance.days = []

            instance.save()
            return redirect("bookingkelas:catalog")
    else:
        form = SessionsForm()

    return render(request, "add_session.html", {"form": form})

@login_required
def book_class(request, session_id):
    session = get_object_or_404(ClassSessions, id=session_id)

    if session.is_full:
        messages.error(request, "Kelas sudah penuh.")
        return redirect("bookingkelas:catalog")

    if session.category == "daily":
        return redirect("bookingkelas:choose_day", session_id=session.id)

    # Weekly booking langsung
    booking = Booking.objects.create(
        user=request.user,
        session=session,
        price_at_booking=Decimal(session.price),
    )

    # Update kapasitas
    session.capacity_current += 1
    session.save()

    messages.success(request, f"Berhasil booking {session.title}.")
    return redirect("checkout:checkout_booking_now", booking_id=booking.id)


@login_required
def choose_day(request, session_id):
    session = get_object_or_404(ClassSessions, id=session_id)

    if session.is_full:
        messages.error(request, "Kelas sudah penuh.")
        return redirect("bookingkelas:catalog")

    if request.method == "POST":
        selected_day = request.POST.get("day")
        if not selected_day:
            messages.error(request, "Pilih satu hari terlebih dahulu.")
            return redirect("bookingkelas:choose_day", session_id=session.id)

        booking = Booking.objects.create(
            user=request.user,
            session=session,
            day_selected=selected_day,
            price_at_booking=Decimal(session.price),
        )

        # Update kapasitas
        session.capacity_current += 1
        session.save()

        messages.success(request, f"Berhasil booking {session.title} ({selected_day}).")
        return redirect("checkout:checkout_booking_now", booking_id=booking.id)

    return render(request, "bookingkelas/choose_day.html", {"session": session, "days": session.days})


def class_list(request):
    classes = ClassSessions.objects.all()
    return render(request, "bookingkelas/class_list.html", {"classes": classes})

def class_add(request):
    return redirect("bookingkelas:class_list")

def class_edit(request, pk):
    kelas = get_object_or_404(ClassSessions, pk=pk)
    form = SessionsForm(request.POST or None, instance=kelas)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("bookingkelas:class_list")
    return render(request, "bookingkelas/class_form.html", {"form": form})

def class_delete(request, pk):
    kelas = get_object_or_404(ClassSessions, pk=pk)
    kelas.delete()
    return redirect("bookingkelas:class_list")
