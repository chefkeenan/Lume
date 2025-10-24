from functools import wraps
from django.http import JsonResponse
from django.contrib import messages
from django.shortcuts import redirect

def block_staff_purchase(viewfunc):
    @wraps(viewfunc)
    def _wrapped(request, *args, **kwargs):
        u = getattr(request, "user", None)
        if u and (u.is_staff or u.is_superuser):
            # Jika AJAX -> JSON 403
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse(
                    {"ok": False, "error": "Admin accounts cannot make purchases."},
                    status=403
                )
            # Non-AJAX -> pakai messages lalu redirect balik
            messages.error(request, "Admin accounts cannot make purchases.")
            return redirect(request.META.get("HTTP_REFERER") or "/")
        return viewfunc(request, *args, **kwargs)
    return _wrapped