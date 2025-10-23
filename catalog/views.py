from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Product
from .forms import ProductForm

def is_admin(u): return u.is_staff

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

# catalog/views.py
@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def product_update(request, pk):
    obj = get_object_or_404(Product, pk=pk)
    form = ProductForm(request.POST, request.FILES, instance=obj)

    # Balas JSON bersih untuk request AJAX
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        if form.is_valid():
            obj = form.save()
            return JsonResponse({"ok": True, "id": str(obj.pk)})
        # kirim error dalam bentuk dict: {field: [messages]}
        return JsonResponse({"ok": False, "errors": form.errors}, status=400)

    # Fallback non-AJAX (opsional)
    if form.is_valid():
        form.save()
        return redirect("catalog:detail", id=obj.pk)
    return render(request, "catalog/product_detail.html", {"p": obj, "form": form})


@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def product_delete(request, pk):
    obj = get_object_or_404(Product, pk=pk)
    obj.delete()
    return JsonResponse({"ok": True, "removed_id": str(pk)})

@login_required
@user_passes_test(is_admin)
@require_http_methods(["GET", "POST"])
def product_create(request):
    form = ProductForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        obj = form.save()
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            row_html = render_to_string("catalog/_product_row.html", {"p": obj}, request=request)
            return JsonResponse({"ok": True, "row_html": row_html})
        return redirect("main:show_main")
    return render(request, "catalog/add_product.html", {"form": form})


def product_detail(request, id):
    p = get_object_or_404(Product, pk=id)  # id adalah UUID
    return render(request, "catalog/product_detail.html", {"p": p})