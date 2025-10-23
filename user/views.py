from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.contrib.auth import logout
from django.shortcuts import render, redirect
from .forms import RegisterForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .forms import ProfileForm
from checkout.models import ProductOrder, BookingOrderItem
from django.utils import timezone

def register_user(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("main:landing")
    else:
        form = RegisterForm()
    return render(request, "register.html", {"form": form})

def login_user(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("main:landing")
    else:
        form = AuthenticationForm(request)
    return render(request, "login.html", {"form": form})

def logout_user(request):
    logout(request)
    return redirect("main:landing")

@login_required
def my_profile(request):
    user = request.user

    if request.method == "POST":
        form = ProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect("user:my_profile")
    else:
        form = ProfileForm(instance=user)
    po_qs = (
        ProductOrder.objects.filter(user=user)
        .prefetch_related("items")
        .order_by("-created_at")
    )

    product_orders = []
    for o in po_qs:
        items = list(o.items.all())
        items_summary = ", ".join(f"{it.product_name} x{it.quantity}" for it in items)
        product_orders.append({
            "created_at": o.created_at,
            "items_summary": items_summary,
            "total": o.total,
        })

    boi_qs = (
        BookingOrderItem.objects
        .filter(order__user=user)
        .select_related("booking", "order")
        .order_by("-order__created_at", "-id")
    )

    now = timezone.localtime()
    bookings = []
    for it in boi_qs:
        status = "Upcoming"
        if it.occurrence_date and it.occurrence_date < now.date():
            status = "Completed"

        bookings.append({
            "session_title": it.session_title,
            "instructor": getattr(it.booking.session, "instructor", None) if hasattr(it.booking, "session") else None,
            "date": it.occurrence_date,
            "time": it.occurrence_start_time,
            "status": status,
        })

    ctx = {
        "form": form,
        "member_since": user.date_joined,
        "orders": product_orders,
        "bookings": bookings,
    }
    return render(request, "profile.html", ctx)
