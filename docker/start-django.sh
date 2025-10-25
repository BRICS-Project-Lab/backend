#!/bin/bash
# docker/start-django.sh

set -e

echo "Starting Django application..."

# Ожидание PostgreSQL
echo "Waiting for PostgreSQL..."
while ! pg_isready -h localhost -p 5432 -U ${DB_USER}; do
    sleep 1
done
echo "PostgreSQL is ready!"

# Ожидание Redis
echo "Waiting for Redis..."
while ! redis-cli -h localhost -p 6379 ping; do
    sleep 1
done
echo "Redis is ready!"

# Миграции
echo "Running migrations..."
python manage.py migrate

# Сбор статики
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Создание суперпользователя (если не существует)
echo "Creating superuser..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    print('Superuser created: admin/admin')
else:
    print('Superuser already exists')
"

# Запуск Django
echo "Starting Django server..."
python manage.py runserver 127.0.0.1:8000