from django.shortcuts import render
from catalog.models import Product
# Create your views here.

#belom kelar
def show_main(request):
    products = Product.objects.all()[:50]
    return render(request, "main.html", {"products": products})