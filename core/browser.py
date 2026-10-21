from typing import Optional
from playwright.sync_api import sync_playwright, Playwright, Browser, BrowserContext, Page
from config.settings import HEADLESS, SLOW_MO, BROWSER_TIMEOUT
from utils.logger import Logger

class BrowserManager:
    """Manages the Playwright browser lifecycle and page context."""

    def __init__(self, headless: bool = HEADLESS):
        self.headless = headless
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

    def start(self) -> Page:
        """Launches Chromium browser and creates a clean context."""
        Logger.info("Starting browser...")
        self._playwright = sync_playwright().start()
        
        self._browser = self._playwright.chromium.launch(
            headless=self.headless,
            slow_mo=SLOW_MO,
            args=[
                "--start-maximized",
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox"
            ]
        )

        # Create context with download handling enabled
        self._context = self._browser.new_context(
            no_viewport=True,
            accept_downloads=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        self._context.set_default_timeout(BROWSER_TIMEOUT)

        self._page = self._context.new_page()
        Logger.info("Browser launched successfully.")
        return self._page

    @property
    def page(self) -> Page:
        if not self._page:
            raise RuntimeError("Browser has not been started. Call start() first.")
        return self._page

    @property
    def context(self) -> BrowserContext:
        if not self._context:
            raise RuntimeError("Browser context has not been started.")
        return self._context

    def close(self):
        """Closes browser context and Playwright process cleanly."""
        Logger.info("Closing browser...")
        try:
            if self._context:
                self._context.close()
            if self._browser:
                self._browser.close()
            if self._playwright:
                self._playwright.stop()
        except Exception as e:
            Logger.warning(f"Error during browser shutdown: {e}")
        finally:
            self._page = None
            self._context = None
            self._browser = None
            self._playwright = None
        Logger.info("Browser closed.")
