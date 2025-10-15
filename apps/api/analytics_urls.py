from django.urls import path
from . import analytics_views

urlpatterns = [
    # Общая аналитика
    path('overview/', analytics_views.OverviewAnalyticsView.as_view(), name='analytics_overview'),
    
    # Аналитика модулей
    path('modules/', analytics_views.ModulesAnalyticsView.as_view(), name='modules_analytics'),
    path('modules/trends/', analytics_views.ModulesTrendsView.as_view(), name='modules_trends'),
    
    # Аналитика тегов
    path('tags/', analytics_views.TagsAnalyticsView.as_view(), name='tags_analytics'),
    path('tags/usage/', analytics_views.TagUsageView.as_view(), name='tag_usage'),
    
    # Аналитика пользователей
    path('users/', analytics_views.UsersAnalyticsView.as_view(), name='users_analytics'),
    path('users/activity/', analytics_views.UserActivityView.as_view(), name='user_activity'),
    
    # Аналитика по странам
    path('countries/', analytics_views.CountriesAnalyticsView.as_view(), name='countries_analytics'),
]
