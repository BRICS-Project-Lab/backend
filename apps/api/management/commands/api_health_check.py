from django.core.management.base import BaseCommand
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate
from apps.api.viewsets import AIModuleViewSet
import time

User = get_user_model()

class Command(BaseCommand):
    help = 'Check API health and performance'
    
    def handle(self, *args, **options):
        self.stdout.write('Checking API health...')
        
        factory = APIRequestFactory()
        
        # Тест базового endpoint
        start_time = time.time()
        request = factory.get('/api/v1/ai-modules/')
        view = AIModuleViewSet.as_view({'get': 'list'})
        response = view(request)
        end_time = time.time()
        
        self.stdout.write(f'AI Modules list endpoint: {response.status_code}')
        self.stdout.write(f'Response time: {(end_time - start_time):.3f}s')
        
        if response.status_code == 200:
            self.stdout.write(
                self.style.SUCCESS('✓ API is healthy')
            )
        else:
            self.stdout.write(
                self.style.ERROR('✗ API health check failed')
            )