"""
Конфигурационный модуль проекта.
Содержит пути, настройки поиска, прокси и интеграцию с 2Captcha.
Загружает параметры из переменных окружения.
"""

import os
from pathlib import Path

from playwright._impl._api_structures import ProxySettings


ROOT_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = ROOT_DIR / "results"
OUTPUT_DIR.mkdir(exist_ok=True)

SEARCH_QUERY = "пицца доставка"
TARGET_DOMAIN = "dodopizza.ru"
SEARCH_ENGINE = "https://www.google.com"

# Нужна "липкая" сессия без ротации прокси
PROXY_TYPE = os.environ.get("PROXY_TYPE", "http").lower()
PROXY_HOST = os.environ.get("PROXY_HOST")
PROXY_PORT = os.environ.get("PROXY_PORT")
PROXY_USERNAME = os.environ.get("PROXY_USERNAME")
PROXY_PASSWORD = os.environ.get("PROXY_PASSWORD")

ANTICAPTCHA_API_KEY = os.environ.get("ANTICAPTCHA_API_KEY")

# Проверка обязательных полей
if not all([PROXY_HOST, PROXY_PORT]):
    raise ValueError("PROXY_HOST и PROXY_PORT обязательны в .env")

# Формируем строку server
proxy_server = f"{PROXY_TYPE}://{PROXY_HOST}:{PROXY_PORT}"

# Создаём ProxySettings для Playwright
PW_PROXY_SETTINGS = ProxySettings(
    server=proxy_server,
    username=PROXY_USERNAME,
    password=PROXY_PASSWORD
)

# Данные для 2Captcha (в формате, понятном twocaptcha)
ANTICAPTCHA_PROXY = {
    "type": PROXY_TYPE,
    "uri": f"{PROXY_USERNAME}:{PROXY_PASSWORD}@{PROXY_HOST}:{PROXY_PORT}" if PROXY_USERNAME else f"{PROXY_HOST}:{PROXY_PORT}"
}
