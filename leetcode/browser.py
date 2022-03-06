__author__ = "evlic"

from contextlib import asynccontextmanager
from typing import AsyncIterator

from playwright.async_api import Page

from utils.browser import get_browser

@asynccontextmanager
async def get_new_page(**kwargs) -> AsyncIterator[Page]:
    browser = await get_browser()
    page = await browser.new_page(**kwargs)
    try:
        yield page
    finally:
        await page.close()
