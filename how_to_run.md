## Как запустить (production, Docker Compose)

### 1) Подготовка окружения
- Установите Docker и Docker Compose.
- Клонируйте репозиторий и перейдите в корень проекта.

Создайте файл `.env` (рядом с `docker/docker-compose.prod.yml`) со значениями переменных:

```bash
# Обязательные учётные данные для авто-создания администратора
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change-me
ADMIN_EMAIL=admin@example.com

# База данных
POSTGRES_USER=doccano
POSTGRES_PASSWORD=change-me
POSTGRES_DB=doccano

# RabbitMQ
RABBITMQ_DEFAULT_USER=doccano
RABBITMQ_DEFAULT_PASS=change-me

# Безопасность/доступ
ALLOWED_HOSTS=*
CSRF_TRUSTED_ORIGINS=http://localhost
```

> Примечание: backend сам выполнит миграции, соберёт статику и создаст админа на старте (см. `tools/prod-django.sh`).

### 2) Сборка и запуск

```bash
# Сборка образов и запуск в фоне
docker compose -f docker/docker-compose.prod.yml up -d --build

# Проверка статуса контейнеров
docker compose -f docker/docker-compose.prod.yml ps
```

После старта приложение будет доступно на http://localhost/ (nginx публикует порт 80).

### 3) Полезные команды

```bash
# Логи backend
docker compose -f docker/docker-compose.prod.yml logs -f backend

# Логи nginx
docker compose -f docker/docker-compose.prod.yml logs -f nginx

# Перезапуск отдельного сервиса
docker compose -f docker/docker-compose.prod.yml restart nginx

# Остановка всего стека
docker compose -f docker/docker-compose.prod.yml down
```

---

## Обновление только фронтенда без пересборки образа
Иногда быстрее собрать фронтенд локально и «подложить» его в работающий контейнер nginx.

**Помогает при ошибках в билдах!**

### Шаги
1) Соберите фронтенд локально:

```bash
cd frontend
yarn install --frozen-lockfile
yarn build
cd ..
```

2) Скопируйте результат сборки в контейнер nginx:

```bash
# Имя контейнера по умолчанию: doccano-prod-nginx-1
docker cp frontend/dist/. doccano-prod-nginx-1:/var/www/html/
```

3) Перезапустите nginx (чтобы отдать новые файлы из кэша корректно):

```bash
docker compose -f docker/docker-compose.prod.yml restart nginx
```

> Если у вас другое имя контейнера (например, из‑за нестандартного project‑name), узнайте его через `docker ps` и подставьте в команду `docker cp`.

---

## Альтернатива: пересборка nginx с фронтендом внутри
Чтобы получить «чистую» сборку без ручного копирования файлов, пересоберите только nginx:

```bash
docker compose -f docker/docker-compose.prod.yml build nginx
docker compose -f docker/docker-compose.prod.yml up -d nginx
```

Это запустит этап сборки фронтенда внутри Docker (см. `docker/Dockerfile.nginx`) и обновит контейнер.