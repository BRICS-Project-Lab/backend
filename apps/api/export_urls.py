from django.urls import path
from . import export_views

urlpatterns = [
    # Экспорт модулей
    path('modules/', export_views.ModulesExportView.as_view(), name='export_modules'),
    path('modules/csv/', export_views.ModulesCSVExport.as_view(), name='export_modules_csv'),
    path('modules/xlsx/', export_views.ModulesXLSXExport.as_view(), name='export_modules_xlsx'),
    
    # Экспорт тегов
    path('tags/', export_views.TagsExportView.as_view(), name='export_tags'),
    
    # Экспорт публикаций
    path('publications/', export_views.PublicationsExportView.as_view(), name='export_publications'),
    
    # Экспорт статистики
    path('stats/', export_views.StatsExportView.as_view(), name='export_stats'),
]
