# main/views.py
from django.shortcuts import render
from catalog.models import Product
from bookingkelas.models import ClassSessions, WEEKDAYS
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import JsonResponse
from django.template.loader import render_to_string

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

    # Ambil data dengan jumlah booking
    qs = (
        ClassSessions.objects
        .annotate(num_bookings=Count("bookings", distinct=True))
        .order_by("-num_bookings")
    )

    # Top 3 Daily dan Top 2 Weekly
    daily_top = qs.filter(category__iexact="daily")[:3]
    weekly_top = qs.filter(category__iexact="weekly")[:2]

    def serialize_sessions(queryset):
        data = []
        for s in queryset:
            days = s.days or []
            days_names = [weekday_map.get(str(d), str(d)) for d in days]
            data.append({
                "title": s.title,
                "instructor": s.instructor,
                "time": s.time,
                "room": s.room,
                "price": s.price,
                "capacity_current": s.capacity_current,
                "capacity_max": s.capacity_max,
                "num_bookings": s.num_bookings,
                "days_names": days_names,
                "instance_id": s.id,
            })
        return data

    context = {
        "highlights": highlights,
        "daily_classes": serialize_sessions(daily_top),
        "weekly_classes": serialize_sessions(weekly_top),
    }

    return render(request, "main/landing.html", context)


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
    
def landing_highlights(request):
    exclude = request.GET.get("exclude", "")
    exclude_ids = [int(x) for x in exclude.split(",") if x.strip().isdigit()]
    count = int(request.GET.get("count", "1"))

    qs = (Product.objects
          .filter(inStock=True)
          .exclude(id__in=exclude_ids)
          .order_by("-id"))[:count]

    cards = []
    for p in qs:
        card_html = render_to_string(
            "product_card.html",
            {"p": p, "user": request.user},
            request=request,
        )
        wrapper = f'<div class="w-[312px]" data-card-wrapper id="wrap-{p.id}">{card_html}</div>'
        cards.append(wrapper)

    return JsonResponse({"ok": True, "cards": cards, "count": len(cards)})