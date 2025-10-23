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

from django.db.models import F
from catalog.models import Product

@login_required(login_url="/user/login/")
def cart_checkout_page(request):
    cart = get_object_or_404(
        Cart.objects.prefetch_related("items__product"),
        user=request.user
    )

    # hanya item terpilih
    items_qs = cart.items.select_related("product").filter(is_selected=True)
    items = list(items_qs)

    if not items:  # tidak ada yang dipilih -> balik ke cart
        messages.error(request, "Pilih dulu item yang mau di-checkout.")
        return redirect("cart:page")

    subtotal = sum(ci.product.price * ci.quantity for ci in items)
    shipping = ProductOrder.FLAT_SHIPPING if items else Decimal("0")
    total = subtotal + shipping

    form = CartCheckoutForm()
    return render(request, "checkout/cart_checkout_page.html", {
        "form": form,
        "cart_items": items,        # hanya yang terpilih
        "subtotal": subtotal,
        "shipping": shipping,
        "total": total,
        "payment_method": "Cash on Delivery",
    })

@login_required(login_url="/user/login/")
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

    # ambil hanya item terpilih
    selected_qs = cart.items.select_related("product").filter(is_selected=True)
    if not selected_qs.exists():
        messages.error(request, "Tidak ada item yang dipilih untuk checkout.")
        return redirect("cart:page")

    user = request.user
    receiver_name = user.get_full_name() or user.username
    receiver_phone = getattr(user, "phone", "") or ""
    cd = form.cleaned_data

    with transaction.atomic():
        # 🔒 VALIDASI stok (kalau ada field stock) pakai row-level lock,
        #   tapi TANPA impor model Product (kita ambil model dari instance)
        locked = {}
        for ci in selected_qs.select_related("product"):
            # lock baris product yang bersangkutan
            PModel = type(ci.product)
            p = PModel.objects.select_for_update().get(pk=ci.product_id)
            locked[ci.product_id] = p

            # kalau model Product kamu punya field 'stock', validasi di sini
            if hasattr(p, "stock") and p.stock is not None:
                if p.stock < ci.quantity:
                    messages.error(request, f"Stok {getattr(p, 'name', getattr(p, 'product_name', 'produk'))} tidak mencukupi.")
                    return redirect("cart:page")

        # 🧾 buat order (bagian ini sama seperti punyamu)
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

        # 🧊 snapshot item + 💥 kurangi stok kalau fieldnya ada
        for ci in selected_qs:
            p = locked.get(ci.product_id, ci.product)

            ProductOrderItem.objects.create(
                order=order,
                product=ci.product,
                product_name=getattr(ci.product, "product_name", getattr(ci.product, "name", str(ci.product))),
                unit_price=ci.product.price,
                quantity=ci.quantity,
            )

            # Kurangi stok secara atomic hanya jika field 'stock' tersedia
            if hasattr(p, "stock") and p.stock is not None:
                PModel = type(p)
                PModel.objects.filter(pk=p.pk).update(stock=F("stock") - ci.quantity)

        # (opsional) matikan inStock kalau ada & stok habis
        for p in locked.values():
            if hasattr(p, "inStock"):
                p.refresh_from_db(fields=["stock"])
                if p.stock is not None and p.stock <= 0 and getattr(p, "inStock", True):
                    type(p).objects.filter(pk=p.pk).update(inStock=False)

        # hitung ulang total (sama seperti punyamu)
        order.recalc_totals()
        order.save(update_fields=["subtotal", "shipping_fee", "total"])

        # 🧹 hapus HANYA item terpilih dari cart setelah commit sukses (punyamu sudah OK)
        selected_ids = list(selected_qs.values_list("id", flat=True))
        transaction.on_commit(lambda: cart.items.filter(id__in=selected_ids).delete())

    messages.success(request, "Checkout sukses! Metode pembayaran: Cash on Delivery.")
    return redirect("checkout:order_confirmed")


#BOOKING CLASS -> CHECKOUT (single, tanpa ongkir) 
@login_required(login_url="/user/login/")
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
@login_required(login_url="/user/login/")
def cart_summary_json(request):
    cart = get_object_or_404(Cart.objects.prefetch_related("items__product"), user=request.user)

    qs = cart.items.select_related("product")
    # kalau ?selected=1, hitung hanya item terpilih
    if request.GET.get("selected") == "1":
        qs = qs.filter(is_selected=True)

    items = list(qs)
    subtotal = sum(ci.product.price * ci.quantity for ci in items)
    shipping = ProductOrder.FLAT_SHIPPING if items else Decimal("0")
    total = subtotal + shipping
    return JsonResponse({
        "subtotal": float(subtotal),
        "shipping": float(shipping),
        "total": float(total),
        "count": sum(ci.quantity for ci in items),
    })

@login_required(login_url="/user/login/")
def order_confirmed(request):
    return render(request, "checkout/order_confirmed.html")
