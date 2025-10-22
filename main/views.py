from django.shortcuts import render
from catalog.models import Product
# Create your views here.

#belom kelar
def show_main(request):
    filter_type = request.GET.get("filter", "all")  # default 'all'

    if filter_type == "all":
        products_list = Product.objects.all()
    else:
        products_list = Product.objects.filter(user=request.user)
    context = {
        'products_list': products_list,
    }

    return render(request, "main.html", context)