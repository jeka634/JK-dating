# JK Dating — Telegram Bot для знакомств

Современный Telegram-бот знакомств с Premium подпиской через Telegram Stars, реферальной системой и архитектурой для TON Connect.

## Стек

- Python 3.12
- aiogram 3.x
- PostgreSQL + SQLAlchemy (async)
- Alembic
- Redis
- FastAPI
- Docker & Docker Compose
- Telegram Stars API
- TON Connect (модуль)

## Возможности

- Регистрация с FSM (имя, возраст, пол, город, описание, фото)
- Просмотр анкет с лайками и матчами
- Premium через Telegram Stars
- Реферальная система
- Админ-панель (Telegram команды + REST API)
- TON кошелёк и баланс $JK
- Webhook и Polling режимы

## Структура проекта

```
/project
├── app/
│   ├── handlers/       # Обработчики бота
│   ├── middlewares/    # Middleware (DB, user, block)
│   ├── database/       # Models, repositories, session
│   ├── services/       # Business logic
│   ├── payments/       # Telegram Stars
│   ├── ton/            # TON Connect модуль
│   ├── keyboards/      # Клавиатуры
│   ├── utils/          # Утилиты, тексты, Redis
│   ├── config/         # Настройки
│   ├── states/         # FSM states
│   ├── filters/        # Фильтры
│   └── main.py         # Точка входа бота
├── web/
│   └── main.py         # FastAPI (webhook + admin API)
├── admin_panel/        # Telegram admin команды
├── alembic/            # Миграции БД
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env.example
```

## Установка

### 1. Клонирование и окружение

```bash
git clone <repo-url> jk-dating
cd jk-dating
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Настройка ENV

```bash
cp .env.example .env
```

Отредактируйте `.env`:

| Переменная | Описание |
|---|---|
| `BOT_TOKEN` | Токен бота от @BotFather |
| `BOT_USERNAME` | Username бота без @ |
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `SECRET_KEY` | Секретный ключ (мин. 32 символа) |
| `ADMIN_IDS` | Telegram ID админов через запятую |
| `ADMIN_API_KEY` | Ключ для Admin REST API |
| `BOT_MODE` | `polling` или `webhook` |
| `WEBHOOK_URL` | URL для webhook (если webhook) |
| `WEBHOOK_PATH` | Путь webhook (по умолчанию `/webhook`) |
| `WEBHOOK_SECRET` | Секрет webhook |
| `TON_API_KEY` | API ключ toncenter.com |
| `TON_NETWORK` | `mainnet` или `testnet` |
| `JK_TOKEN_CONTRACT` | Адрес контракта $JK |
| `PREMIUM_PRICE_STARS` | Цена Premium в Stars |
| `PREMIUM_DURATION_DAYS` | Длительность Premium |
| `FREE_DAILY_LIKES` | Лимит лайков для free (20) |

## Docker

### Запуск всех сервисов

```bash
cp .env.example .env
# Заполните .env

docker compose up -d postgres redis
docker compose run --rm migrate
docker compose up -d bot api
```

### Сервисы

| Сервис | Порт | Описание |
|---|---|---|
| postgres | 5432 | PostgreSQL 16 |
| redis | 6379 | Redis 7 |
| bot | — | Telegram бот (polling/webhook) |
| api | 8000 | FastAPI (webhook + admin) |
| migrate | — | Alembic миграции |

### Остановка

```bash
docker compose down
```

### Полная очистка

```bash
docker compose down -v
```

## Создание БД

### Локально (без Docker)

```sql
CREATE USER jk_user WITH PASSWORD 'jk_password';
CREATE DATABASE jk_dating OWNER jk_user;
GRANT ALL PRIVILEGES ON DATABASE jk_dating TO jk_user;
```

### Через Docker

База создаётся автоматически при первом запуске `postgres` сервиса.

## Alembic

### Применить миграции

```bash
alembic upgrade head
```

### Создать новую миграцию

```bash
alembic revision --autogenerate -m "description"
```

### Откат

```bash
alembic downgrade -1
```

## Запуск

### Polling (разработка)

```bash
# В .env
BOT_MODE=polling

python -m app.main
```

### Webhook (production)

```bash
# В .env
BOT_MODE=webhook
WEBHOOK_URL=https://your-domain.com
WEBHOOK_PATH=/webhook
WEBHOOK_SECRET=your_secret

# Запуск API (принимает webhook)
uvicorn web.main:app --host 0.0.0.0 --port 8000
```

### FastAPI Admin API

```bash
uvicorn web.main:app --host 0.0.0.0 --port 8000 --reload
```

## Настройка Telegram

1. Создайте бота через [@BotFather](https://t.me/BotFather)
2. Получите `BOT_TOKEN`
3. Установите команды:

```
start - Начать
admin - Админ панель (только для админов)
```

4. Для webhook — настройте HTTPS домен

## Настройка Telegram Stars

1. В [@BotFather](https://t.me/BotFather) включите Payments для Stars
2. Premium оплачивается через `currency="XTR"` (Telegram Stars)
3. `provider_token` оставьте пустым для Stars
4. Установите `PREMIUM_PRICE_STARS` в `.env`

### Тестирование оплаты

- Используйте тестовый режим BotFather
- После оплаты бот автоматически активирует Premium

## Настройка PostgreSQL

Connection string:

```
postgresql+asyncpg://jk_user:jk_password@localhost:5432/jk_dating
```

Для Docker:

```
postgresql+asyncpg://jk_user:jk_password@postgres:5432/jk_dating
```

## Настройка Redis

```
redis://localhost:6379/0
```

Для Docker:

```
redis://redis:6379/0
```

Redis используется для:
- FSM storage (состояния регистрации)
- Кэш просмотренных анкет
- Текущая анкета при browsing

## Настройка TON

1. Получите API ключ на [toncenter.com](https://toncenter.com)
2. Установите в `.env`:

```
TON_API_KEY=your_key
TON_NETWORK=mainnet
JK_TOKEN_CONTRACT=EQAK3lkmVshzYJeypOCtPBnE_kOJ4Nb9hwyRvQJeRDDW6HPM
```

3. В боте: Настройки → TON кошелёк → Подключить

Модуль `app/ton/` поддерживает:
- Подключение кошелька
- Проверку адреса
- Баланс $JK токена
- Архитектура для будущих платежей

## Admin API

Все запросы требуют заголовок `X-Admin-Key`.

### Endpoints

| Method | Path | Описание |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/admin/stats` | Статистика |
| GET | `/admin/users` | Список пользователей |
| DELETE | `/admin/users/{id}` | Удаление |
| POST | `/admin/users/{id}/block` | Блокировка |
| POST | `/admin/users/{id}/unblock` | Разблокировка |
| GET | `/admin/complaints` | Жалобы |
| POST | `/admin/complaints/{id}/resolve` | Решение жалобы |
| GET | `/admin/payments` | Платежи |
| GET | `/admin/logs` | Логи админов |

### Пример

```bash
curl -H "X-Admin-Key: your_key" http://localhost:8000/admin/stats
```

## Admin Telegram команды

Доступны пользователям из `ADMIN_IDS`:

- `/admin` — панель статистики
- `/users` — список пользователей
- `/complaints` — активные жалобы
- `/block ID` — блокировка
- `/unblock ID` — разблокировка
- `/delete ID` — удаление

## Premium функции

| Функция | Free | Premium |
|---|---|---|
| Лайки в день | 20 | Безлимит |
| Кто лайкнул | ❌ | ✅ |
| Фильтры | ❌ | ✅ |
| Поднятие анкеты | ❌ | ✅ |
| Скрытый режим | ❌ | ✅ |
| Повторный просмотр | ❌ | ✅ |
| История лайков | ❌ | ✅ |

## Реферальная система

Каждый пользователь получает уникальную ссылку:

```
https://t.me/BOT_USERNAME?start=ref_CODE
```

При первой покупке Premium приглашённым — реферер получает бонусные дни.

## Лицензия

MIT
