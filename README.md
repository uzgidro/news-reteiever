# Telegram Channel Message Receiver (Microservice)

REST API микросервис для получения сообщений из одного Telegram-канала через MTProto API (Pyrogram).

## Концепция

Это микросервис, который:
- Подключается к **одному конкретному** Telegram-каналу (настраивается через конфиг)
- Предоставляет REST API для получения сообщений в формате JSON
- Поддерживает пагинацию и фильтрацию по датам
- Обрабатывает медиа-файлы (фото/видео)
- Извлекает метаданные (просмотры, реакции, автор)

## Возможности

- **Работа с одним каналом** - канал настраивается через `TARGET_CHANNEL_ID`
- **REST API endpoint** - `GET /api/v1/messages` возвращает JSON
- **Пагинация** - ~20 сообщений на запрос с offset_id
- **Фильтрация по дате** - выбор сообщений за период
- **Обработка медиа** - скачивание и кеширование фото/видео
- **Метаданные** - дата, автор, просмотры, реакции
- **Swagger UI** - интерактивная документация API

## Технологический стек

- Python 3.10+
- FastAPI - async web framework
- Pyrogram - MTProto клиент для Telegram
- Pydantic - валидация данных
- Uvicorn - ASGI сервер

## Установка

### 1. Активация виртуального окружения

```bash
cd C:\projects\python\channelMessageReceiver
.venv\Scripts\activate
```

### 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 3. Получение Telegram API credentials

1. Перейдите на https://my.telegram.org/apps
2. Войдите в аккаунт Telegram
3. Создайте новое приложение
4. Скопируйте `api_id` и `api_hash`

### 4. Определение ID канала

**Способ 1: Через бота**
1. Добавьте бота [@username_to_id_bot](https://t.me/username_to_id_bot) или [@getidsbot](https://t.me/getidsbot)
2. Перешлите любое сообщение из канала боту
3. Бот покажет Channel ID (например: `-1001234567890`)

**Способ 2: Через username**
Если у канала есть публичный username, можно использовать его напрямую:
- `@channelname` или просто `channelname`

### 5. Настройка конфигурации

```bash
copy .env .env
```

Отредактируйте `.env` файл:

```env
# Telegram API credentials
TELEGRAM_API_ID=ваш_api_id
TELEGRAM_API_HASH=ваш_api_hash

# ID или username целевого канала
TARGET_CHANNEL_ID=-1001234567890
# или
TARGET_CHANNEL_ID=@channelname
```

## Запуск

### Режим разработки (с auto-reload)

```bash
uvicorn main:app --reload
```

### Режим production

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1
```

или

```bash
python main.py
```

**Важно**: Используйте только 1 worker, так как Pyrogram поддерживает одну активную сессию.

Сервис будет доступен на: http://localhost:8000

## Первичная настройка (Аутентификация)

При первом запуске нужно аутентифицироваться в Telegram:

### Через Swagger UI (рекомендуется)

1. Откройте http://localhost:8000/docs
2. Разверните раздел **Authentication**
3. Выполните `/auth/request-code`:
   ```json
   {
     "phone": "+1234567890"
   }
   ```
4. Проверьте Telegram - придет код подтверждения
5. Выполните `/auth/verify-code`:
   ```json
   {
     "phone": "+1234567890",
     "code": "12345",
     "phone_code_hash": "hash_из_предыдущего_ответа"
   }
   ```
6. Если включен 2FA, выполните `/auth/verify-2fa`:
   ```json
   {
     "phone": "+1234567890",
     "password": "ваш_2fa_пароль"
   }
   ```

### Через curl

```bash
# 1. Запросить код
curl -X POST "http://localhost:8000/api/v1/auth/request-code" \
  -H "Content-Type: application/json" \
  -d '{"phone": "+1234567890"}'

# 2. Верифицировать код
curl -X POST "http://localhost:8000/api/v1/auth/verify-code" \
  -H "Content-Type: application/json" \
  -d '{"phone": "+1234567890", "code": "12345", "phone_code_hash": "..."}'
```

После успешной аутентификации сессия сохраняется в файл `sessions/telegram_session.session`. При последующих запусках аутентификация не требуется.

## Использование API

### Основной endpoint

```
GET /api/v1/messages
```

### Примеры запросов

#### 1. Получить последние 20 сообщений

```bash
curl "http://localhost:8000/api/v1/messages?limit=20&offset_id=0"
```

или откройте в браузере:
```
http://localhost:8000/api/v1/messages?limit=20
```

#### 2. Получить следующую страницу (пагинация)

Используйте `next_offset_id` из предыдущего ответа:

```bash
curl "http://localhost:8000/api/v1/messages?limit=20&offset_id=12345"
```

#### 3. Фильтрация по датам

Получить сообщения за январь 2026:

```bash
curl "http://localhost:8000/api/v1/messages?limit=50&date_from=2026-01-01T00:00:00Z&date_to=2026-01-31T23:59:59Z"
```

#### 4. Без медиа-файлов (быстрее)

```bash
curl "http://localhost:8000/api/v1/messages?limit=20&include_media=false"
```

### Пример ответа (JSON)

```json
{
  "channel_id": -1001234567890,
  "channel_title": "Название канала",
  "messages": [
    {
      "id": 12345,
      "text": "Текст сообщения...",
      "date": "2026-01-05T12:00:00+00:00",
      "views": 1500,
      "forwards": 25,
      "reactions": [
        {"emoji": "👍", "count": 42},
        {"emoji": "🔥", "count": 18}
      ],
      "author": {
        "id": 123456,
        "username": "author_username",
        "first_name": "John"
      },
      "media": {
        "type": "photo",
        "url": "http://localhost:8000/media/1001234567890/12345/photo.jpg",
        "file_size": 524288,
        "width": 1280,
        "height": 720
      },
      "reply_to_message_id": null,
      "edit_date": null,
      "has_protected_content": false
    }
  ],
  "pagination": {
    "total_fetched": 20,
    "next_offset_id": 12325,
    "has_more": true
  }
}
```

### Query параметры

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|----------|
| `limit` | int | 20 | Количество сообщений (1-100) |
| `offset_id` | int | 0 | ID сообщения для пагинации |
| `date_from` | string | null | Дата начала (ISO 8601) |
| `date_to` | string | null | Дата окончания (ISO 8601) |
| `include_media` | bool | true | Включить медиа информацию |
| `media_format` | string | "url" | Формат медиа: "url" или "base64" |

## API Endpoints

### Messages (основной функционал)

- `GET /api/v1/messages` - Получить сообщения из настроенного канала

### Authentication (первичная настройка)

- `POST /api/v1/auth/request-code` - Запросить код подтверждения
- `POST /api/v1/auth/verify-code` - Подтвердить код
- `POST /api/v1/auth/verify-2fa` - 2FA аутентификация
- `GET /api/v1/auth/status` - Статус аутентификации
- `POST /api/v1/auth/logout` - Выход

### System

- `GET /health` - Проверка состояния сервиса
- `GET /` - Информация об API
- `GET /docs` - Swagger UI (интерактивная документация)

## Интеграция с другими сервисами

### Пример на Python

```python
import requests

# Получить сообщения
response = requests.get(
    'http://localhost:8000/api/v1/messages',
    params={
        'limit': 50,
        'offset_id': 0,
        'include_media': True
    }
)

data = response.json()

for message in data['messages']:
    print(f"[{message['date']}] {message['text']}")
    if message.get('media'):
        print(f"  Media: {message['media']['url']}")
```

### Пример на JavaScript (fetch)

```javascript
async function getMessages(limit = 20, offsetId = 0) {
  const response = await fetch(
    `http://localhost:8000/api/v1/messages?limit=${limit}&offset_id=${offsetId}`
  );
  const data = await response.json();
  return data;
}

// Использование
const messages = await getMessages(50);
console.log(`Получено ${messages.messages.length} сообщений`);
```

## Конфигурация

Все настройки задаются через переменные окружения в `.env` файле:

| Параметр | Описание | Пример |
|----------|----------|--------|
| `TELEGRAM_API_ID` | Telegram API ID | `12345678` |
| `TELEGRAM_API_HASH` | Telegram API Hash | `abcdef123...` |
| `TARGET_CHANNEL_ID` | ID или username канала | `-1001234567890` |
| `APP_HOST` | Хост сервера | `0.0.0.0` |
| `APP_PORT` | Порт сервера | `8000` |
| `DEFAULT_MESSAGES_LIMIT` | Лимит по умолчанию | `20` |

## Структура проекта

```
channelMessageReceiver/
├── app/
│   ├── api/routes/          # API endpoints
│   │   ├── auth.py         # Аутентификация
│   │   ├── channels.py     # Информация о канале
│   │   └── messages.py     # Основной endpoint
│   ├── core/               # Ядро
│   │   ├── telegram_client.py
│   │   └── exceptions.py
│   ├── models/             # Pydantic модели
│   │   ├── requests.py
│   │   └── responses.py
│   ├── services/           # Бизнес-логика
│   │   ├── message_service.py
│   │   ├── media_service.py
│   │   └── channel_service.py
│   └── utils/              # Утилиты
│       └── formatters.py
├── sessions/               # Telegram сессии (не в git)
├── media/                  # Кеш медиа (не в git)
├── config.py              # Конфигурация
├── main.py                # Точка входа
└── .env                   # Переменные окружения (не в git)
```

## Безопасность

- **Session файлы** - хранятся локально в `sessions/`, не коммитятся в git
- **API credentials** - хранятся в `.env`, не коммитятся в git
- **Медиа файлы** - кешируются локально, можно ограничить размер кеша
- **Валидация** - все входные данные валидируются через Pydantic
- **Rate limiting** - для production рекомендуется добавить

## Решение проблем

### Ошибка "Not authenticated with Telegram"

Пройдите аутентификацию через `/api/v1/auth/request-code` и `/api/v1/auth/verify-code`.

### Ошибка "Configured channel not accessible"

Проверьте:
1. Правильность `TARGET_CHANNEL_ID` в `.env`
2. Ваш Telegram аккаунт подписан на этот канал
3. Канал не заблокирован

### Ошибка "Session expired"

Удалите файлы сессий и пройдите аутентификацию заново:

```bash
rm sessions/*.session*
```

### FloodWait ошибка

Telegram временно ограничил запросы. Подождите указанное время.

## Деплой в production

### Docker Compose (рекомендуется)

**Важно**: Docker volumes сохраняют сессию между обновлениями контейнера!

#### Первый запуск (с аутентификацией)

1. Создайте `.env` файл с настройками:

```bash
cp .env .env
# Отредактируйте .env: добавьте API credentials и TARGET_CHANNEL_ID
```

2. Запустите контейнер:

```bash
docker-compose up -d
```

3. **Пройдите аутентификацию** (только один раз):

```bash
# Откройте Swagger UI
http://your-server:8000/docs

# Выполните:
# 1. POST /api/v1/auth/request-code
# 2. POST /api/v1/auth/verify-code
# (опционально) POST /api/v1/auth/verify-2fa
```

4. Проверьте, что сессия создана:

```bash
ls sessions/
# Должен появиться файл telegram_session.session
```

✅ **Готово!** Сессия сохранена в `./sessions/` на хосте.

#### Обновление кода (без потери сессии)

```bash
# 1. Остановить контейнер
docker-compose down

# 2. Обновить код (git pull или копирование новых файлов)
git pull

# 3. Пересобрать образ
docker-compose build

# 4. Запустить заново
docker-compose up -d
```

**Важно**: Файл `sessions/telegram_session.session` **НЕ удаляется**, сессия сохраняется!

#### Мониторинг и логи

```bash
# Просмотр логов
docker-compose logs -f

# Статус контейнера
docker-compose ps

# Перезапуск
docker-compose restart

# Проверка здоровья
curl http://localhost:8000/health
```

#### Очистка и переаутентификация

Если нужно переаутентифицироваться:

```bash
# 1. Остановить контейнер
docker-compose down

# 2. Удалить старую сессию
rm sessions/*.session*

# 3. Запустить и пройти аутентификацию заново
docker-compose up -d
# Затем снова через Swagger UI
```

### Обычный Docker (без compose)

```bash
# Сборка образа
docker build -t telegram-channel-receiver .

# Запуск с volumes для сохранения сессии
docker run -d \
  --name telegram-receiver \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/sessions:/app/sessions \
  -v $(pwd)/media:/app/media \
  --restart unless-stopped \
  telegram-channel-receiver

# Обновление
docker stop telegram-receiver
docker rm telegram-receiver
docker build -t telegram-channel-receiver .
docker run -d \
  --name telegram-receiver \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/sessions:/app/sessions \
  -v $(pwd)/media:/app/media \
  --restart unless-stopped \
  telegram-channel-receiver
```

### Kubernetes (для масштабирования)

Создайте `k8s-deployment.yaml`:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: telegram-sessions
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: telegram-receiver
spec:
  replicas: 1  # ВАЖНО: только 1 реплика (одна Telegram сессия)
  selector:
    matchLabels:
      app: telegram-receiver
  template:
    metadata:
      labels:
        app: telegram-receiver
    spec:
      containers:
      - name: telegram-receiver
        image: telegram-channel-receiver:latest
        ports:
        - containerPort: 8000
        env:
        - name: TELEGRAM_API_ID
          valueFrom:
            secretKeyRef:
              name: telegram-secrets
              key: api-id
        - name: TELEGRAM_API_HASH
          valueFrom:
            secretKeyRef:
              name: telegram-secrets
              key: api-hash
        - name: TARGET_CHANNEL_ID
          value: "-1001234567890"
        volumeMounts:
        - name: sessions
          mountPath: /app/sessions
        - name: media
          mountPath: /app/media
      volumes:
      - name: sessions
        persistentVolumeClaim:
          claimName: telegram-sessions
      - name: media
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: telegram-receiver
spec:
  selector:
    app: telegram-receiver
  ports:
  - port: 8000
    targetPort: 8000
  type: LoadBalancer
```

Деплой:

```bash
# Создать секреты
kubectl create secret generic telegram-secrets \
  --from-literal=api-id=YOUR_API_ID \
  --from-literal=api-hash=YOUR_API_HASH

# Задеплоить
kubectl apply -f k8s-deployment.yaml

# Для первичной аутентификации:
kubectl port-forward svc/telegram-receiver 8000:8000
# Затем http://localhost:8000/docs
```

### Systemd (Linux, без Docker)

Создайте `/etc/systemd/system/telegram-receiver.service`:

```ini
[Unit]
Description=Telegram Channel Message Receiver
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/channelMessageReceiver
Environment="PATH=/path/to/.venv/bin"
ExecStart=/path/to/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Активация:

```bash
sudo systemctl daemon-reload
sudo systemctl enable telegram-receiver
sudo systemctl start telegram-receiver
sudo systemctl status telegram-receiver

# Логи
sudo journalctl -u telegram-receiver -f
```

### CI/CD Pipeline (GitHub Actions пример)

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2

    - name: Build and push Docker image
      run: |
        docker build -t your-registry/telegram-receiver:latest .
        docker push your-registry/telegram-receiver:latest

    - name: Deploy to server
      uses: appleboy/ssh-action@master
      with:
        host: ${{ secrets.SERVER_HOST }}
        username: ${{ secrets.SERVER_USER }}
        key: ${{ secrets.SSH_KEY }}
        script: |
          cd /app/telegram-receiver
          docker-compose pull
          docker-compose up -d
          # Сессия сохраняется в ./sessions/ - не затрагивается!
```

### Важные заметки по production

1. **Одна сессия = один контейнер/процесс**
   - Не запускайте несколько реплик с одной сессией
   - Pyrogram не поддерживает одновременное использование сессии

2. **Backup сессии**
   ```bash
   # Регулярно делайте backup
   tar -czf sessions-backup-$(date +%Y%m%d).tar.gz sessions/
   ```

3. **Monitoring**
   - Используйте `/health` endpoint для healthcheck
   - Настройте алерты на недоступность API
   - Логируйте ошибки подключения к Telegram

4. **Rate Limiting**
   - Telegram имеет лимиты на запросы
   - Не делайте слишком частые запросы к API
   - Используйте кеширование там, где возможно

5. **Обновления безопасности**
   - Регулярно обновляйте зависимости: `pip install --upgrade -r requirements.txt`
   - Следите за обновлениями Pyrogram

## Лицензия

MIT

## Автор

Создано с помощью Claude Code
