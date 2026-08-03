Приложение на FastAPI/
Проект кулинария, добавление резептов.
Что есть
Таблицы:
-categories (id, title), 
-posts (id, title, content, user_id, category_id, create_at, photo, published, comments),
-users (id, name, password_hash) и sessions (hash токена, срок действия) в PostgreSQL., 
-comments (id, text, create_at, updated_at, post_id, user_id)

Сессионная авторизация с http-only cookie, хранением хэша токена и очисткой просроченных сессий.
JWT авторизация с access токенами на pyjwt; refresh — непрозрачные строки, в БД хранится только SHA-256 хэш. Оба токена дополнительно кладутся в куки (access_token, refresh_token).
Асинхронный стек: FastAPI, SQLAlchemy 2.x + asyncpg, uvicorn.
Docker Compose поднимает PostgreSQL 17 и API.

Подготовка окружения
Установите uv (через pip install uv или скрипт https://astral.sh/uv).
Поднимите Postgres 17 (по умолчанию пользователь/пароль/база — postgres).
Создайте .env с нужными значениями (см. список переменных ниже). По умолчанию DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:7432/postgres.

Локальный запуск (API + отдельный Postgres)
uv sync
docker compose up -d db  # поднимет только Postgres
uv run uvicorn auth_app.main:app --reload --host 0.0.0.0 --port 8000

Запуск целиком через Docker Compose
Compose поднимет API и PostgreSQL в одном docker compose up (API смотрит на хост db через переменную окружения, прокидываемую внутри композа).

docker compose up --build


Основные переменные окружения
DATABASE_URL (default postgresql+asyncpg://postgres:postgres@localhost:7432/postgres)
JWT_SECRET_KEY — секрет для подписи JWT
ACCESS_TOKEN_EXPIRES_MINUTES (по умолчанию 15)
REFRESH_TOKEN_EXPIRES_MINUTES (по умолчанию 43200, то есть 30 дней)
SESSION_TTL_MINUTES (по умолчанию 1440)
SESSION_EXTEND_MINUTES (rolling продление, по умолчанию 10080 = 7 дней)
SESSION_ABSOLUTE_TIMEOUT_DAYS (жесткий предел жизни сессии, по умолчанию 30 дней)
SESSION_ROLLING_INTERVAL_MINUTES (интервал проверки для продления, по умолчанию 10)
SESSION_COOKIE_NAME, SESSION_COOKIE_SECURE, SESSION_COOKIE_DOMAIN
ACCESS_COOKIE_NAME, REFRESH_COOKIE_NAME (по умолчанию access_token / refresh_token)

Маршруты
POST /auth/register — регистрация
POST /auth/login/session — логин, установка сессионной куки
POST /auth/logout/session — логаут, очистка куки и записи в БД
GET /auth/me/session — профиль по сессии
POST /auth/login/jwt — логин, выдача пары access/refresh (refresh записывается в БД, хранится хэш)
POST /auth/token/refresh — обновление пары по refresh (старый refresh гасится и заменяется новым)
GET /auth/me/jwt — профиль по access токену

Соответствено для category, posts, comments
POST - создание категории, поста или коментария
GET - вывести все категории, посты или коментраия
PUT - обновить 
DELETE - удалить
