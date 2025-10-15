from django.urls import path
from . import views

app_name = 'common'

urlpatterns = [
    # Health check endpoint
    path('', views.health_check, name='health_check'),
    path('ping/', views.ping, name='ping'),
    
    # System information
    path('info/', views.system_info, name='system_info'),
    path('version/', views.version_info, name='version_info'),
]