from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils.html import strip_tags
from django.urls import reverse

from .models import Product
from .forms import ProductForm
from cart.models import Cart  # asumsi sudah ada

# --- Helpers ---
def product_to_dict(p: Product):
    return {
        "id": str(p.id),
        "product_name": p.product_name,
        "price": p.price,
        "description": p.description,
        "stock": p.stock,
        "thumbnail": p.thumbnail,
        "inStock": p.inStock,
    }

def show_json(request):
    products = Product.objects.all()
    data = [product_to_dict(p) for p in products]
    return JsonResponse(data, safe=False)

# --- CRUD basic (sesuaikan kebutuhan proyekmu) ---
def add_product(request):
    form = ProductForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        product_entry = form.save(commit=False)
        # HAPUS: product_entry.user = request.user (model Product tidak punya field user)
        product_entry.save()
        return redirect("main:show_main")
    return render(request, "add_product.html", {"form": form})

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    qty = int(request.POST.get("qty", 1))
    if qty < 1:
        qty = 1
    cart.add(product, qty)
    return redirect("cart:page")  # pastikan URL name ini ada

@login_required(login_url="/user/login/")  # samakan dengan app user-mu
@require_POST
def update_product_ajax(request, id: str):
    product = get_object_or_404(Product, pk=id)

    # HAPUS: cek ownership ke user karena Product tidak punya field user
    # if product.user_id != request.user.id: return HttpResponseForbidden(...)

    # Ambil field dari POST; fallback ke nilai lama
    product_name = strip_tags(request.POST.get("product_name", product.product_name)).strip()
    description  = strip_tags(request.POST.get("description", product.description)).strip()
    thumbnail    = strip_tags(request.POST.get("thumbnail", product.thumbnail)).strip()

    # price opsional
    pr_raw = request.POST.get("price")
    if pr_raw is not None:
        try:
            product.price = int(pr_raw)
        except ValueError:
            return JsonResponse({"success": False, "message": "Price must be an integer."}, status=400)

    # stock opsional
    st_raw = request.POST.get("stock")
    if st_raw is not None:
        try:
            product.stock = int(st_raw)
        except ValueError:
            return JsonResponse({"success": False, "message": "Stock must be an integer."}, status=400)

    # inStock opsional (checkbox/boolean)
    in_stock_raw = request.POST.get("inStock")
    if in_stock_raw is not None:
        # terima 'true'/'false' atau 'on'
        product.inStock = in_stock_raw.lower() in ("1", "true", "on", "yes")

    if not product_name:
        return JsonResponse({"success": False, "message": "Product name is required."}, status=400)

    product.product_name = product_name
    product.description  = description
    product.thumbnail    = thumbnail
    product.save()

    return JsonResponse({"success": True, "data": product_to_dict(product)})

@login_required(login_url="/user/login/")
@require_POST
def delete_product_ajax(request, id: str):
    product = get_object_or_404(Product, pk=id)
    # HAPUS: cek ownership; model Product tidak punya user
    product.delete()
    return JsonResponse({"success": True, "id": str(id)})

# --- Detail page ---
def product_detail(request, id):
    p = get_object_or_404(Product, pk=id)
    return render(request, "product_detail.html", {"p": p})
