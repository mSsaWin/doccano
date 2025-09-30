# Doccano Development Setup

Этот документ описывает, как запустить Doccano в режиме разработки с hot reload для бэкенда и фронтенда.

## Требования

- Docker и Docker Compose
- Git

## Быстрый старт

### 1. Клонирование репозитория

```bash
git clone https://github.com/doccano/doccano.git
cd doccano
```

### 2. Запуск в режиме разработки

```bash
# Запуск всех сервисов
docker-compose -f docker-compose.dev.yml up --build

# Или в фоновом режиме
docker-compose -f docker-compose.dev.yml up --build -d
```

### 3. Доступ к приложению

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Admin панель**: http://localhost:8000/admin
- **Flower (Celery monitoring)**: http://localhost:5555

## Структура сервисов

### Backend (Django)
- **Порт**: 8000
- **Hot reload**: ✅ Включен
- **База данных**: PostgreSQL
- **Celery**: Redis broker
- **Настройки**: `config.settings.development`

### Frontend (Nuxt.js)
- **Порт**: 3000
- **Hot reload**: ✅ Включен
- **Proxy**: Настроен на backend API

### База данных
- **PostgreSQL**: Порт 5432
- **Пользователь**: doccano
- **Пароль**: doccano
- **База данных**: doccano

### Celery
- **Worker**: Автоматический перезапуск при изменениях
- **Broker**: Redis
- **Flower**: Мониторинг задач

## Полезные команды

### Управление сервисами

```bash
# Запуск всех сервисов
docker-compose -f docker-compose.dev.yml up

# Запуск только backend
docker-compose -f docker-compose.dev.yml up backend postgres redis

# Запуск только frontend
docker-compose -f docker-compose.dev.yml up frontend

# Остановка всех сервисов
docker-compose -f docker-compose.dev.yml down

# Остановка с удалением volumes
docker-compose -f docker-compose.dev.yml down -v
```

### Работа с базой данных

```bash
# Выполнение миграций
docker-compose -f docker-compose.dev.yml exec backend python manage.py migrate

# Создание суперпользователя
docker-compose -f docker-compose.dev.yml exec backend python manage.py createsuperuser

# Доступ к базе данных
docker-compose -f docker-compose.dev.yml exec postgres psql -U doccano -d doccano
```

### Логи

```bash
# Просмотр логов всех сервисов
docker-compose -f docker-compose.dev.yml logs -f

# Просмотр логов конкретного сервиса
docker-compose -f docker-compose.dev.yml logs -f backend
docker-compose -f docker-compose.dev.yml logs -f frontend
```

## Разработка

### Hot Reload

- **Backend**: Изменения в Python файлах автоматически перезапускают Django сервер
- **Frontend**: Изменения в Vue/TypeScript файлах автоматически перезагружают страницу
- **Celery**: Изменения в задачах автоматически перезапускают worker

### Структура проекта

```
doccano/
├── backend/                 # Django приложение
│   ├── config/             # Настройки Django
│   ├── api/                # API endpoints
│   ├── projects/           # Модели проектов
│   └── ...
├── frontend/               # Nuxt.js приложение
│   ├── components/         # Vue компоненты
│   ├── pages/              # Страницы
│   └── ...
├── docker-compose.dev.yml  # Конфигурация для разработки
├── docker/
│   ├── Dockerfile.dev      # Dockerfile для backend
│   └── ...
└── frontend/
    └── Dockerfile.dev      # Dockerfile для frontend
```

### Переменные окружения

Создайте файл `.env` в корне проекта на основе `env.dev.example`:

```bash
cp env.dev.example .env
```

Основные переменные:
- `DEBUG=True` - Режим отладки Django
- `DATABASE_URL` - URL базы данных
- `CELERY_BROKER_URL` - URL Redis для Celery
- `SECRET_KEY` - Секретный ключ Django

## Отладка

### Проблемы с подключением к базе данных

```bash
# Проверка статуса PostgreSQL
docker-compose -f docker-compose.dev.yml exec postgres pg_isready -U doccano

# Проверка подключения из backend
docker-compose -f docker-compose.dev.yml exec backend python manage.py dbshell
```

### Проблемы с Celery

```bash
# Проверка статуса Redis
docker-compose -f docker-compose.dev.yml exec redis redis-cli ping

# Просмотр задач в Flower
# Откройте http://localhost:5555
```

### Проблемы с фронтендом

```bash
# Переустановка зависимостей
docker-compose -f docker-compose.dev.yml exec frontend yarn install

# Очистка кэша
docker-compose -f docker-compose.dev.yml exec frontend yarn cache clean
```

## Производственная среда

Для запуска в производственной среде используйте:

```bash
docker-compose -f docker/docker-compose.prod.yml up
```

## Дополнительная информация

- [Официальная документация Doccano](https://doccano.github.io/doccano/)
- [Django документация](https://docs.djangoproject.com/)
- [Nuxt.js документация](https://nuxtjs.org/)
- [Docker Compose документация](https://docs.docker.com/compose/)
