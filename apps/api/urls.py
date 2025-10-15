from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from . import viewsets

# Основной роутер
router = DefaultRouter()
router.register(r'ai-modules', viewsets.AIModuleViewSet, basename='aimodule')
router.register(r'tags', viewsets.TagViewSet)
router.register(r'tag-categories', viewsets.TagCategoryViewSet)
router.register(r'publications', viewsets.PublicationViewSet)
router.register(r'users', viewsets.UserViewSet)
router.register(r'countries', viewsets.CountryViewSet)

# Вложенные роутеры для файлов модулей
modules_router = routers.NestedDefaultRouter(router, r'ai-modules', lookup='ai_module')
modules_router.register(r'files', viewsets.AIModuleFileViewSet, basename='aimodule-files')

urlpatterns = [
    # Основные API endpoints
    path('', include(router.urls)),
    path('', include(modules_router.urls)),
    
    # Дополнительные endpoints
    path('analytics/', include('apps.api.analytics_urls')),
    path('export/', include('apps.api.export_urls')),
]
