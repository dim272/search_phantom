"""
Утилиты для работы с файловой системой, извлечением ссылок и сохранением данных.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, parse_qs

from playwright.async_api import Page

from config import OUTPUT_DIR

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_session_folder() -> Path:
    """
    Создаёт новую папку для текущей сессии вида `results/2025-04-05_12-30-45`.

    :return: Объект Path к созданной папке.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    session_dir = OUTPUT_DIR / timestamp
    session_dir.mkdir(exist_ok=True)
    logger.info(f"Создана сессионная папка: {session_dir}")
    return session_dir

def save_links(links: list[str], session_dir: Path):
    """
    Сохраняет список ссылок в файл `top_10_links.txt` внутри папки сессии.

    :param links: Список URL-адресов.
    :param session_dir: Папка сессии, куда сохранить файл.
    """
    links_file = session_dir / "top_10_links.json"

    with open(links_file, 'w', encoding='utf-8') as f:
        json.dump(links, f, ensure_ascii=False, indent=2)
    logger.info(f"Сохранены ссылки: {links_file}")

async def save_html(page: Page, session_dir: Path):
    """
    Сохраняет HTML-содержимое текущей страницы.

    :param page: Экземпляр страницы Playwright.
    :param session_dir: Папка сессии, куда сохранить HTML.
    """
    file_path = url_to_file_path(page.url, session_dir)

    content = await page.content()
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    logger.info(f"Сохранён HTML страницы: {page.url}")


async def save_screenshot(page: Page, session_dir: Path):
    """
    Сохраняет скриншот текущей страницы с уникальным именем.

    :param page: Экземпляр страницы Playwright.
    :param session_dir: Папка сессии, куда сохранить скриншот.
    """
    file_path = url_to_file_path(page.url, session_dir, ext="png")
    await page.screenshot(path=file_path, full_page=True)
    logger.info(f"Сохранён скриншот страницы: {page.url}")

def url_to_file_path(url: str, session_dir: Path, ext: str = "html") -> Path:
    """
    Генерирует путь для сохранения файла на основе имени домена из URL.

    :param url: URL-адрес страницы.
    :param session_dir: Папка сессии, куда сохранить файл.
    :param ext: Расширение файла (по умолчанию 'html').
    :return: Объект Path к сохранённому файлу.
    """
    hostname = urlparse(url).hostname
    return session_dir / f"{hostname}.{ext}"


def organic_link(link: str) -> str | None:
    """
    Проверяет, является ли ссылка органической (не рекламой, не Google-сервисом).
    Извлекает чистый домен для анализа.

    :param link: Полный URL из атрибута href.
    :return: Очищенный URL (https://domain.com/path) или None, если ссылка рекламная.
    """
    if not link or not link.startswith('http'):
        return None

    if '/url?' in link:
        # Парсим настоящий URL из параметра `q`
        try:
            q = parse_qs(urlparse(link).query).get('q', [])
            if q:
                link = q[0]
        except:
            return None

    # Исключаем ссылки Google (не ведущие напрямую на сайт)
    hostname = urlparse(link).hostname
    google_domains = ('google.com', 'goo.gl')
    for domain in google_domains:
        if domain in hostname:
            return None

    return link
