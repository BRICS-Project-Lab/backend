#!/bin/bash
# docker/init-db.sh

set -e

echo "Initializing PostgreSQL database..."

# Создание директорий
mkdir -p /var/lib/postgresql/data /var/run/postgresql /var/log/postgresql
chown -R postgres:postgres /var/lib/postgresql /var/run/postgresql /var/log/postgresql

# Поиск правильного пути к PostgreSQL
POSTGRES_BIN=$(find /usr -name "initdb" 2>/dev/null | head -1 | xargs dirname)
if [ -z "$POSTGRES_BIN" ]; then
    POSTGRES_BIN="/usr/bin"
fi

echo "Using PostgreSQL binaries from: $POSTGRES_BIN"

# Инициализация базы данных
su - postgres -c "$POSTGRES_BIN/initdb -D /var/lib/postgresql/data"

# Запуск PostgreSQL
su - postgres -c "$POSTGRES_BIN/pg_ctl -D /var/lib/postgresql/data -l /var/log/postgresql/postgresql.log start"

# Ожидание запуска
sleep 5

# Создание базы данных и пользователя
su - postgres -c "psql -c \"CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';\"" || true
su - postgres -c "psql -c \"CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};\"" || true
su - postgres -c "psql -c \"GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};\"" || true

echo "PostgreSQL database initialized successfully!"