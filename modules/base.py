import time
from abc import ABC, abstractmethod
from typing import Optional
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from config.settings import GST_RETURNS_DASHBOARD_URL, GST_DASHBOARD_URL
from utils.logger import Logger

class BaseModule(ABC):
    """Abstract base class for all GST portal automation modules."""

    def __init__(self, page: Page, gstin: str, client_name: str = ""):
        self.page = page
        self.gstin = gstin
        self.client_name = client_name

    def wait_for_loading(self, timeout: int = 20000):
        """Waits for any GST loading spinner / overlay to disappear."""
        try:
            loading_selector = ".loading, .spinner, div[id*='loading'], .modal-backdrop"
            if self.page.locator(loading_selector).count() > 0:
                self.page.locator(loading_selector).first.wait_for(state="detached", timeout=timeout)
        except Exception:
            pass
        time.sleep(0.5)

    def dismiss_portal_popups(self):
        """Dismisses common GST portal modal popups and notification banners with close/cross icons."""
        try:
            popup_selectors = [
                # Notification banner cross / close icons
                "xpath=//div[contains(@class, 'banner') or contains(@class, 'alert') or contains(@class, 'notification') or contains(@class, 'header')]//button[contains(@class, 'close') or @aria-label='Close' or contains(., '×') or contains(., 'X')]",
                "xpath=//div[contains(@class, 'banner') or contains(@class, 'alert') or contains(@class, 'notification') or contains(@class, 'header')]//a[contains(@class, 'close') or contains(., '×') or contains(., 'X')]",
                "xpath=//button[contains(@class, 'close') or @aria-label='Close' or text()='×' or text()='✕']",
                "xpath=//span[text()='×' or text()='✕']/parent::button",
                "xpath=//span[text()='×' or text()='✕']/parent::a",
                "button[aria-label='Close']",
                "button.close",
                # Modal action buttons
                "button:has-text('REMIND ME LATER')",
                "button:has-text('Remind Me Later')",
                "button:has-text('Remind me later')",
                "button:has-text('LATER')",
                "button:has-text('Later')",
                "button:has-text('CLOSE')",
                "button:has-text('Close')",
                ".modal-footer button:has-text('Later')",
                ".modal-footer button:has-text('Close')",
                "button.close[data-dismiss='modal']"
            ]
            for sel in popup_selectors:
                try:
                    loc = self.page.locator(sel)
                    if loc.count() > 0 and loc.first.is_visible():
                        Logger.info(f"Dismissing banner / popup notice on screen: {sel}")
                        loc.first.click(force=True)
                        time.sleep(0.8)
                except Exception:
                    continue
        except Exception:
            pass

    def _check_and_switch_tab(self) -> bool:
        """Checks if a new tab or window was opened and switches active page if so."""
        try:
            pages = self.page.context.pages
            if len(pages) > 1:
                # Check if the latest tab is the returns dashboard
                latest = pages[-1]
                if "return" in latest.url or "/returns" in latest.url:
                    Logger.info(f"Switching to newly opened Returns tab: {latest.url}")
                    self.page = latest
                    self.page.bring_to_front()
                    return True
        except Exception:
            pass
        return False

    def _is_returns_search_ready(self) -> bool:
        """Checks if the Returns Dashboard search controls are visible on the active page."""
        try:
            fy_loc = self.page.locator("select#fin, select[name='fin'], #fin, select[id*='fin']")
            if fy_loc.count() > 0 and fy_loc.first.is_visible():
                return True
            search_loc = self.page.locator("button:has-text('SEARCH'), input[value='SEARCH']")
            if search_loc.count() > 0 and search_loc.first.is_visible():
                return True
        except Exception:
            pass
        return False

    def _wait_for_returns_search_ready(self, timeout: int = 15000) -> bool:
        """Waits for Returns Dashboard controls to appear."""
        start_time = time.time()
        while (time.time() - start_time) * 1000 < timeout:
            self._check_and_switch_tab()
            if self._is_returns_search_ready():
                return True
            time.sleep(0.5)
        return False

    def navigate_to_returns_dashboard(self) -> bool:
        """
        Navigates to the Returns Dashboard page via on-page dashboard buttons,
        top navigation menus, or direct fallback.
        """
        Logger.info("Navigating to Returns Dashboard...")
        self.dismiss_portal_popups()

        # 1. Are we ALREADY on Returns Dashboard?
        self._check_and_switch_tab()
        if self._is_returns_search_ready():
            Logger.success("Returns Dashboard is already loaded.")
            return True

        # Check if we are on a return subpage with a BACK button (e.g. gstr2bdwld)
        back_selectors = [
            "xpath=/html/body/app-root/div[2]/app-gstr2bdwld/block-ui/div/div[2]/div/div[8]/div[2]/button",
            "xpath=//app-gstr2bdwld//div[contains(@class, 'block-ui')]//button[contains(translate(text(), 'BACK', 'back'), 'back')]",
            "xpath=//app-gstr2bdwld//button[contains(translate(text(), 'BACK', 'back'), 'back')]",
            "button:has-text('BACK')",
            "button:has-text('Back')",
            "xpath=//button[contains(text(), 'BACK') or contains(text(), 'Back')]"
        ]
        for b_sel in back_selectors:
            b_btn = self.page.locator(b_sel)
            if b_btn.count() > 0 and b_btn.first.is_visible():
                Logger.info("Found 'BACK' button on page. Clicking to return to period selection...")
                b_btn.first.click()
                time.sleep(1)
                self.wait_for_loading()
                if self._wait_for_returns_search_ready(timeout=10000):
                    Logger.success("Returned to Returns Dashboard via BACK button.")
                    return True

        # 2. Look for Returns Dashboard / File Returns button on current page
        dashboard_button_selectors = [
            "button:has-text('FILE RETURNS')",
            "a:has-text('FILE RETURNS')",
            "button:has-text('File Returns')",
            "a:has-text('File Returns')",
            "button:has-text('RETURN DASHBOARD')",
            "a:has-text('RETURN DASHBOARD')",
            "button:has-text('Return Dashboard')",
            "a:has-text('Return Dashboard')",
            "button:has-text('Returns Dashboard')",
            "a:has-text('Returns Dashboard')",
            "a[href*='returns/auth/dashboard']",
            "a[href*='/returns']"
        ]

        for sel in dashboard_button_selectors:
            btn = self.page.locator(sel)
            if btn.count() > 0 and btn.first.is_visible():
                Logger.info(f"Clicking Returns Dashboard button: '{sel}'...")
                init_pages = len(self.page.context.pages)
                btn.first.click()
                time.sleep(1)
                self.wait_for_loading()
                
                # Check if opened in new tab
                if len(self.page.context.pages) > init_pages:
                    self._check_and_switch_tab()

                if self._wait_for_returns_search_ready(timeout=15000):
                    Logger.success("Returns Dashboard loaded successfully.")
                    return True

        # 3. Try top navigation menu: Services -> Returns -> Returns Dashboard
        try:
            Logger.info("Checking top navigation menu (Services -> Returns)...")
            services_menu = self.page.locator("a:has-text('Services'), li.dropdown:has-text('Services')")
            if services_menu.count() > 0 and services_menu.first.is_visible():
                services_menu.first.click()
                time.sleep(0.5)
                returns_sub = self.page.locator("a:has-text('Returns')")
                if returns_sub.count() > 0 and returns_sub.first.is_visible():
                    returns_sub.first.click()
                    time.sleep(0.5)
                    returns_dash_link = self.page.locator("a:has-text('Returns Dashboard')")
                    if returns_dash_link.count() > 0 and returns_dash_link.first.is_visible():
                        init_pages = len(self.page.context.pages)
                        returns_dash_link.first.click()
                        time.sleep(1)
                        self.wait_for_loading()
                        if len(self.page.context.pages) > init_pages:
                            self._check_and_switch_tab()
                        if self._wait_for_returns_search_ready(timeout=15000):
                            Logger.success("Returns Dashboard loaded via top menu.")
                            return True
        except Exception as e:
            Logger.warning(f"Top menu navigation attempt encountered: {e}")

        # 4. Fallback: Reload main dashboard and retry clicking
        try:
            Logger.info("Reloading main dashboard to retry navigation...")
            self.page.goto(GST_DASHBOARD_URL, wait_until="domcontentloaded", timeout=25000)
            self.wait_for_loading()
            self.dismiss_portal_popups()
            
            for sel in dashboard_button_selectors:
                btn = self.page.locator(sel)
                if btn.count() > 0 and btn.first.is_visible():
                    btn.first.click()
                    time.sleep(1)
                    self.wait_for_loading()
                    self._check_and_switch_tab()
                    if self._wait_for_returns_search_ready(timeout=15000):
                        Logger.success("Returns Dashboard loaded successfully.")
                        return True
        except Exception as e:
            Logger.warning(f"Dashboard reload attempt encountered: {e}")

        # 5. Last Resort: Direct URL navigation
        try:
            Logger.info("Attempting direct URL navigation to Returns Dashboard...")
            self.page.goto(GST_RETURNS_DASHBOARD_URL, wait_until="domcontentloaded", timeout=25000)
            self.wait_for_loading()
            self.dismiss_portal_popups()
            if self._wait_for_returns_search_ready(timeout=15000):
                Logger.success("Returns Dashboard reached via direct URL.")
                return True
        except Exception as e:
            Logger.error(f"Direct URL navigation failed: {e}")

        Logger.error(f"Could not reach Returns Dashboard. Current URL: {self.page.url} | Title: {self.page.title()}")
        return False

    def select_period(self, fy: str, quarter: str, month: str) -> bool:
        """
        Selects Financial Year, Quarter, and Return Period (Month) on Returns Dashboard,
        then clicks the SEARCH button.
        """
        Logger.info(f"Selecting Period: FY={fy}, Quarter={quarter}, Month={month}")
        try:
            self.wait_for_loading()

            # 1. Select Financial Year
            fy_select = self.page.locator("select#fin, select[name='fin'], select[id*='fin']")
            if fy_select.count() > 0:
                options = fy_select.first.locator("option").all_inner_texts()
                clean_fy = fy.strip().lower()
                matched_fy = None
                
                # Check match in options
                for opt in options:
                    c_opt = opt.strip().lower()
                    if not c_opt or "select" in c_opt:
                        continue
                    if clean_fy == c_opt or clean_fy in c_opt or c_opt in clean_fy:
                        matched_fy = opt.strip()
                        break
                    # If 4-digit start year matches (e.g. 2026 matches 2026-27 or 2026-2027)
                    if len(clean_fy) >= 4 and clean_fy[:4] in c_opt:
                        matched_fy = opt.strip()
                        break

                if matched_fy:
                    Logger.info(f"Selecting Financial Year: '{matched_fy}'")
                    fy_select.first.select_option(label=matched_fy)
                else:
                    Logger.warning(f"FY '{fy}' not found among options {options}. Trying direct selection...")
                    fy_select.first.select_option(label=fy)

                self.wait_for_loading()
                time.sleep(0.5)

            # 2. Select Quarter (if dropdown exists and is visible)
            quarter_select = self.page.locator("select#quarter, select[name='quarter'], select[id*='quarter']")
            if quarter_select.count() > 0 and quarter_select.first.is_visible():
                options = quarter_select.first.locator("option").all_inner_texts()
                matched_opt = None
                for opt in options:
                    c_opt = opt.strip().lower()
                    if quarter.lower() in c_opt or f"quarter {quarter[-1]}" in c_opt:
                        matched_opt = opt.strip()
                        break
                if matched_opt:
                    Logger.info(f"Selecting Quarter: '{matched_opt}'")
                    quarter_select.first.select_option(label=matched_opt)
                    self.wait_for_loading()
                    time.sleep(0.5)

            # 3. Select Month / Period
            month_select = self.page.locator("select#mon, select[name='mon'], select[id*='mon']")
            if month_select.count() > 0:
                options = month_select.first.locator("option").all_inner_texts()
                matched_month = None
                for opt in options:
                    if month.lower() in opt.strip().lower():
                        matched_month = opt.strip()
                        break
                if matched_month:
                    Logger.info(f"Selecting Month: '{matched_month}'")
                    month_select.first.select_option(label=matched_month)
                else:
                    month_select.first.select_option(label=month)
                self.wait_for_loading()
                time.sleep(0.5)

            # 4. Click SEARCH
            search_btn = self.page.locator("button:has-text('SEARCH'), button:has-text('Search'), input[value='SEARCH'], #search")
            if search_btn.count() > 0:
                search_btn.first.click()
                self.wait_for_loading(timeout=25000)
                Logger.info("Search triggered, awaiting return tiles...")
                time.sleep(1.5)
                return True
            else:
                Logger.error("Search button not found on Returns Dashboard.")
                return False

        except Exception as e:
            Logger.error(f"Error selecting period ({fy} - {month}): {e}")
            return False

    @abstractmethod
    def run(self, *args, **kwargs):
        """Entry method to execute the module task."""
        pass
