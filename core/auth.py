import time
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from config.settings import GST_LOGIN_URL, GST_DASHBOARD_URL, CAPTCHA_TIMEOUT
from utils.logger import Logger

class AuthManager:
    """Handles GST portal authentication, captcha prompt, and session verification."""

    def __init__(self, page: Page):
        self.page = page

    def is_logged_in(self) -> bool:
        """Checks if current page is in an authenticated session."""
        current_url = self.page.url.lower()
        if "/auth/" in current_url:
            return True
        try:
            # Check for common dashboard/logout elements
            logout_btn = self.page.locator("a:has-text('Logout'), button:has-text('Logout')")
            return logout_btn.count() > 0
        except Exception:
            return False

    def login(self, username: str, password: str, client_name: str = "", gstin: str = "") -> bool:
        """
        Navigates to the GST portal login page, fills credentials, 
        and waits for the user to complete the Captcha and any 2FA/OTP.
        """
        display_name = client_name or gstin or username
        Logger.header(f"Authenticating Client: {display_name}")

        try:
            Logger.info(f"Navigating to {GST_LOGIN_URL}...")
            self.page.goto(GST_LOGIN_URL, wait_until="networkidle", timeout=45000)

            # Wait for login form elements
            self.page.wait_for_selector("#username", timeout=15000)
            
            # Fill username and password
            Logger.info("Entering username and password...")
            self.page.fill("#username", "")
            self.page.fill("#username", username)
            
            self.page.fill("#user_pass", "")
            self.page.fill("#user_pass", password)

            # Focus the captcha input box
            if self.page.locator("#captcha").count() > 0:
                self.page.focus("#captcha")

            Logger.prompt("CAPTCHA REQUIRED:")
            print("  -> Please view the browser window, type the Captcha characters, and click 'Login'.")
            print("  -> (If 2FA/OTP is prompted, please complete it on the browser as well.)")
            Logger.info("Waiting for successful login to dashboard...")

            # Wait for navigation to dashboard or URL containing /auth/
            start_time = time.time()
            max_wait = CAPTCHA_TIMEOUT / 1000  # seconds

            while time.time() - start_time < max_wait:
                # Check if dashboard reached
                if self.is_logged_in():
                    Logger.success(f"Login successful for {display_name}!")
                    # Wait for dashboard to settle
                    time.sleep(2)
                    return True

                # Check for portal error messages
                error_elem = self.page.locator(".err-msg, .alert-danger, .error-msg, span.text-danger")
                if error_elem.count() > 0:
                    for i in range(error_elem.count()):
                        txt = error_elem.nth(i).text_content()
                        if txt and txt.strip() and ("invalid" in txt.lower() or "error" in txt.lower() or "failed" in txt.lower()):
                            Logger.warning(f"Portal message: {txt.strip()}")

                time.sleep(1)

            Logger.error("Login timed out. Dashboard was not reached.")
            return False

        except PlaywrightTimeoutError as e:
            Logger.error(f"Timeout during login process: {e}")
            return False
        except Exception as e:
            Logger.error(f"Unexpected error during login: {e}")
            return False

    def logout(self):
        """Logs out of the GST portal session."""
        try:
            logout_btn = self.page.locator("a:has-text('Logout'), button:has-text('Logout')")
            if logout_btn.count() > 0:
                Logger.info("Logging out from portal...")
                logout_btn.first.click()
                self.page.wait_for_load_state("networkidle", timeout=10000)
                Logger.success("Logged out successfully.")
        except Exception as e:
            Logger.warning(f"Could not logout cleanly: {e}")
