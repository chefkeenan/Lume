from django.shortcuts import render
from .models import Product
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse, HttpResponseRedirect
from django.core import serializers

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