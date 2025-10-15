from rest_framework import permissions
from apps.ai_modules.models import AIModule

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Разрешение только для владельца объекта на редактирование.
    Остальные могут только читать.
    """
    
    def has_object_permission(self, request, view, obj):
        # Разрешения на чтение для всех
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Разрешения на запись только для владельца
        return obj.created_by == request.user

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Разрешение только для администраторов на запись.
    Остальные могут только читать.
    """
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return request.user.is_authenticated and request.user.is_admin()

class IsOwnerOrAdminOrReadOnly(permissions.BasePermission):
    """
    Комбинированное разрешение: владелец или администратор могут редактировать,
    остальные только читать.
    """
    
    def has_object_permission(self, request, view, obj):
        # Разрешения на чтение для всех
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Разрешения на запись для владельца или администратора
        return (
            obj.created_by == request.user or 
            (request.user.is_authenticated and request.user.is_admin())
        )

class IsAuthenticated(permissions.BasePermission):
    """
    Разрешение только для аутентифицированных пользователей.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

class IsActiveUser(permissions.BasePermission):
    """
    Разрешение только для активных (не заблокированных) пользователей.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            not request.user.is_blocked
        )

class CanModerateContent(permissions.BasePermission):
    """
    Разрешение для модерации контента (только администраторы).
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_admin() and
            not request.user.is_blocked
        )

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Разрешение для владельца объекта или администратора.
    """
    
    def has_object_permission(self, request, view, obj):
        return (
            obj.created_by == request.user or
            (request.user.is_authenticated and request.user.is_admin())
        )

class CanManageFiles(permissions.BasePermission):
    """
    Разрешение для управления файлами модуля.
    """
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Получаем модуль из URL
        ai_module_pk = view.kwargs.get('ai_module_pk')
        if ai_module_pk:
            try:
                ai_module = AIModule.objects.get(pk=ai_module_pk)
                return ai_module.can_edit(request.user)
            except AIModule.DoesNotExist:
                return False
        
        return True
