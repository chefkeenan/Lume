# checkout/views.py
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404

from .forms import CartCheckoutForm
from .models import ProductOrder, ProductOrderItem, BookingOrder, BookingOrderItem
from cart.models import Cart
from bookingkelas.models import Booking

# CART -> CHECKOUT PRODUK 
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

    user = request.user
    receiver_name = user.get_full_name() or user.username
    receiver_phone = getattr(user, "phone", "") or ""

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

#BOOKING CLASS -> CHECKOUT (single, tanpa ongkir) 
@login_required
def checkout_booking_now(request, booking_id):
    # Terima GET/POST agar kompatibel dengan redirect dari modul booking
    b = get_object_or_404(
        Booking.objects.select_related("session"),
        id=booking_id, user=request.user, is_cancelled=False
    )

    # Sudah pernah di-checkout? langsung ke confirmed (idempotent)
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

# JSON ringkasan cart, untuk AJAX
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
def order_confirmed(request):
    return render(request, "checkout/order_confirmed.html")
