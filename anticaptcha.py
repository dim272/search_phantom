"""
Модуль для решения reCAPTCHA v2 с использованием сервиса 2Captcha.
Интегрируется с Playwright и поддерживает прокси с аутентификацией.
"""

import logging

from twocaptcha import TwoCaptcha
from playwright.async_api import Page, BrowserContext

from config import ANTICAPTCHA_API_KEY, ANTICAPTCHA_PROXY

logger = logging.getLogger(__name__)


async def captcha_exist(page: Page) -> bool:
    """Проверяет, есть ли на странице reCAPTCHA."""
    try:
        captcha_locator = page.locator('.g-recaptcha')
        captcha_count = await captcha_locator.count()

        if captcha_count > 0 and await captcha_locator.is_visible():
            logger.info("reCAPTCHA detected on page.")
            return True

        locator = page.locator('iframe[src*="recaptcha"]')
        count = await locator.count()
        if count > 0:
            logger.info("reCAPTCHA iframe detected.")
            return True

        return False
    except Exception as e:
        logger.warning(f"Error checking for captcha: {e}")
        return False

async def extract_captcha_params(page: Page):
    """Извлекает sitekey, data-s и другие параметры из reCAPTCHA."""
    try:
        sitekey = await page.evaluate('''() => {
            const el = document.querySelector('.g-recaptcha');
            return el ? el.dataset.sitekey : null;
        }''')

        data_s = await page.evaluate('''() => {
            const el = document.querySelector('.g-recaptcha');
            return el ? el.dataset.s : null;
        }''')

        if not sitekey:
            raise ValueError("Could not extract sitekey from page")

        if not data_s:
            # Попробуем извлечь из iframe src
            data_s = await page.evaluate('''() => {
                const iframe = document.querySelector('iframe[src*="recaptcha/api2/anchor"]');
                if (iframe && iframe.src) {
                    const url = new URL(iframe.src);
                    return url.searchParams.get('s');
                }
                return null;
            }''')

        if not data_s:
            raise ValueError("Could not extract data-s value")

        logger.info(f"Extracted sitekey: {sitekey}")
        logger.info(f"Extracted data-s: {data_s}")

        return {
            'sitekey': sitekey,
            'data_s': data_s
        }
    except Exception as e:
        logger.error(f"Failed to extract captcha params: {str(e)}")
        raise

def prepare_task_params(sitekey, url, data_s, cookies, user_agent):
    """
    Подготавливает и валидирует параметры для задачи reCAPTCHA V2.
    Все параметры обязательны.

    :param sitekey: str, значение data-sitekey
    :param url: str, URL страницы с капчей
    :param data_s: str, значение параметра data-s (из атрибута data-s или параметра s в iframe)
    :param cookies: dict или str, куки в формате "key=value; key2=value2"
    :param user_agent: str, User-Agent строки
    :param proxy: dict, {'type': 'http', 'uri': 'user:pass@ip:port'}
    :return: dict — готовый словарь параметров для solver.recaptcha()
    """
    # Валидация обязательных строк
    if not all([sitekey, url, data_s, user_agent]):
        raise ValueError("Все параметры (sitekey, url, data_s, user_agent, proxy) обязательны и не должны быть пустыми.")

    # Обработка cookies: если передан dict, преобразуем в строку; если строка — оставляем как есть
    if isinstance(cookies, dict):
        cookies_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])
    elif isinstance(cookies, str):
        cookies_str = cookies
    else:
        raise TypeError("Куки должны быть строкой или словарём")

    return {
        'sitekey': sitekey,
        'url': url,
        'data-s': data_s,
        'cookies': cookies_str,
        'userAgent': user_agent,
        'proxy': ANTICAPTCHA_PROXY
    }

async def solve_recaptcha_v2(page: Page, context: BrowserContext) -> None:
    """
    Решает reCAPTCHA v2 на текущей странице с помощью сервиса 2Captcha.

    :param page: Экземпляр страницы Playwright.
    :param context: Контекст браузера Playwright (для кук и сессии).
    :raises RuntimeError: Если не удалось решить капчу или отсутствует API-ключ.
    """
    if not await captcha_exist(page):
        return None

    logger.info("Solving initial reCAPTCHA...")

    user_agent = await page.evaluate("() => navigator.userAgent")
    params = await extract_captcha_params(page)
    cookies = await context.cookies()
    cookies_dict = {c['name']: c['value'] for c in cookies}

    try:
        task_params = prepare_task_params(
            sitekey=params['sitekey'],
            url=page.url,
            data_s=params['data_s'],
            cookies=cookies_dict,
            user_agent=user_agent,
        )

        solver = TwoCaptcha(ANTICAPTCHA_API_KEY)
        logger.info("Sending reCAPTCHA to 2Captcha...")
        result = solver.recaptcha(**task_params)
        token = result['code']

        logger.info(f"reCAPTCHA solved! Token: {token[:50]}...")

        await page.evaluate(f"""(token) => {{
            const textarea = document.querySelector('textarea[name="g-recaptcha-response"]');
            if (textarea) {{
                textarea.style.display = 'block';
                textarea.value = token;
                textarea.dispatchEvent(new Event('input', {{ bubbles: true }}));
                textarea.dispatchEvent(new Event('change', {{ bubbles: true }}));
            }}
            // Вызываем callback, если он есть
            const widget = document.querySelector('.g-recaptcha');
            if (widget && typeof widget.dataset.callback === 'string') {{
                window[widget.dataset.callback](token);
            }}
        }}""", token)

        await page.wait_for_timeout(5000)

    except Exception as e:
        logger.error(f"Error solving reCAPTCHA: {str(e)}")
