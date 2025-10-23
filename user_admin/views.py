from decimal import Decimal
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Sum, F, Value, CharField
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.utils.timezone import localtime

from django.conf import settings
from user.models import User
from catalog.models import Product
from cart.models import Cart
from bookingkelas.models import Booking
from checkout.models import ProductOrder, ProductOrderItem, BookingOrder, BookingOrderItem

def is_admin(u): 
    return u.is_staff

@login_required(login_url="/user/login/")
@user_passes_test(is_admin)
def dashboard(request):
    # AJAX
    return render(request, "admin_dashboard.html")

@login_required(login_url="/user/login/")
@user_passes_test(is_admin)
def api_stats(request):
    # Total income 
    prod_income = ProductOrder.objects.aggregate(s=Sum("total"))["s"] or Decimal("0")
    book_income = BookingOrder.objects.aggregate(s=Sum("total"))["s"] or Decimal("0")
    total_income = prod_income + book_income

    data = {
        "total_users": User.objects.count(),
        "total_orders": ProductOrder.objects.count(),
        "total_bookings": Booking.objects.count(),
        "total_income": f"{total_income:.2f}",
    }
    return JsonResponse({"ok": True, "data": data})

@login_required(login_url="/user/login/")
@user_passes_test(is_admin)
def api_users(request):
    q = request.GET.get("q", "").strip()
    qs = User.objects.all()
    if q:
        qs = qs.filter(username__icontains=q)

    qs = qs.annotate(
        total_orders=Count("product_orders", distinct=True),
        total_bookings=Count("bookings", distinct=True),
    ).order_by("-date_joined")[:200]

    users = [{
        "id": u.id,
        "username": u.username,
        "email": u.email,
        "phone": getattr(u, "phone", "") or "",
        "join_date": localtime(u.date_joined).strftime("%Y-%m-%d %H:%M"),
        "total_orders": u.total_orders,
        "total_bookings": u.total_bookings,
        "status": "active" if u.is_active else "inactive",
    } for u in qs]

    return JsonResponse({"ok": True, "users": users})

@login_required(login_url="/user/login/")
@user_passes_test(is_admin)
def api_orders(request):
    qs = ProductOrder.objects.prefetch_related("items", "user").order_by("-created_at")[:300]
    orders = []
    for o in qs:
        items_summary = ", ".join(f"{it.product_name} x{it.quantity}" for it in o.items.all())
        orders.append({
            "id": str(o.id),
            "user_id": o.user_id,
            "user_name": o.user.username,
            "user_email": o.user.email,
            "items": items_summary,
            "amount": f"{o.total:.2f}",
            "status": "completed",  # tidak ada field status di model, asumsikan completed
            "date": localtime(o.created_at).strftime("%Y-%m-%d %H:%M"),
        })
    return JsonResponse({"ok": True, "orders": orders})

@login_required(login_url="/user/login/")
@user_passes_test(is_admin)
def api_bookings(request):
    qs = Booking.objects.select_related("user", "session").order_by("-created_at")[:300]
    bookings = []
    for b in qs:
        s = b.session
        bookings.append({
            "id": b.id,
            "user_id": b.user_id,
            "user_name": b.user.username,
            "class_name": s.title,
            "instructor": getattr(s, "instructor", "") or "",
            "date": localtime(b.created_at).strftime("%Y-%m-%d"),
            "time": localtime(b.created_at).strftime("%H:%M"),
            "status": "cancelled" if b.is_cancelled else "completed",
        })
    return JsonResponse({"ok": True, "bookings": bookings})

@login_required(login_url="/user/login/")
@user_passes_test(is_admin)
def api_activity(request):
    orders = ProductOrder.objects.select_related("user").order_by("-created_at")[:10]
    bookings = Booking.objects.select_related("user", "session").order_by("-created_at")[:10]

    act = []
    for o in orders:
        act.append({
            "type": "order",
            "title": f"New order from {o.user.username}",
            "subtitle": f"Total Rp {int(o.total):,}".replace(",", "."),
            "status": "completed",
            "ts": localtime(o.created_at).isoformat(),
        })
    for b in bookings:
        act.append({
            "type": "booking",
            "title": f"Booking — {b.user.username}",
            "subtitle": b.session.title,
            "status": "cancelled" if b.is_cancelled else "completed",
            "ts": localtime(b.created_at).isoformat(),
        })
    act.sort(key=lambda x: x["ts"], reverse=True)
    return JsonResponse({"ok": True, "activity": act[:10]})
