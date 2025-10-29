import csv
import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.publications.models import Publication
from apps.ai_modules.models import AIModule
from datetime import datetime
from deep_translator import GoogleTranslator


User = get_user_model()

def ru_to_en(text: str) -> str:
    if not text:
        return text
    return GoogleTranslator(source='auto', target='en').translate(text)


class Command(BaseCommand):
    help = 'Import publications from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to CSV file')
        parser.add_argument('--ai_module_id', type=int, help='ID of AI Module to link publications')

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        ai_module_id = options.get('ai_module_id')
        
        # Получить AI Module, если указан ID, иначе взять первый
        if ai_module_id:
            ai_module = AIModule.objects.get(id=ai_module_id)
        else:
            ai_module = AIModule.objects.first()
            if not ai_module:
                self.stdout.write(self.style.ERROR('No AI Modules found. Please create one first.'))
                return
        
        # Получить или создать пользователя
        try:
            user = User.objects.filter(is_superuser=True).first()
            if not user:
                user = User.objects.create_superuser(
                    username='admin',
                    email='admin@example.com',
                    password='admin'
                )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating user: {e}'))
            return
        
        if not os.path.exists(csv_file):
            self.stdout.write(self.style.ERROR(f'File not found: {csv_file}'))
            return
        
        imported_count = 0
        error_count = 0
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                try:
                    # Парсинг publication_date из publication_year
                    publication_date = None
                    if row.get('publication_year') and row['publication_year'].strip():
                        try:
                            year = int(row['publication_year'])
                            publication_date = datetime(year, 1, 1).date()
                        except ValueError:
                            pass
                    
                    added_by = user
                    
                    
                    # Создание публикации
                    publication, created = Publication.objects.get_or_create(
                        doi=row.get('doi', '').strip(),
                        defaults={
                            'ai_module': ai_module,
                            'title': row.get('title', '').strip(),
                            'authors': row.get('authors', '').strip(),
                            'journal_conference': row.get('journal_or_conference', '').strip(),
                            'publication_date': publication_date,
                            'url': row.get('url', '').strip(),
                            'added_by': added_by,
                        }
                    )
                    
                    if created:
                        imported_count += 1
                        self.stdout.write(self.style.SUCCESS(f'Imported: {publication.title}'))
                    else:
                        self.stdout.write(self.style.WARNING(f'Skipped (exists): {publication.title}'))
                
                except Exception as e:
                    error_count += 1
                    self.stdout.write(self.style.ERROR(f'Error importing row: {e}'))
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nImport completed. Imported: {imported_count}, Errors: {error_count}'
            )
        )