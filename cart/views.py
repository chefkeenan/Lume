# cart/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_POST, require_GET
from django.db import transaction
from django.http import JsonResponse, HttpResponseBadRequest
from django.db.models import Sum
from django.urls import reverse, NoReverseMatch
from django.contrib import messages

from .models import Cart, CartItem
from .forms import CartItemQuantityForm
from catalog.models import Product

# helpers 
def _selected_qty(cart) -> int:
    """Jumlah total quantity yang TERPILIH (is_selected=True)."""
    return cart.items.filter(is_selected=True).aggregate(q=Sum("quantity"))["q"] or 0

# page (redirect ke login kalau belum login)
def cart_page(request):
    if not request.user.is_authenticated:
        messages.info(request, "Please log in to view your cart.")
        try:
            login_url = reverse("user:login")
        except NoReverseMatch:
            login_url = reverse("login")
        return redirect(f"{login_url}?next={request.get_full_path()}")

    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = cart.items.select_related("product").all()
    return render(request, "cart/cart.html", {
        "cart": cart,
        "items": items,
        "total_items": cart.total_items(),  
    })

# data (untuk render via JS) 
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
        "message": "",
        "total_items": cart.total_items(),                         
        "selected_count": cart.items.filter(is_selected=True).count(),  
        "selected_qty": _selected_qty(cart),                      
        "items": items,
    })


# set quantity 
@require_POST
@login_required
@transaction.atomic
def set_quantity_ajax(request, item_id: int):
    cart, _ = Cart.objects.select_for_update().get_or_create(user=request.user)
    item = get_object_or_404(
        CartItem.objects.select_for_update().select_related("product"),
        pk=item_id, cart=cart
    )
    try:
        qty = int(request.POST.get("quantity", item.quantity))
    except (TypeError, ValueError):
        return HttpResponseBadRequest("bad quantity")

    product = item.product

    if not getattr(product, "inStock", True) or product.stock <= 0:
        item.delete()
        return JsonResponse({
            "ok": False,
            "reason": "out_of_stock",
            "message": "Product is out of stock.",
            "item_id": item_id,
            "quantity": 0,
            "total_items": cart.total_items(),
            "selected_count": cart.items.filter(is_selected=True).count(),
            "selected_qty": _selected_qty(cart),
        }, status=400)

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
            "selected_qty": _selected_qty(cart),
        }, status=400)

    # hapus jika <= 0
    if qty <= 0:
        item.delete()
        return JsonResponse({
            "ok": True,
            "message": "Item removed.",
            "item_id": item_id,
            "quantity": 0,
            "total_items": cart.total_items(),
            "selected_count": cart.items.filter(is_selected=True).count(),
            "selected_qty": _selected_qty(cart),
        })

    # update normal
    item.quantity = qty
    item.save(update_fields=["quantity"])
    return JsonResponse({
        "ok": True,
        "message": "Quantity updated.",
        "item_id": item_id,
        "quantity": qty,
        "total_items": cart.total_items(),
        "selected_count": cart.items.filter(is_selected=True).count(),
        "selected_qty": _selected_qty(cart),
    })

# remove / clear
@require_POST
@login_required
@transaction.atomic
def remove_item_ajax(request, item_id: int):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    item.delete()
    return JsonResponse({
        "ok": True,
        "message": "Item removed from cart. 🗑️",
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
    return JsonResponse({
        "ok": True,
        "message": "Cart cleared.",
        "total_items": 0,
        "selected_count": 0,
        "selected_qty": 0,
    })

# select / unselect 
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
        "message": "Selection updated.",
        "item_id": item_id,
        "is_selected": item.is_selected,
        "selected_count": cart.items.filter(is_selected=True).count(),
        "selected_qty": _selected_qty(cart),
    })

@require_POST
@login_required
@transaction.atomic
def select_all_ajax(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart.items.update(is_selected=True)
    return JsonResponse({
        "ok": True,
        "message": "All items selected.",
        "selected_count": cart.items.filter(is_selected=True).count(),
        "total_items": cart.total_items(),
        "selected_qty": _selected_qty(cart),
    })

@require_POST
@login_required
@transaction.atomic
def unselect_all_ajax(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart.items.update(is_selected=False)
    return JsonResponse({
        "ok": True,
        "message": "Selection cleared.",
        "selected_count": 0,
        "total_items": cart.total_items(),
        "selected_qty": 0,
    })

@login_required
@transaction.atomic
def add_to_cart(request, product_id):
    product = get_object_or_404(Product.objects.select_for_update(), pk=product_id)
    cart, _ = Cart.objects.select_for_update().get_or_create(user=request.user)

    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    def respond(ok, msg, status=200, warn=False, added=False):
        if is_ajax:
            return JsonResponse(
                {
                    "ok": ok,
                    "message": msg,
                    "warn": warn,
                    "added": added,
                    "cart_count": cart.total_items(),  
                },
                status=status,
            )
        # fallback non-AJAX 
        if ok:
            messages.success(request, msg)
        else:
            if warn:
                messages.warning(request, msg)
            else:
                messages.error(request, msg)
        return redirect(request.META.get("HTTP_REFERER") or reverse("cart:page"))

    # cek kalau produk emang udah ga bisa dibeli
    if product.stock <= 0 or not getattr(product, "inStock", True):
        return respond(
            ok=False,
            msg="Product is out of stock.",
            status=400,
        )

    # cek apakah item ini udah ada di cart
    try:
        item = cart.items.select_for_update().get(product=product)
        # stok tersisa berapa dibanding qty di cart sekarang
        remaining = product.stock - item.quantity
        if remaining <= 0:
            # jadi udah max banget
            return respond(
                ok=False,
                msg="You're already holding the last available stock for this item.",
                status=400,
                warn=True,   
                added=False,
            )

        # masih boleh nambah 1
        item.quantity = item.quantity + 1
        item.save(update_fields=["quantity"])

        # cek lagi setelah nambah, kalau sekarang pas banget nyentuh stok terakhir kasih message khusus
        now_remaining = product.stock - item.quantity
        if now_remaining <= 0:
            special_msg = f"'{product.product_name}' added to cart. That's the last one in stock!"
            return respond(
                ok=True,
                msg=special_msg,
                status=200,
                warn=False,
                added=True,
            )

        return respond(
            ok=True,
            msg=f"'{product.product_name}' added to cart.",
            status=200,
            warn=False,
            added=True,
        )

    except CartItem.DoesNotExist:
        # belum ada di cart -> tambahin qty=1
        cart.items.create(product=product, quantity=1, is_selected=True)

        # kalau stock cuma 1 total
        if product.stock == 1:
            msg = f"'{product.product_name}' added to cart. That's the last one in stock!"
        else:
            msg = f"'{product.product_name}' added to cart."

        return respond(
            ok=True,
            msg=msg,
            status=200,
            warn=False,
            added=True,
        )
