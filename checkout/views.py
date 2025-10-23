from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta

from .forms import CartCheckoutForm
from .models import ProductOrder, ProductOrderItem, BookingOrder, BookingOrderItem
from cart.models import Cart
from bookingkelas.models import Booking

WEEKDAY_MAP = {"mon":0,"tue":1,"wed":2,"thur":3,"fri":4,"sat":5}

# CART -> CHECKOUT PRODUK (alamat diinput tiap checkout)
@login_required
def cart_checkout_page(request):
    cart = get_object_or_404(
        Cart.objects.prefetch_related("items__product"),
        user=request.user
    )
    items = list(cart.items.all())
    subtotal = sum(ci.product.price * ci.quantity for ci in items) if items else Decimal("0")
    shipping = ProductOrder.FLAT_SHIPPING if items else Decimal("0")
    total = subtotal + shipping

    form = CartCheckoutForm()
    return render(request, "checkout/cart_checkout_page.html", {
        "form": form,
        "cart_items": items,
        "subtotal": subtotal,
        "shipping": shipping,
        "total": total,
        "payment_method": "Cash on Delivery",
    })

@login_required
def checkout_cart_create(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required.")

    form = CartCheckoutForm(request.POST)
    if not form.is_valid():
        for err in form.errors.values():
            messages.error(request, err)
        return redirect("checkout:cart_checkout_page")

    cart = get_object_or_404(
        Cart.objects.prefetch_related("items__product"),
        user=request.user
    )
    if not cart.items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect("checkout:cart_checkout_page")

    # ambil nama & telepon dari user model 
    user = request.user
    receiver_name = user.get_full_name() or user.username
    receiver_phone = user.phone or ""

    cd = form.cleaned_data

    with transaction.atomic():
        order = ProductOrder.objects.create(
            user=user,
            cart=cart,
            receiver_name=receiver_name,
            receiver_phone=receiver_phone,
            address_line1=cd["address_line1"],
            address_line2=cd.get("address_line2", ""),
            city=cd["city"],
            province=cd["province"],
            postal_code=cd["postal_code"],
            country=cd["country"],
            notes=cd.get("notes", ""),
        )

        for ci in cart.items.all():
            ProductOrderItem.objects.create(
                order=order,
                product=ci.product,
                product_name=ci.product.name,
                unit_price=ci.product.price,
                quantity=ci.quantity,
            )

        order.recalc_totals()
        order.save(update_fields=["subtotal", "shipping_fee", "total"])
        transaction.on_commit(lambda: cart.items.all().delete())

    messages.success(request, "Checkout sukses! Metode pembayaran: Cash on Delivery.")
    return redirect("checkout:order_confirmed")

# BOOKING CLASS -> CHECKOUT (single booking, tanpa alamat & ongkir)
@login_required
def checkout_booking_now(request, booking_id):
    # Terima GET/POST agar kompatibel dengan redirect dari modul booking temanmu
    b = get_object_or_404(
        Booking.objects.select_related("session"),
        id=booking_id, user=request.user, is_cancelled=False
    )

    # Jika sudah pernah di-checkout, jangan dobel
    if BookingOrderItem.objects.filter(booking=b).exists():
        messages.info(request, "Booking ini sudah pernah di-checkout.")
        return redirect("checkout:order_confirmed")

    with transaction.atomic():
        order = BookingOrder.objects.create(user=request.user, notes="")
        title = b.session.title
        if getattr(b, "day_selected", ""):
            title = f"{title} ({b.day_selected})"

        BookingOrderItem.objects.create(
            order=order,
            booking=b,
            session_title=title,
            occurrence_date=None,
            occurrence_start_time=None,
            unit_price=b.price_at_booking,
            quantity=1,
        )
        order.recalc_totals()
        order.save(update_fields=["subtotal", "total"])

    messages.success(request, "Checkout sukses! Metode pembayaran: Cash on Delivery.")
    return redirect("checkout:order_confirmed")

def order_confirmed(request):
    """
    Halaman 'Order Confirmed' generik untuk product & booking.
    Tidak menampilkan detail order; hanya ucapan sukses + tombol back to home.
    """
    return render(request, "checkout/order_confirmed.html")

@login_required
def cart_summary_json(request):
    cart = get_object_or_404(Cart.objects.prefetch_related("items__product"), user=request.user)
    items = list(cart.items.all())
    subtotal = sum(ci.product.price * ci.quantity for ci in items)
    shipping = ProductOrder.FLAT_SHIPPING if items else Decimal("0")
    total = subtotal + shipping
    return JsonResponse({
        "subtotal": float(subtotal),
        "shipping": float(shipping),
        "total": float(total),
        "count": sum(ci.quantity for ci in items),
    })

@login_required
def booking_checkout_page(request, booking_id):
    b = get_object_or_404(
        Booking.objects.select_related("session"),
        id=booking_id, user=request.user, is_cancelled=False
    )
    subtotal = b.price_at_booking
    return render(request, "checkout/booking_checkout_page.html", {
        "booking": b,
        "subtotal": subtotal,
        "total": subtotal,
        "payment_method": "Cash on Delivery",
    })

def _next_date_for_day(day_code: str):
    if not day_code or day_code not in WEEKDAY_MAP:
        return None
    today = timezone.localdate()
    target = WEEKDAY_MAP[day_code]
    days_ahead = (target - today.weekday()) % 7
    if days_ahead == 0: days_ahead = 7
    return today + timedelta(days=days_ahead)

@login_required
def my_checkouts(request):
    product_orders = (
        ProductOrder.objects.filter(user=request.user)
        .prefetch_related("items")
        .order_by("-created_at")
    )
    booking_orders = (
        BookingOrder.objects.filter(user=request.user)
        .prefetch_related("items__booking__session")
        .order_by("-created_at")
    )

    prods = [{
        "id": o.id,
        "date": o.created_at,
        "items": ", ".join(i.product_name for i in o.items.all()),
        "qty": sum(i.quantity for i in o.items.all()),
        "total": o.total,
        "status": "Completed",
    } for o in product_orders]

    classes = []
    for bo in booking_orders:
        for it in bo.items.all():
            b = it.booking
            s = b.session
            next_date = _next_date_for_day(getattr(b, "day_selected", "") or "")
            status = "Upcoming" if next_date and next_date >= timezone.localdate() else "Completed"
            title = it.session_title or s.title
            classes.append({
                "id": bo.id,
                "title": title,
                "instructor": s.instructor,
                "room": s.room,
                "time_label": s.time,
                "day_selected": getattr(b, "day_selected", ""),
                "start_date": next_date,
                "price": it.unit_price,
                "status": status,
            })

    tab = request.GET.get("tab", "products")
    return render(request, "checkout/my_checkouts.html", {
        "tab": tab,
        "product_orders": prods,
        "booking_orders": classes,
    })
