# doccano (production)

Простой пошаговый запуск prod-стека doccano на Docker Compose из локальных файлов.

## Что нужно
1) Установлен Docker и Docker Compose (команда `docker compose`).  
2) Вы в корне репозитория (где лежит папка `docker/`).

## Шаг 1. Создайте `.env`
Файл `.env` положите в папку `docker/` рядом с `docker-compose.prod.yml` (например, `docker/.env`).

Пример содержимого (значения условные, замените на свои):
```
ADMIN_USERNAME=root
ADMIN_PASSWORD=StrongPass123!
ADMIN_EMAIL=admin@example.com

POSTGRES_USER=doccano
POSTGRES_PASSWORD=DbPass123!
POSTGRES_DB=doccano_db

RABBITMQ_DEFAULT_USER=doccano
RABBITMQ_DEFAULT_PASS=RabbitPass123!

FLOWER_BASIC_AUTH=flower_user:FlowerPass123!

ALLOWED_HOSTS=app.example.com,api.example.com,localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=https://app.example.com,https://api.example.com
```
Подставьте свои значения (логины/пароли/домены).

Что значит каждая переменная:
- `ADMIN_USERNAME` / `ADMIN_PASSWORD` / `ADMIN_EMAIL` — учётка администратора, создаётся автоматически при старте backend.
- `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` — доступы к базе Postgres внутри docker-compose.
- `RABBITMQ_DEFAULT_USER` / `RABBITMQ_DEFAULT_PASS` — учётка RabbitMQ.
- `FLOWER_BASIC_AUTH` — базовая авторизация для панели Celery Flower (формат `user:pass`).
- `ALLOWED_HOSTS` — список доменов/хостов, с которых разрешён доступ к Django (перечисление через запятую).
- `CSRF_TRUSTED_ORIGINS` — список origin’ов, которым доверяется CSRF (протокол+домен, через запятую).

## Шаг 2. Запустите стек
Из корня репозитория:
```
docker compose -f docker/docker-compose.prod.yml --env-file docker/.env up -d --build
```
Что делает команда:
- Собирает backend/celery/flower из локального кода (`docker/Dockerfile.prod`).
- Собирает nginx и фронтенд из локальной `frontend/` (`docker/Dockerfile.nginx`).
- Поднимает сервисы: backend, celery, flower, nginx, postgres, rabbitmq.
- Применяет миграции, собирает статику, создаёт админа (`tools/prod-django.sh`).

## Шаг 3. Проверка статуса
```
docker compose -f docker/docker-compose.prod.yml --env-file docker/.env ps
```
Должны быть в состоянии `Up`: `backend`, `celery`, `flower`, `nginx`, `postgres`, `rabbitmq`.
Приложение открывается на http://localhost/ (nginx публикует порт 80).

## Шаг 4. Логи и ошибки
- Логи backend:  
  `docker compose -f docker/docker-compose.prod.yml --env-file docker/.env logs -f backend`
- Логи nginx:  
  `docker compose -f docker/docker-compose.prod.yml --env-file docker/.env logs -f nginx`
- Если сервис не `Up` в выводе `ps`, смотрите его логи (например, `backend`) и чините переменные в `.env` или права на порт.

## Шаг 5. Проверка админки
- Откройте http://localhost/admin/ (если используете домен/порт — подставьте свои `ALLOWED_HOSTS`/порт).
- Введите логин/пароль из переменных `ADMIN_USERNAME` / `ADMIN_PASSWORD` из `docker/.env`.
- Если страница недоступна, проверьте: контейнеры `backend` и `nginx` в состоянии `Up`, логи `backend` и `nginx`, корректность `ALLOWED_HOSTS` и `CSRF_TRUSTED_ORIGINS`.

## Шаг 6. Остановка
- Остановить контейнеры, сохранить тома:  
  `docker compose -f docker/docker-compose.prod.yml --env-file docker/.env down`
- Полностью удалить вместе с томами (сотрёт БД!):  
  `docker compose -f docker/docker-compose.prod.yml --env-file docker/.env down -v`

## Порты
- nginx: 80 (фронт + прокси на backend)
- flower: 5555 (если нужен доступ, задайте `FLOWER_BASIC_AUTH=user:pass` в `.env`)
