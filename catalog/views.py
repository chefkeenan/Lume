from django.shortcuts import render
from .models import Product
from catalog.forms import ProductForm
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from cart.models import Cart          
from catalog.models import Product    
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.utils.html import strip_tags
import datetime

# Create your views here.
def product_to_dict(p : Product):
    return {
        'id' : p.id,
        'name': p.prodcut_name,
        'price': p.price,
        'description': p.description,
        'stock': p.stock,
        'thumbnail': p.thumbnail,
        'inStock': p.inStock,
    }

def show_json(request):
    products_list = Product.objects.all()
    data = [product_to_dict(products_list)]
    return JsonResponse(data, safe = False)

def add_product(request):
    form = ProductForm(request.POST or None)

    if form.is_valid() and request.method == 'POST':
        product_entry = form.save(commit = False)
        product_entry.user = request.user
        product_entry.save()
        return redirect('main:show_main')

    context = {
        'form': form
    }

    return render(request, "add_product.html", context)

@login_required
def add_to_cart(request, product_id):
    # ambil produk
    product = get_object_or_404(Product, pk=product_id)

    # ambil atau buat cart user
    cart, _ = Cart.objects.get_or_create(user=request.user)

    # ambil qty dari form (default 1)
    qty = int(request.POST.get("qty", 1))
    if qty < 1:
        qty = 1

    # tambahkan ke cart (pakai method kamu di models)
    cart.add(product, qty)

    return redirect("cart:page")

@login_required(login_url='/login')
@require_POST
def update_product_ajax(request, id: int):
    product = get_object_or_404(Product, pk=id)
    if product.user_id != request.user.id:
        return HttpResponseForbidden("You are not allowed to edit this item.")

    name = strip_tags((request.POST.get("name", product.name)).strip())
    description = strip_tags((request.POST.get("description", product.description)).strip())
    thumbnail = strip_tags((request.POST.get("thumbnail", product.thumbnail)).strip())

    if (pr := request.POST.get("price")) is not None:
        try:
            product.price = int(pr)
        except ValueError:
            return JsonResponse({'success': False, 'message': 'Price must be an integer.'}, status=400)


    if not name:
        return JsonResponse({'success': False, 'message': 'Name is required.'}, status=400)

    product.name = name
    product.description = description
    product.thumbnail = thumbnail
    product.save()

    return JsonResponse({'success': True, 'data': product_to_dict(product)})


@login_required(login_url='/login')
@require_POST
def delete_product_ajax(request, id: int):
    product = get_object_or_404(Product, pk=id)
    if product.user_id != request.user.id:
        return HttpResponseForbidden("You are not allowed to delete this item.")
    product.delete()
    return JsonResponse({'success': True, 'id': id})