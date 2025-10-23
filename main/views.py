# main/views.py
from django.shortcuts import render
from catalog.models import Product
from bookingkelas.models import ClassSessions, WEEKDAYS
from django.core.paginator import Paginator
from django.db.models import Count, Q

PRICE_RANGES = [
    ("0-200k", "≤ Rp200.000", 0, 200_000),
    ("200k-500k", "Rp200.000 – Rp500.000", 200_000, 500_000),
    ("500k-1m", "Rp500.000 – Rp1.000.000", 500_000, 1_000_000),
    ("1m-2m", "Rp1.000.000 – Rp2.000.000", 1_000_000, 2_000_000),
    ("2m-5m", "Rp2.000.000 – Rp5.000.000", 2_000_000, 5_000_000),
    ("5m+", "≥ Rp5.000.000", 5_000_000, None),
]

def _weekday_map():
    return dict(WEEKDAYS)

def _base_title(title):
    import re
    m = re.match(r"^(.*?)(?:\s*-\s*(mon|tue|wed|thur|fri|sat))?$", title, flags=re.I)
    return m.group(1).strip() if m else title

def landing_view(request):
    highlights = Product.objects.all().order_by("-id")[:8]
    weekday_map = _weekday_map()

    # Ambil semua sesi dan hitung jumlah booking
    qs = (
        ClassSessions.objects
        .annotate(num_bookings=Count("bookings", distinct=True))
        .order_by("-num_bookings", "category", "time")
    )

    # === Kelompokkan daily/weekly berdasarkan base title dan waktu ===
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
                "capacity_current": s.capacity_current,
                "capacity_max": s.capacity_max,
                "num_bookings": s.num_bookings,
                "days_keys": set(days),
                "days_names": set(days_names),
                "instances": [s],
                "instance_id": s.id,
            }
        else:
            groups[key]["instances"].append(s)
            groups[key]["days_keys"].update(days)
            groups[key]["days_names"].update(days_names)
            groups[key]["num_bookings"] += s.num_bookings

    grouped = list(groups.values())

    # === Pisahkan daily dan weekly ===
    daily_classes = [g for g in grouped if g["category"] == "daily"]
    weekly_classes = [g for g in grouped if g["category"] == "weekly"]

    # Urutkan berdasarkan popularitas (num_bookings)
    daily_sorted = sorted(daily_classes, key=lambda x: x["num_bookings"], reverse=True)[:3]
    weekly_sorted = sorted(weekly_classes, key=lambda x: x["num_bookings"], reverse=True)[:2]

    sessions = daily_sorted + weekly_sorted

    return render(request, "main/landing.html", {
        "highlights": highlights,
        "sessions": sessions,
    })


def show_main(request):
    q = (request.GET.get("q") or "").strip()                 
    qs = Product.objects.all().order_by("-id")

    # SEARCH 
    if q:
        qs = qs.filter(
            Q(product_name__icontains=q) |
            Q(description__icontains=q)
        )

    # filter harga: single-select via dropdown
    selected_price = request.GET.get("price", "")
    if selected_price:
        for key, _label, lo, hi in PRICE_RANGES:
            if key == selected_price:
                if lo is not None:
                    qs = qs.filter(price__gte=lo)
                if hi is not None:
                    qs = qs.filter(price__lt=hi)
                break

    # sort (opsional)
    order = request.GET.get("order")
    if order in {"price", "-price"}:
        qs = qs.order_by(order, "-id")  # stabilkan dengan -id kedua

    # pagination
    paginator = Paginator(qs, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "main.html", {
        "page_obj": page_obj,
        "price_ranges": PRICE_RANGES,
        "selected_price": selected_price,
        "order": order or "",
        "q": q,                                  
        "total_found": qs.count(),               
    })
