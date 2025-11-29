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
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

def _is_ajax(request):
    return (
        request.POST.get("ajax") == "1" or
        request.headers.get("x-requested-with") == "XMLHttpRequest"
    )


def _safe_next(request, fallback_name="main:landing"):
    nxt = (request.POST.get("next") or request.GET.get("next") or "").strip()
    try:
        login_path = reverse("user:login")
    except Exception:
        login_path = "/user/login/"
    if not nxt or nxt == request.path or nxt == login_path:
        return reverse(fallback_name)
    return nxt

@csrf_exempt
@require_http_methods(["GET", "POST"])
def login_user(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            target = _safe_next(request)

            if _is_ajax(request):
                return JsonResponse({
                    "ok": True,
                    "redirect_url": target,
                    "message": "Log in successful."
                })
            messages.success(request, "Log in successful.")
            return redirect(target)
        else:
            if _is_ajax(request):   
                errors = {k: v for k, v in form.errors.items()}
                nfe = list(form.non_field_errors())
                if nfe:
                    errors["__all__"] = nfe
                return JsonResponse({"ok": False, "errors": errors}, status=400)

            return render(request, "login.html", {
                "form": form,
                "non_field_errors": form.non_field_errors(),
            })
    else:
        form = AuthenticationForm(request)
    return render(request, "login.html", {"form": form})

@csrf_exempt
@require_http_methods(["GET", "POST"])
def register_user(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()

            login(request, user, backend=settings.AUTHENTICATION_BACKENDS[0])

            if _is_ajax(request):
                return JsonResponse({
                    "ok": True,
                    "redirect_url": reverse("main:landing"),
                    "message": "Registration successful."
                })
            messages.success(request, "Registration successful.")
            return redirect("main:landing")
        else:
            if _is_ajax(request):
                return JsonResponse(
                    {
                        "ok": False,
                        "errors": form.errors,
                        "non_field_errors": form.non_field_errors(),
                    },
                    status=400
                )
    else:
        form = RegisterForm()
    return render(request, "register.html", {"form": form})

@csrf_exempt
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
        line_items = []
        for it in o.items.all():
            price = getattr(it, "price", None)
            if price is None:
                price = getattr(it, "unit_price", 0)

            qty = int(getattr(it, "quantity", 0) or 0)

            line_total = getattr(it, "line_total", None)
            if line_total is not None:
                subtotal = int(line_total)
            else:
                try:
                    subtotal = int(qty * float(price))
                except Exception:
                    subtotal = 0

            name = getattr(it, "product_name", None)
            if not name and getattr(it, "product", None):
                name = getattr(it.product, "product_name", "-")

            line_items.append({
                "name": name or "-",
                "qty": qty,
                "price": int(float(price) if price is not None else 0),
                "subtotal": subtotal,
            })

        product_orders.append({
            "id": o.id,
            "created_at": o.created_at,
            "total": int(float(o.total) if o.total is not None else 0),
            "line_items": line_items,
        })

    product_orders.sort(key=lambda x: x["created_at"], reverse=True)

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
