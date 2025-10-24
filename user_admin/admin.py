from django.contrib import admin
from django.apps import apps
from django.db import models as dj_models

class ReadOnlyAdmin(admin.ModelAdmin):
    actions = None
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False
    def get_readonly_fields(self, request, obj=None):
        fields = [f.name for f in self.model._meta.fields]
        m2m = [m.name for m in self.model._meta.many_to_many]
        return list(set(fields + m2m))

app_config = apps.get_app_config("user_admin")

for model in app_config.get_models():
    field_names = [f.name for f in model._meta.fields]
    preferred = [n for n in ("id", "name", "title", "code", "status", "created_at", "updated_at") if n in field_names]
    fallback = [n for n in field_names if n not in preferred]
    list_display = (preferred + fallback)[:8]
    search_fields = [f.name for f in model._meta.fields if isinstance(f, (dj_models.CharField, dj_models.TextField))]
    list_filter = [f.name for f in model._meta.fields if isinstance(f, (dj_models.BooleanField, dj_models.DateField))]

    admin_class = type(
        f"{model.__name__}ReadOnlyAdmin",
        (ReadOnlyAdmin,),
        {
            "list_display": list_display,
            "search_fields": search_fields,
            "list_filter": list_filter,
            "list_select_related": True,
            "ordering": ("-id",),
        },
    )
    try:
        admin.site.register(model, admin_class)
    except admin.sites.AlreadyRegistered:
        pass
