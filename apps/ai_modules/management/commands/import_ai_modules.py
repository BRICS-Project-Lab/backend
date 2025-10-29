import csv
import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.ai_modules.models import AIModule, AIModuleDetail
from apps.tags.models import Tag, TagCategory, AIModuleTag
from apps.publications.models import Publication
from deep_translator import GoogleTranslator
from apps.common.models import Country

def ru_to_en(text: str) -> str:
    if not text:
        return text
    return GoogleTranslator(source='auto', target='en').translate(text)


User = get_user_model()

class Command(BaseCommand):
    help = 'Import AI modules from CSV file'
    
    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to CSV file')
    
    def handle(self, *args, **options):
        csv_file = options['csv_file']
        
        # Получаем админский аккаунт
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            self.stdout.write(self.style.ERROR('No admin user found'))
            return
        
        # Создаем категории тегов
        service_type_category, _ = TagCategory.objects.get_or_create(
            name_ru='Тип сервиса (Услуги)',
            name='Type of service',
            defaults={'slug': 'service-type', 'description': 'Типы ИИ сервисов'}
        )
        
        application_area_category, _ = TagCategory.objects.get_or_create(
            name_ru='Область применения',
            name='Scope of application',
            defaults={'slug': 'application-area', 'description': 'Области применения ИИ'}
        )
        
        technology_type_category, _ = TagCategory.objects.get_or_create(
            name_ru='Тип технологии',
            name='Type of technologes',
            defaults={'slug': 'technology-type', 'description': 'Типы технологий'}
        )
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row_num, row in enumerate(reader, 1):
                try:
                    country, flag = Country.objects.get_or_create(
                        name=ru_to_en(row['Страна '].strip()),
                        name_ru=ru_to_en(row['Страна '].strip())
                    )
                    # Создаем AI модуль
                    ai_module = AIModule.objects.create(
                        name=ru_to_en(row['Название сервиса'].strip()),
                        name_ru=row['Название сервиса'].strip(),
                        company=row['Страна Разработчика'].strip(),
                        country=country,
                        status=AIModule.Status.ACTIVE,
                        params_count=10000000000,
                        license_type="MIT",
                        created_by=admin_user,
                        version=self.generate_version(),
                        task_short_description=row.get('Ключев. характеристики', '').strip()[:500]
                    )
                    
                    # Создаем детали
                    ai_module_detail = AIModuleDetail.objects.create(
                        ai_module=ai_module,
                        description=row.get('ПРИМЕЧАНИЕ', '').strip(),
                        technical_info=row.get('Ключев. характеристики', '').strip(),
                        status=row.get('Статус использования', 'used').strip(),
                        ability=row.get('Доступность', '').strip(),
                        registration_number=row.get('Регистрационный номер', '').strip()
                    )
                    
                    # Создаем теги и привязываем их
                    self.create_and_assign_tags(
                        ai_module, 
                        row.get('Тип сервиса (услуги)', '').strip(),
                        service_type_category
                    )
                    
                    self.create_and_assign_tags(
                        ai_module, 
                        row.get('Область применения', '').strip(),
                        application_area_category
                    )
                    
                    self.create_and_assign_tags(
                        ai_module, 
                        row.get('Тип технологии', '').strip(),
                        technology_type_category
                    )
                    
                    # Создаем публикацию из научной базы
                    scientific_basis = row.get('Научная база', '').strip()
                    if scientific_basis:
                        Publication.objects.create(
                            ai_module=ai_module,
                            title=scientific_basis[:500],
                            authors='',
                            journal_conference='',
                            publication_date='2024-01-01',
                            added_by=admin_user
                        )
                    
                    self.stdout.write(f'✓ Row {row_num}: {ai_module.name_ru}')
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'✗ Row {row_num}: {str(e)}')
                    )
                    continue
        
        self.stdout.write(
            self.style.SUCCESS('Import completed!')
        )
    
    def create_and_assign_tags(self, ai_module, tag_text, category):
        """Создает тег и привязывает к модулю"""
        if not tag_text:
            return
            
        # Очищаем текст тега
        tag_text = tag_text.strip()
        if not tag_text:
            return
            
        # Создаем slug для тега
        from django.utils.text import slugify
        tag_slug = slugify(tag_text)
        
        # Создаем или получаем тег
        tag, created = Tag.objects.get_or_create(
            category=category,
            slug=tag_slug,
            defaults={
                'name_ru': tag_text,
                'name':ru_to_en(tag_text),
                'description': f'Тег для {category.name_ru}',
                'is_active': True
            }
        )
        
        # Привязываем тег к модулю
        AIModuleTag.objects.get_or_create(
            ai_module=ai_module,
            tag=tag
        )
    
    def generate_version(self):
        return f"{random.randint(1, 9)}.{random.randint(0, 9)}.{random.randint(0, 9)}"