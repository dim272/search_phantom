"""
Основной модуль запуска парсера.
Запускает браузер, выполняет поиск, решает капчу, кликает по целевому домену.
"""
import random
import asyncio
import logging

from playwright.async_api import async_playwright, Page

from anticaptcha import solve_recaptcha_v2
from config import PW_PROXY_SETTINGS, SEARCH_QUERY, SEARCH_ENGINE, TARGET_DOMAIN
from utils import create_session_folder, save_screenshot, save_html, save_links, organic_link

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def human_like_actions(page: Page):
    """
    Эмулирует поведение реального пользователя: случайные задержки и скроллинг.

    :param page: Экземпляр страницы Playwright.
    """
    await page.wait_for_timeout(random.randint(250, 2000))

    # Случайный скролл
    for _ in range(random.randint(1, 3)):
        scroll_amount = random.randint(100, 500)
        await page.evaluate(f"window.scrollBy(0, {scroll_amount})")
        await page.wait_for_timeout(random.randint(500, 1500))

    # Вернуться наверх
    await page.evaluate("window.scrollTo(0, 0)")
    await page.wait_for_timeout(random.randint(77, 777))


async def extract_top_10_links(page: Page):
    """
    Извлекает первые 10 органических (не рекламных) ссылок из результатов Google.

    :param page: Страница с результатами поиска.
    :return: Список из 10 URL (или меньше, если найдено меньше).
    """
    logger.info("Извлечение первых 10 ссылок из результатов поиска...")

    # Ожидание появления хотя бы одной органической ссылки
    try:
        await page.wait_for_selector('#rso', timeout=10000)
    except:
        logger.error("Не удалось найти ссылки в результатах поиска.")
        return []

    # Селектор для органических результатов (основные ссылки в результатах)
    # Исключаем рекламные блоки, "Места", "Картинки" и т.д.
    link_elements = await page.locator('#rso a[href^="http"]').all()

    links = []
    for el in link_elements:
        href = await el.get_attribute('href')
        link = organic_link(href)
        if not link or link in links:
            continue

        links.append(link)
        if len(links) >= 10:
            break

    logger.info(f"Найдено {len(links)} органических ссылок:")
    for i, link in enumerate(links, 1):
        logger.info(f"{i}. {link}")

    return links


async def main():
    """
    Основная асинхронная функция:
    - Запускает браузер через Playwright.
    - Переходит на Google.
    - Решает reCAPTCHA.
    - Выполняет поиск.
    - Извлекает топ-10 ссылок.
    - Кликает по целевому домену.
    - Сохраняет результаты.
    """
    session_dir = create_session_folder()   # для сохранения результатов

    async with async_playwright() as p:
        device = p.devices["iPhone 13 Pro"]
        browser = await p.chromium.launch(
            headless=False,
            proxy=PW_PROXY_SETTINGS
        )
        context = await browser.new_context(**device)

        page = await context.new_page()
        user_agent = await page.evaluate("() => navigator.userAgent")
        logger.info(f"User-Agent: {user_agent}")

        try:
            await page.goto(SEARCH_ENGINE, wait_until="networkidle")
            await human_like_actions(page)

            await solve_recaptcha_v2(page, context)
            await page.wait_for_load_state("domcontentloaded")
            await page.wait_for_timeout(random.randint(1200, 2800))

            search_input = page.locator('textarea[name="q"]')
            await search_input.wait_for(state="visible", timeout=10000)
            await search_input.click()

            logger.info(f"Typing search query {SEARCH_QUERY!r} ...")
            for char in SEARCH_QUERY:
                await search_input.type(char, delay=random.randint(77, 377))

            await page.keyboard.press("Enter")
            await page.wait_for_load_state("domcontentloaded")
            await page.wait_for_timeout(random.randint(1200, 2800))

            await solve_recaptcha_v2(page, context)

            await page.wait_for_load_state("domcontentloaded")
            await page.wait_for_timeout(random.randint(1200, 2800))

            await save_screenshot(page, session_dir)
            await save_html(page, session_dir)

            top_10_links = await extract_top_10_links(page)
            save_links(top_10_links, session_dir)

            target_link = page.locator(f'a[href*="{TARGET_DOMAIN}"]').first

            if await target_link.is_visible():
                await target_link.click()
                logger.info("Clicked on target link.")

                await page.wait_for_load_state("domcontentloaded")
                await page.wait_for_timeout(random.randint(1200, 2800))

                await save_screenshot(page, session_dir)
                await save_html(page, session_dir)
            else:
                logger.warning("Target link not found or not visible.")

        except Exception as e:
            logger.error(f"Error during execution: {str(e)}")
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())