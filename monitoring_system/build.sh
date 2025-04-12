#!/usr/bin/env bash
# build.sh

# Останавливаем билд, если происходит ошибка
set -o errexit

# Устанавливаем зависимости
pip install -r requirements.txt

# Применяем миграции
python manage.py migrate --noinput

# Собираем статику
python manage.py collectstatic --noinput

# Если нужно что-то дополнительное (например, очистка кэша, но это необязательно)
# python manage.py clear_cache --noinput
