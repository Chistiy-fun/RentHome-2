# 🏠 RentHome — Сервис аренды домов через Telegram-бота

Полноценный production-ready проект на **Django + aiogram 3** с Docker.

---

## 📁 Структура проекта

```
RentHome/
├── backend/                    # Django + DRF
│   ├── apps/
│   │   ├── users/              # Telegram-пользователи, реферальная система
│   │   ├── houses/             # Дома, фото, услуги, теги
│   │   ├── bookings/           # Бронирования, расчёт цен
│   │   ├── payments/           # Платежи
│   │   ├── promos/             # Промокоды
│   │   └── referrals/          # (логика в apps/users/services.py)
│   ├── renthome/               # Django settings, URLs
│   ├── services/               # Общие утилиты (при необходимости)
│   ├── requirements.txt
│   ├── Dockerfile
│   └── entrypoint.sh
│
├── bot/                        # aiogram 3 Telegram-бот
│   ├── handlers/
│   │   ├── start.py            # /start, реферальная ссылка
│   │   ├── houses.py           # Список домов, карточка, FSM бронирования
│   │   ├── bookings.py         # Мои брони, оплата, заезд, отмена
│   │   ├── support.py          # Поддержка → форвард админу
│   │   └── states.py           # FSM States
│   ├── keyboards/
│   │   └── keyboards.py        # Все клавиатуры
│   ├── services/
│   │   ├── api.py              # HTTP-клиент для Django API
│   │   └── notifications.py    # Уведомления + планировщик напоминаний
│   ├── main.py                 # Точка входа бота
│   ├── requirements.txt
│   └── Dockerfile
│
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🚀 Быстрый старт

### 1. Клонировать и настроить окружение

```bash
git clone <repo>
cd RentHome

# Создать .env из примера
cp .env.example .env
```

### 2. Заполнить `.env`

Откройте `.env` и укажите:

```env
BOT_TOKEN=токен_от_BotFather
ADMIN_TELEGRAM_ID=ваш_telegram_id
BOT_USERNAME=имя_вашего_бота
DJANGO_SECRET_KEY=длинная_случайная_строка
```

### 3. Запустить одной командой

```bash
docker-compose up --build
```

После старта:
- Django backend: **http://localhost:8000**
- Django Admin: **http://localhost:8000/admin/** (логин: `admin`, пароль: `admin123`)
- Бот запустится автоматически и начнёт polling

---

## ⚙️ Настройка Telegram Payments

### Тестовый режим (по умолчанию, MOCK_PAYMENTS=true)

По умолчанию реальных платежей **нет** — при нажатии "Оплатить" деньги сразу помечаются как оплаченные. Удобно для разработки.

### Реальные тестовые платежи через Stripe TEST

1. В @BotFather: **Payments → Connect Stripe TEST**
2. Пройдите авторизацию Stripe
3. Получите тестовый provider token вида `1744374395:TEST:...`
4. Добавьте в `.env`:
   ```env
   TELEGRAM_PAYMENT_PROVIDER_TOKEN=1744374395:TEST:ваш_токен
   MOCK_PAYMENTS=false
   ```
5. Перезапустите: `docker-compose restart bot`

Для тестовой оплаты используйте карту: `4242 4242 4242 4242`.

---

## 🤖 Функционал бота

### Главное меню
| Кнопка | Описание |
|--------|----------|
| 🏠 Найти дом | Список доступных домов с пагинацией |
| 📖 Мои брони | История бронирований и управление |
| ℹ️ Поддержка | Отправка сообщения администратору |

### Процесс бронирования
```
/start → Главное меню
  → 🏠 Найти дом → список → /house_N → карточка с фото
    → 📅 Забронировать
      → ввод даты заезда (ДД.ММ.ГГГГ)
      → ввод даты выезда
      → выбор доп. услуг (чекбоксы)
      → промокод (опционально)
      → итоговая цена + подтверждение
        → создание брони (даты блокируются)
        → 💳 Оплатить предоплату (10%)
          → статус: partially_paid
          → 📍 Я на месте
            → 💳 Оплатить остаток
              → статус: paid
              → 🔑 Код доступа выдаётся
```

### Реферальная система
- `/referral` — ваша ссылка вида `t.me/БОТ?start=ref_КОД`
- Новый пользователь по ссылке → **25% скидка** (одноразово)
- Реферер получает накопительную скидку после каждой успешной оплаты:
  - 1–2 реферала → 2%
  - 3–5 → 5%
  - 6–10 → 10%
  - 10+ → 15%

---

## 📡 REST API

Base URL: `http://localhost:8000/api/`

### Пользователи

| Метод | Путь | Описание |
|-------|------|----------|
| `POST` | `/users/register/` | Регистрация / авторизация по telegram_id |
| `GET` | `/users/by-telegram-id/{id}/` | Получить пользователя по TG ID |
| `GET` | `/users/` | Список всех пользователей |

**Пример — регистрация:**
```bash
curl -X POST http://localhost:8000/api/users/register/ \
  -H 'Content-Type: application/json' \
  -d '{"telegram_id": 123456789, "username": "ivan", "full_name": "Иван Иванов"}'
```

### Дома

| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/houses/` | Список активных домов (пагинация) |
| `GET` | `/houses/{id}/` | Карточка дома |
| `GET` | `/houses/{id}/services/` | Услуги дома |
| `GET` | `/houses/{id}/availability/` | Занятые даты |

**Пример — список домов:**
```bash
curl http://localhost:8000/api/houses/?page=1
```

### Бронирования

| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/bookings/?telegram_id=123` | Брони пользователя |
| `POST` | `/bookings/` | Создать бронь |
| `GET` | `/bookings/{id}/` | Детали брони |
| `POST` | `/bookings/calculate-price/` | Предварительный расчёт цены |
| `POST` | `/bookings/{id}/cancel/` | Отменить бронь |
| `POST` | `/bookings/{id}/admin-cancel/` | Отменить (админ) |
| `POST` | `/bookings/{id}/checkin/` | Заезд ("Я на месте") |

**Пример — создание брони:**
```bash
curl -X POST http://localhost:8000/api/bookings/ \
  -H 'Content-Type: application/json' \
  -d '{
    "telegram_id": 123456789,
    "house_id": 1,
    "start_date": "2025-07-01",
    "end_date": "2025-07-07",
    "service_ids": [1, 2],
    "promo_code": "SUMMER10"
  }'
```

**Пример — расчёт цены:**
```bash
curl -X POST http://localhost:8000/api/bookings/calculate-price/ \
  -H 'Content-Type: application/json' \
  -d '{
    "telegram_id": 123456789,
    "house_id": 1,
    "start_date": "2025-07-01",
    "end_date": "2025-07-07",
    "service_ids": [],
    "promo_code": ""
  }'
```

### Платежи

| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/payments/?telegram_id=123` | История платежей |
| `POST` | `/payments/process/` | Обработать платёж |

**Пример — подтверждение предоплаты:**
```bash
curl -X POST http://localhost:8000/api/payments/process/ \
  -H 'Content-Type: application/json' \
  -d '{
    "booking_id": 1,
    "telegram_id": 123456789,
    "payment_type": "prepayment",
    "telegram_payment_id": "TG_CHARGE_ID"
  }'
```

### Промокоды

| Метод | Путь | Описание |
|-------|------|----------|
| `POST` | `/promos/check/` | Проверить промокод |

```bash
curl -X POST http://localhost:8000/api/promos/check/ \
  -H 'Content-Type: application/json' \
  -d '{"code": "SUMMER10"}'
```

---

## 🛠 Django Admin

Доступен по адресу: **http://localhost:8000/admin/**

Логин/пароль (создаются автоматически): `admin` / `admin123`

### Возможности:
- **Дома** — добавление/редактирование, загрузка фото (через inline), услуги
- **Бронирования** — просмотр, отмена с причиной, bulk-отмена
- **Пользователи** — история, скидки, рефералы
- **Платежи** — только просмотр (изменение статусов через API)
- **Промокоды** — создание, активация/деактивация

---

## 🔔 Уведомления

Напоминания работают через встроенный asyncio-цикл в боте (без Celery):
- **За 1 день до заезда** — напоминание пользователю
- **В день заезда** — напоминание нажать "Я на месте"
- **После создания брони** — подтверждение
- **После оплаты** — квитанция + код доступа (при полной)
- **При отмене** — уведомление с причиной

---

## 🧪 Разработка без Docker

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
mkdir -p db
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

# Bot (в другом терминале)
cd bot
pip install -r requirements.txt
BOT_TOKEN=ваш_токен BACKEND_URL=http://localhost:8000 python main.py
```

---

## 📝 Примечания

- **База данных**: SQLite (файл `backend/db/db.sqlite3`). Для продакшна замените на PostgreSQL.
- **Медиафайлы**: хранятся локально в `backend/media/`. Для продакшна — S3 или аналог.
- **Secret Key**: обязательно смените `DJANGO_SECRET_KEY` перед деплоем.
- **MOCK_PAYMENTS=true**: режим без реальных платежей для тестирования.
