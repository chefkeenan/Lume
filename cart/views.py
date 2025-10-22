from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.db import transaction

from .models import Cart, CartItem
from catalog.models import Product 


@login_required
def cart_page(request):
    """
    Halaman cart: menampilkan daftar item dalam cart user
    """
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = cart.items.select_related("product").all()
    context = {
        "cart": cart,
        "items": items,
        "total_items": cart.total_items(),
    }
    return render(request, "cart/cart.html", context)

@require_POST
@login_required
@transaction.atomic
def increment_item(request, item_id: int):
    """
    Tambah quantity (+1) untuk item yang sudah ada di cart
    """
    cart, _ = Cart.objects.get_or_create(user=request.user)
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    new_qty = item.quantity + 1
    cart.set_quantity(item.product, new_qty)
    return redirect("cart:page")

@require_POST
@login_required
@transaction.atomic
def decrement_item(request, item_id: int):
    """
    Kurangi quantity (-1). Jika jadi 0 -> item dihapus
    """
    cart, _ = Cart.objects.get_or_create(user=request.user)
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    new_qty = item.quantity - 1
    cart.set_quantity(item.product, new_qty)  # akan auto-delete jika <= 0
    return redirect("cart:page")

@require_POST
@login_required
@transaction.atomic
def remove_item(request, item_id: int):
    """
    Hapus satu product dari cart
    """
    cart, _ = Cart.objects.get_or_create(user=request.user)
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    cart.remove_product(item.product)
    return redirect("cart:page")

@require_POST
@login_required
@transaction.atomic
def clear_cart(request):
    """
    Kosongkan cart. (Dalam flow final, ini dipanggil modul checkout setelah sukses bayar.)
    """
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart.clear()
    return redirect("cart:page")

