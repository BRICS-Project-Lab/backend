# Dockerfile
FROM python:3.12-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    nginx \
    postgresql \
    postgresql-contrib \
    redis-server \
    certbot \
    python3-certbot-nginx \
    curl \
    supervisor \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Создание рабочей директории
WORKDIR /app

# Копирование requirements и установка Python зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY . .

# Создание пользователя для Django
RUN useradd --create-home --shell /bin/bash django && \
    chown -R django:django /app

# Создание директорий для nginx, SSL и логов
RUN mkdir -p /var/log/nginx /var/log/postgresql /var/log/redis /var/log/supervisor \
    /etc/nginx/sites-available /etc/nginx/sites-enabled /etc/letsencrypt \
    /var/lib/postgresql/data /var/run/postgresql

# Настройка PostgreSQL
RUN chown -R postgres:postgres /var/lib/postgresql /var/run/postgresql /var/log/postgresql

COPY docker/nginx.conf /etc/nginx/nginx.conf
COPY docker/default.conf /etc/nginx/sites-available/default
COPY docker/postgresql.conf /etc/postgresql/15/main/postgresql.conf
COPY docker/pg_hba.conf /etc/postgresql/15/main/pg_hba.conf
COPY docker/redis.conf /etc/redis/redis.conf
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

RUN ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/

COPY docker/init-db.sh /init-db.sh
COPY docker/start.sh /start.sh
COPY docker/start-django.sh /start-django.sh
COPY docker/ssl-setup.sh /ssl-setup.sh
RUN chmod +x /init-db.sh /start.sh /start-django.sh /ssl-setup.sh

EXPOSE 80 443 8000 5432 6379

USER root

CMD ["/start.sh"]