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
from django.urls import reverse

@login_required
def cart_page(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    return render(request, "cart/cart.html", {"total_items": cart.total_items()})

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
@require_POST
@login_required
@transaction.atomic
def set_quantity_ajax(request, item_id: int):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    try:
        qty = int(request.POST.get("quantity", item.quantity))
    except (TypeError, ValueError):
        return HttpResponseBadRequest("bad quantity")

    if qty <= 0:
        item.delete()
        qty = 0
    else:
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
    return JsonResponse({"ok": True, "selected_count": cart.items.filter(is_selected=True).count()})

@require_POST
@login_required
@transaction.atomic
def unselect_all_ajax(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart.items.update(is_selected=False)
    return JsonResponse({"ok": True, "selected_count": 0})

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

def add_to_cart(request, product_id):
    """
    Tambah 1 item ke cart (dipakai tombol 'Add to Cart' di kartu produk).
    Sederhana: redirect balik ke halaman sebelumnya.
    """
    product = get_object_or_404(Product, pk=product_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart.add(product, qty=1)  # is_selected=True by default (di models)
    messages.success(request, f"'{getattr(product, 'product_name', 'Produk')}' ditambahkan ke cart.")
    return redirect(request.META.get("HTTP_REFERER") or reverse("cart:page"))