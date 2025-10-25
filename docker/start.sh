#!/bin/bash
# docker/start.sh

set -e

echo "Starting BRICS Backend with PostgreSQL and Redis..."

# Создание пользователя redis (если не существует)
if ! id "redis" &>/dev/null; then
    useradd -r -s /bin/false redis
fi

# Создание необходимых директорий
mkdir -p /var/lib/redis /var/log/redis /var/run/redis
chown -R redis:redis /var/lib/redis /var/log/redis /var/run/redis

# Создание директории для PostgreSQL
mkdir -p /var/lib/postgresql/data /var/run/postgresql
chown -R postgres:postgres /var/lib/postgresql /var/run/postgresql /var/log/postgresql

# Инициализация базы данных (если не существует)
if [ ! -f /var/lib/postgresql/data/PG_VERSION ]; then
    echo "Initializing PostgreSQL database..."
    /init-db.sh
else
    echo "PostgreSQL database already exists, starting..."
    # Поиск правильного пути к PostgreSQL
    POSTGRES_BIN=$(find /usr -name "pg_ctl" 2>/dev/null | head -1 | xargs dirname)
    if [ -z "$POSTGRES_BIN" ]; then
        POSTGRES_BIN="/usr/bin"
    fi
    su - postgres -c "$POSTGRES_BIN/pg_ctl -D /var/lib/postgresql/data -l /var/log/postgresql/postgresql.log start"
fi

# Запуск Redis
echo "Starting Redis..."
redis-server /etc/redis/redis.conf &

# Настройка SSL (если указан домен)
if [ ! -z "$DOMAIN_NAME" ]; then
    echo "Setting up SSL for domain: $DOMAIN_NAME"
    /ssl-setup.sh
fi

# Запуск всех сервисов через supervisor
echo "Starting all services..."
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf