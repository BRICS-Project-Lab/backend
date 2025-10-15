from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    extra = 0
    # Убираем readonly_fields, так как в UserProfile нет created_at и updated_at
    fields = ('bio', 'avatar', 'expertise_areas')

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'role', 'is_active', 'is_blocked', 'date_joined')
    list_filter = ('role', 'is_active', 'is_blocked')
    search_fields = ('username', 'email')
    readonly_fields = ('date_joined', 'last_login')
    inlines = [UserProfileInline]
    
    # Добавляем поля для редактирования в админке
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'organization', 'country', 'phone', 'is_blocked')
        }),
    )

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_organization', 'get_country')
    search_fields = ('user__username', 'user__organization', 'user__country')
    
    def get_organization(self, obj):
        return obj.user.organization
    get_organization.short_description = 'Organization'
    
    def get_country(self, obj):
        return obj.user.country
    get_country.short_description = 'Country'
