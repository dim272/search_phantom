# search_phantom
Google Scraper with reCAPTCHA Bypass

Автоматизированный парсер Google с обходом reCAPTCHA через 2Captcha, поддержкой прокси и эмуляцией поведения пользователя.

## Функции
- Поиск по запросу в Google
- Обход reCAPTCHA v2 (через [2Captcha](https://2captcha.com))
- Работа через аутентифицированный прокси
- Извлечение топ-10 органических ссылок
- Клик по целевому домену
- Сохранение скриншотов, HTML и ссылок

## ️Перед запуском
1. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```
2. Создай .env файл с переменными:
   ```env
    PROXY_HOST=your.proxy.host
    PROXY_PORT=3128
    PROXY_USERNAME=user
    PROXY_PASSWORD=pass
    ANTICAPTCHA_API_KEY=ваш_ключ_с_2captcha
   ```
3. Запускай скрипт:
   ```bash
   python main.py
   ```