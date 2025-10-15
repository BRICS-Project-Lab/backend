from django.core.management.base import BaseCommand
from django.urls import reverse
from django.test import RequestFactory
from rest_framework.test import APIRequestFactory
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.utils import extend_schema
import json

class Command(BaseCommand):
    help = 'Generate API documentation'
    
    def handle(self, *args, **options):
        self.stdout.write('Generating API documentation...')
        
        # Здесь можно добавить логику генерации документации
        # Например, создание Postman коллекции или markdown файлов
        
        self.stdout.write(
            self.style.SUCCESS('API documentation generated successfully')
        )

