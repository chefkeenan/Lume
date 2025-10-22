from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404

from .forms import CartCheckoutForm
from .models import ProductOrder, ProductOrderItem, BookingOrder, BookingOrderItem
from cart.models import Cart
from bookingkelas.models import Booking  
from django.urls import reverse
from decimal import Decimal

# CART -> CHECKOUT PRODUK (alamat diinput tiap checkout)
# checkout/views.py (potongan perubahan)
from decimal import Decimal
# ...

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
    if request.method != "POST":
        return HttpResponseBadRequest("POST required.")

    # Ambil booking yang valid milik user (tidak dibatalkan)
    b = get_object_or_404(
        Booking.objects.select_related("session", "occurrence"),
        id=booking_id,
        user=request.user,
        is_cancelled=False
    )

    # (Opsional) jika ada occurrence, pastikan masih masa depan (safeguard)
    if b.occurrence and not b.occurrence.is_in_future():
        messages.error(request, "Occurrence sudah lewat, tidak bisa di-checkout.")
        return redirect("checkout:order_confirmed")

    with transaction.atomic():
        # Cegah double-attach (booking yang sama tidak boleh di-checkout dua kali)
        if BookingOrderItem.objects.filter(booking=b).exists():
            messages.error(request, "This booking has already been checked out.")
            return redirect("checkout:order_confirmed")

        # Buat order & snapshot item booking (tanpa ongkir)
        order = BookingOrder.objects.create(user=request.user, notes="")
        BookingOrderItem.objects.create(
            order=order,
            booking=b,
            session_title=b.session.title,
            occurrence_date=(b.occurrence.date if b.occurrence else None),
            occurrence_start_time=(b.occurrence.start_time if b.occurrence else None),
            unit_price=b.price_at_booking,
            quantity=1,  # satu booking = satu seat
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

