# main/views.py
from django.shortcuts import render
from django.db.models import Q
from catalog.models import Product
from bookingkelas.models import ClassSessions, WEEKDAYS

PRICE_RANGES = [
    ("0-200k", "≤ Rp200.000",               0,        200_000),
    ("200k-500k", "Rp200.000 – Rp500.000",  200_000,  500_000),
    ("500k-1m", "Rp500.000 – Rp1.000.000",  500_000,  1_000_000),
    ("1m-2m", "Rp1.000.000 – Rp2.000.000",  1_000_000, 2_000_000),
    ("2m-5m", "Rp2.000.000 – Rp5.000.000",  2_000_000, 5_000_000),
    ("5m+", "≥ Rp5.000.000",                5_000_000, None),
]

def _weekday_map():
    return dict(WEEKDAYS)

def landing_view(request):
    highlights = Product.objects.all().order_by("-id")[:8]
    weekday_map = _weekday_map()
    sessions_qs = ClassSessions.objects.all().order_by("category", "time")[:4]
    sessions = []
    for s in sessions_qs:
        days = s.days or []
        days_names = [weekday_map.get(str(d), str(d)) for d in days]
        sessions.append({
            "id": s.id,
            "title": s.title,
            "category": s.category,            # "daily" / "weekly"
            "instructor": s.instructor,
            "time": s.time,
            "capacity_current": s.capacity_current,
            "capacity_max": s.capacity_max,
            "price": s.price,
            "days_names": days_names,
        })

    return render(request, "main/landing.html", {
        "highlights": highlights,
        "sessions": sessions,
    })


def show_main(request):
    qs = Product.objects.all()

    # ambil beberapa checkbox price: /?price=0-200k&price=5m+
    selected = set(request.GET.getlist("price"))

    if selected:
        q = Q()
        for key, _label, min_v, max_v in PRICE_RANGES:
            if key in selected:
                if min_v is not None and max_v is not None:
                    q |= Q(price__gte=min_v, price__lte=max_v)
                elif min_v is not None and max_v is None:
                    q |= Q(price__gte=min_v)
                elif min_v is None and max_v is not None:
                    q |= Q(price__lte=max_v)
        qs = qs.filter(q)

    # opsional: sorting harga (termurah / termahal)
    order = request.GET.get("order")
    if order in {"price", "-price"}:
        qs = qs.order_by(order)

    # siapkan context price ranges + status checked
    price_ranges_ctx = [
        {"key": key, "label": label, "checked": (key in selected)}
        for key, label, _min_v, _max_v in PRICE_RANGES
    ]

    ctx = {
        "products": qs,
        "PRICE_RANGES": price_ranges_ctx,
    }
    return render(request, "main.html", ctx)  # sesuaikan nama template
