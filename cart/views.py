from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db import transaction
from django.http import JsonResponse, HttpResponseBadRequest
from catalog.models import Product
from .models import Cart, CartItem
from .forms import CartItemQuantityForm
from django.views.decorators.http import require_GET, require_POST
from django.middleware.csrf import get_token
from django.contrib import messages
from django.urls import reverse, NoReverseMatch
from django.shortcuts import redirect, render

def cart_page(request):
    # Kalau belum login: kirim pesan + redirect ke login dengan ?next=<url_sekarang>
    if not request.user.is_authenticated:
        messages.info(request, "Please log in to view your cart.")
        try:
            login_url = reverse("user:login")  # kalau app 'user' pakai namespace
        except NoReverseMatch:
            login_url = reverse("login")       # fallback kalau tanpa namespace
        return redirect(f"{login_url}?next={request.get_full_path()}")

    # Sudah login: render cart seperti biasa
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = cart.items.select_related("product").all()
    return render(request, "cart/cart.html", {
        "cart": cart,
        "items": items,
        "total_items": cart.total_items(),
    })

# DATA: JSON untuk render/memanipulasi DOM 
@require_GET
@login_required
def cart_json(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    qs = cart.items.select_related("product")

    selected = request.GET.get("selected")
    if selected == "1":
        qs = qs.filter(is_selected=True)
    elif selected == "0":
        qs = qs.filter(is_selected=False)

    items = []
    for it in qs:
        p = it.product
        items.append({
            "id": it.id,
            "product_name": getattr(p, "product_name", getattr(p, "name", str(p))),
            "price": getattr(p, "price", 0),
            "thumbnail": getattr(p, "thumbnail", "") or getattr(p, "image_url", ""),
            "quantity": it.quantity,
            "is_selected": it.is_selected,
        })

    return JsonResponse({
        "ok": True,
        "total_items": cart.total_items(),
        "selected_count": cart.items.filter(is_selected=True).count(),
        "items": items,
    })

# ACTIONS: quantity via AJAX POST 
from django.db.models import F
@require_POST
@login_required
@transaction.atomic
def set_quantity_ajax(request, item_id: int):
    """
    Ubah quantity item cart via AJAX.
    - Jika qty <= 0 -> hapus item.
    - Jika qty > stock produk -> tolak (400) dengan pesan error.
    """
    # Lock row supaya konsisten kalau ada update paralel
    cart, _ = Cart.objects.select_for_update().get_or_create(user=request.user)
    item = get_object_or_404(
        CartItem.objects.select_for_update().select_related("product"),
        pk=item_id, cart=cart
    )

    # Ambil target quantity dari POST
    try:
        qty = int(request.POST.get("quantity", item.quantity))
    except (TypeError, ValueError):
        return HttpResponseBadRequest("bad quantity")

    product = item.product

    # Kalau produk tidak tersedia
    if not getattr(product, "inStock", True) or product.stock <= 0:
        # Bisa pilih: hapus item / pertahankan & kasih pesan. Di sini aku hapus.
        item.delete()
        return JsonResponse({
            "ok": False,
            "reason": "out_of_stock",
            "message": "Product is out of stock.",
            "item_id": item_id,
            "quantity": 0,
            "total_items": cart.total_items(),
            "selected_count": cart.items.filter(is_selected=True).count(),
        }, status=400)

    # VALIDASI: jangan melebihi stok
    if qty > product.stock:
        return JsonResponse({
            "ok": False,
            "reason": "exceed_stock",
            "message": f"Exceeding stock. Only {product.stock} left.",
            "item_id": item_id,
            "quantity": item.quantity, 
            "available": product.stock,
            "total_items": cart.total_items(),
            "selected_count": cart.items.filter(is_selected=True).count(),
        }, status=400)

    # Hapus jika <= 0
    if qty <= 0:
        item.delete()
        return JsonResponse({
            "ok": True,
            "item_id": item_id,
            "quantity": 0,
            "total_items": cart.total_items(),
            "selected_count": cart.items.filter(is_selected=True).count(),
        })

    # Update normal
    item.quantity = qty
    item.save(update_fields=["quantity"])

    return JsonResponse({
        "ok": True,
        "item_id": item_id,
        "quantity": qty,
        "total_items": cart.total_items(),
        "selected_count": cart.items.filter(is_selected=True).count(),
    })

# ACTIONS: hapus / kosongkan 
@require_POST
@login_required
@transaction.atomic
def remove_item_ajax(request, item_id: int):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    item.delete()
    return JsonResponse({
        "ok": True,
        "item_id": item_id,
        "quantity": 0,
        "total_items": cart.total_items(),
        "selected_count": cart.items.filter(is_selected=True).count(),
    })

@require_POST
@login_required
@transaction.atomic
def clear_cart_ajax(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart.clear()
    return JsonResponse({"ok": True, "total_items": 0, "selected_count": 0})

# ACTIONS: toggle selection & bulk selection 
@require_POST
@login_required
@transaction.atomic
def toggle_select_ajax(request, item_id: int):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    val = request.POST.get("is_selected")
    if val not in ("0", "1"):
        return HttpResponseBadRequest("bad is_selected")
    item.is_selected = (val == "1")
    item.save(update_fields=["is_selected"])
    return JsonResponse({
        "ok": True,
        "item_id": item_id,
        "is_selected": item.is_selected,
        "selected_count": cart.items.filter(is_selected=True).count(),
    })

@require_POST
@login_required
@transaction.atomic
def select_all_ajax(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart.items.update(is_selected=True)
    return JsonResponse({
        "ok": True,
        "selected_count": cart.items.filter(is_selected=True).count(),
        "total_items": cart.total_items(), 
    })


@require_POST
@login_required
@transaction.atomic
def unselect_all_ajax(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart.items.update(is_selected=False)
    return JsonResponse({
        "ok": True,
        "selected_count": 0,
        "total_items": cart.total_items(), 
    })


# FORMS.PY DEMO: Edit Quantity (AJAX GET + POST)
@require_GET
@login_required
def quantity_form(request, item_id: int):
    """
    AJAX GET: kirim metadata form dalam JSON (tanpa HTML).
    Frontend yang membangun elemen <form> sendiri.
    """
    cart, _ = Cart.objects.get_or_create(user=request.user)
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    form = CartItemQuantityForm(instance=item)  

    payload = {
        "ok": True,
        "item_id": item_id,
        "action": reverse("cart:qty_form_submit", args=[item_id]),
        "csrf": get_token(request),
        "fields": {
            "quantity": {
                "name": "quantity",
                "type": "number",
                "value": form.instance.quantity,  
                "min": 0
            }
        }
    }
    return JsonResponse(payload)

@require_POST
@login_required
@transaction.atomic
def quantity_form_submit(request, item_id: int):
    """
    AJAX POST: proses ModelForm.
    - Jika invalid: kirim errors JSON (biar JS tampilkan pesan tanpa reload)
    - Jika valid: update qty / hapus item bila qty <= 0
    """
    cart, _ = Cart.objects.get_or_create(user=request.user)
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    form = CartItemQuantityForm(request.POST, instance=item)

    if not form.is_valid():
        # kirim struktur error sederhana
        return JsonResponse({"ok": False, "errors": form.errors.get_json_data()}, status=400)

    qty = form.cleaned_data["quantity"]
    if qty <= 0:
        item.delete()
        return JsonResponse({
            "ok": True,
            "deleted": True,
            "item_id": item_id,
            "quantity": 0,
            "total_items": cart.total_items(),
            "selected_count": cart.items.filter(is_selected=True).count(),
        })

    form.save(update_fields=["quantity"])
    return JsonResponse({
        "ok": True,
        "deleted": False,
        "item_id": item_id,
        "quantity": item.quantity,
        "total_items": cart.total_items(),
        "selected_count": cart.items.filter(is_selected=True).count(),
    })

@login_required
@transaction.atomic
def add_to_cart(request, product_id):
    """
    Tambah 1 unit produk ke cart dari katalog.
    Ditolak jika jumlah di cart sudah mencapai stok.
    """
    product = get_object_or_404(Product.objects.select_for_update(), pk=product_id)
    cart, _ = Cart.objects.select_for_update().get_or_create(user=request.user)

    # Cari item existing
    try:
        item = cart.items.select_for_update().get(product=product)
        if item.quantity >= product.stock:
            messages.error(request, "Exceeding stock. Quantity already at maximum available.")
        else:
            item.quantity = item.quantity + 1
            item.save(update_fields=["quantity"])
            messages.success(request, f"'{product.product_name}' added to cart.")
    except CartItem.DoesNotExist:
        if product.stock <= 0 or not getattr(product, "inStock", True):
            messages.error(request, "Product is out of stock.")
        else:
            cart.items.create(product=product, quantity=1, is_selected=True)
            messages.success(request, f"'{product.product_name}' added to cart.")

    return redirect(request.META.get("HTTP_REFERER") or reverse("cart:page"))
