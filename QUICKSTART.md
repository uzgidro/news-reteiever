# Быстрый старт с Docker

## Первый запуск (5 минут)

### 1. Настройте конфигурацию

```bash
# Создайте .env файл
cp .env.example .env
```

Отредактируйте `.env`:
```env
TELEGRAM_API_ID=12345678              # Получите на https://my.telegram.org/apps
TELEGRAM_API_HASH=abcd1234...         # Получите на https://my.telegram.org/apps
TARGET_CHANNEL_ID=-1001234567890      # ID вашего канала
```

**Как получить Channel ID:**
- Перешлите сообщение из канала боту [@getidsbot](https://t.me/getidsbot)
- Или используйте username: `@channelname`

### 2. Запустите контейнер

```bash
docker-compose up -d
```

Проверьте запуск:
```bash
docker-compose logs -f
```

Вы увидите:
```
INFO - Telegram client initialized (no session found, authentication required)
INFO - Application startup complete
INFO - Uvicorn running on http://0.0.0.0:8020
```

### 3. Пройдите аутентификацию (только один раз!)

Откройте в браузере: **http://localhost:8020/docs**

**Шаг 1:** Запросите код
- Разверните `POST /api/v1/auth/request-code`
- Нажмите "Try it out"
- Введите:
  ```json
  {
    "phone": "+1234567890"
  }
  ```
- Нажмите "Execute"
- Скопируйте `phone_code_hash` из ответа

**Шаг 2:** Подтвердите код
- Проверьте Telegram - вам придет код
- Разверните `POST /api/v1/auth/verify-code`
- Введите:
  ```json
  {
    "phone": "+1234567890",
    "code": "12345",
    "phone_code_hash": "скопированный_hash"
  }
  ```
- Нажмите "Execute"

**Шаг 3 (если есть 2FA):**
- Разверните `POST /api/v1/auth/verify-2fa`
- Введите пароль 2FA

✅ **Готово!** Сессия сохранена.

### 4. Проверьте работу

```bash
# Через браузер
http://localhost:8020/api/v1/messages?limit=5

# Через curl
curl "http://localhost:8020/api/v1/messages?limit=5"
```

Вы получите JSON с сообщениями из канала!

## Обновление кода (без потери сессии)

```bash
# 1. Остановить
docker-compose down

# 2. Обновить код
git pull

# 3. Пересобрать и запустить
docker-compose build
docker-compose up -d
```

**Важно:** Сессия в `./sessions/` не удаляется - аутентификация НЕ требуется!

## Проверка статуса

```bash
# Health check
curl http://localhost:8020/health

# Ответ:
{
  "status": "healthy",
  "telegram_connected": true,
  "telegram_authorized": true,
  "version": "1.0.0"
}
```

## Логи

```bash
# Просмотр логов
docker-compose logs -f

# Последние 100 строк
docker-compose logs --tail=100

# Только ошибки
docker-compose logs | grep ERROR
```

## Типичные проблемы

### "Not authenticated with Telegram"

**Причина:** Сессия не создана или удалена

**Решение:**
```bash
# Проверьте наличие сессии
ls sessions/

# Если файла нет - пройдите аутентификацию через Swagger UI
http://localhost:8020/docs
```

### "Configured channel not accessible"

**Причина:** Неправильный `TARGET_CHANNEL_ID` или аккаунт не подписан на канал

**Решение:**
1. Проверьте `TARGET_CHANNEL_ID` в `.env`
2. Убедитесь что ваш Telegram аккаунт подписан на этот канал
3. Перезапустите: `docker-compose restart`

### Контейнер не запускается

```bash
# Проверьте логи
docker-compose logs

# Проверьте .env файл
cat .env

# Пересоздайте контейнер
docker-compose down
docker-compose up -d
```

## Полезные команды

```bash
# Статус контейнера
docker-compose ps

# Перезапуск
docker-compose restart

# Остановка
docker-compose stop

# Полное удаление (без сессии!)
docker-compose down

# Удаление с volumes (УДАЛИТ СЕССИЮ!)
docker-compose down -v
```

## Production checklist

- [ ] Установлен правильный `TARGET_CHANNEL_ID`
- [ ] Пройдена аутентификация через Swagger UI
- [ ] Файл `sessions/telegram_session.session` существует
- [ ] Настроен мониторинг `/health` endpoint
- [ ] Настроен backup директории `sessions/`
- [ ] Логи ротируются (настроено в docker-compose.yml)
- [ ] Порт 8020 защищен (через reverse proxy nginx/traefik)

## Интеграция с другими сервисами

### Python
```python
import requests

response = requests.get('http://localhost:8020/api/v1/messages?limit=20')
data = response.json()

for msg in data['messages']:
    print(f"{msg['date']}: {msg['text']}")
```

### JavaScript
```javascript
const response = await fetch('http://localhost:8020/api/v1/messages?limit=20');
const data = await response.json();
console.log(data.messages);
```

### cURL
```bash
curl "http://localhost:8020/api/v1/messages?limit=20&date_from=2026-01-01T00:00:00Z"
```

## Дополнительная информация

Полная документация: [README.md](README.md)
