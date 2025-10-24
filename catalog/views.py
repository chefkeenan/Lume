from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.http import JsonResponse, HttpResponseNotAllowed
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Product
from .forms import ProductForm
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponse, HttpResponseNotAllowed
from django.shortcuts import redirect
from catalog.models import Product

def is_admin(u): return u.is_staff

@login_required
@user_passes_test(is_admin)
@require_http_methods(["GET"])
def product_add_modal(request):
    form = ProductForm()
    html = render_to_string("catalog/_product_form.html", {"form": form, "obj": None}, request=request)
    return JsonResponse({"ok": True, "form_html": html})

@login_required
@user_passes_test(is_admin)
def product_list(request):
    products = Product.objects.all().order_by("-id")
    return render(request, "catalog/product_list.html", {"products": products})

@login_required
@user_passes_test(is_admin)
@require_http_methods(["GET"])
def product_edit_modal(request, pk):
    obj = get_object_or_404(Product, pk=pk)
    form = ProductForm(instance=obj)
    html = render_to_string("catalog/_product_form.html", {"form": form, "obj": obj}, request=request)
    return JsonResponse({"ok": True, "form_html": html})

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def product_update(request, pk):
    obj = get_object_or_404(Product, pk=pk)
    form = ProductForm(request.POST, request.FILES, instance=obj)

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        if form.is_valid():
            obj = form.save()
            return JsonResponse({"ok": True, "id": str(obj.pk)})
        return JsonResponse({"ok": False, "errors": form.errors}, status=400)

    if form.is_valid():
        form.save()
        return redirect("catalog:detail", id=obj.pk)
    return render(request, "catalog/product_detail.html", {"p": obj, "form": form})




@require_POST
def product_delete(request, pk):
    deleted, _ = Product.objects.filter(pk=pk).delete()
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return HttpResponse(status=204)

    return redirect("main:show_main")

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST", "GET"])
def product_create(request):
    form = ProductForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        obj = form.save()
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            card_html = render_to_string("product_card.html", {"p": obj}, request=request)
            return JsonResponse({"ok": True, "card_html": card_html, "id": str(obj.pk)})
        return redirect("main:show_main")
    return render(request, "catalog/add_product.html", {"form": form})


def product_detail(request, id):
    p = get_object_or_404(Product, pk=id)
    return render(request, "catalog/product_detail.html", {"p": p})