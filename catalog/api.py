from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from catalog.models import Product

def serialize_product(p: Product):
    return {
        "id": str(p.id),
        "name": p.product_name,
        "description": p.description,
        "price": p.price,
        "stock": p.stock,
        "in_stock": p.inStock,
        "thumbnail": p.normalized_thumbnail,
        "thumbnail_proxy": p.proxied_thumbnail,
        "external_id": p.external_id,
    }

@require_http_methods(["GET"])
def api_products(request):
    qs = Product.objects.all().order_by("-id")
    q = request.GET.get("q")
    if q:
        qs = qs.filter(product_name__icontains=q)
    limit = int(request.GET.get("limit", 50))
    offset = int(request.GET.get("offset", 0))
    data = [serialize_product(p) for p in qs[offset:offset + limit]]
    return JsonResponse({"count": qs.count(), "results": data})

@require_http_methods(["GET"])
def api_product_detail(request, pk):
    p = get_object_or_404(Product, pk=pk)
    return JsonResponse(serialize_product(p))
