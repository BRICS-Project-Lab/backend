from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Country, AuditLog

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_brics_member')
    list_editable = ('is_brics_member',)
    search_fields = ('name', 'code')
    list_filter = ('is_brics_member',)

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('get_object_repr', 'content_type', 'object_id', 'action', 'performed_by', 'timestamp', 'ip_address')
    list_filter = ('action', 'timestamp', 'content_type')
    search_fields = ('performed_by__username', 'comment', 'object_id')
    readonly_fields = ('content_type', 'object_id', 'action', 'performed_by', 'timestamp', 'comment', 'old_values', 'new_values', 'ip_address')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def get_object_repr(self, obj):
        try:
            return str(obj.content_object)
        except Exception:
            return f"{obj.content_type} #{obj.object_id}"
    get_object_repr.short_description = _('Object')