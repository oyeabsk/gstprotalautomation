import time
from pathlib import Path
from typing import Optional, List, Dict
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from modules.base import BaseModule
from utils.logger import Logger
from utils.file_manager import FileManager
from utils.period_helper import get_month_sort_prefix

class GSTR1Downloader(BaseModule):
    """
    Automates downloading GSTR-1 filed returns (PDF Summary format) from the GST Portal.
    Workflow:
      1. Navigate to Returns Dashboard
      2. Select Period (FY, Quarter, Month) -> Click 'SEARCH'
      3. Locate GSTR-1 card and click 'VIEW' button
      4. Scroll down on GSTR-1 page and click 'View Summary' button
      5. Scroll down to bottom of summary page and click 'Download (PDF)' button
      6. Save downloaded PDF to downloads/{GSTIN}/{FY}/GSTR-1/
      7. Click 'BACK' button 1 on Summary page (/html/body/div[2]/div[2]/div/div[2]/div/div/div[3]/div[4]/div/button[1])
      8. Click 'BACK' button 2 on GSTR-1 page (/html/body/div[2]/div[2]/div/div[2]/div[7]/div/a)
      9. Directly ready on select period page for the next period!
    """

    def _locate_gstr1_view_button(self):
        """
        Locates the specific VIEW button inside the GSTR-1 card,
        ensuring it does NOT target GSTR-1A, GSTR-2A, GSTR-2B, or GSTR-3B.
        Exact user XPath: /html/body/div[2]/div[2]/div/div[2]/div[4]/div[3]/div[1]/div[1]/div/div/div/div[1]/button
        """
        # Approach 1: User's exact XPath
        user_xpath = "xpath=/html/body/div[2]/div[2]/div/div[2]/div[4]/div[3]/div[1]/div[1]/div/div/div/div[1]/button"
        try:
            btn = self.page.locator(user_xpath)
            if btn.count() > 0 and btn.first.is_visible():
                Logger.info("Found GSTR-1 VIEW button via user XPath.")
                return btn.first
        except Exception:
            pass

        # Approach 2: Inspect cards and check for GSTR-1 exclusivity (not GSTR-1A, not 2B, not 3B)
        cards = self.page.locator(".card, .panel, .tile, div[class*='col-']").all()
        for card in cards:
            try:
                card_text = card.inner_text()
                if (("GSTR-1" in card_text or "GSTR 1" in card_text or "Details of outward supplies" in card_text)
                    and "GSTR-1A" not in card_text
                    and "GSTR-2B" not in card_text
                    and "GSTR-3B" not in card_text
                    and "GSTR-2A" not in card_text):
                    
                    btn = card.locator("button:has-text('VIEW'), a:has-text('VIEW'), button:has-text('View'), a:has-text('View')")
                    if btn.count() > 0 and btn.first.is_visible():
                        Logger.info("Found GSTR-1 VIEW button via card text isolation.")
                        return btn.first
            except Exception:
                continue

        # Approach 3: Targeted XPath finding the card container of GSTR-1 heading
        xpath_selectors = [
            "xpath=(//*[(contains(text(), 'GSTR-1') or contains(text(), 'GSTR 1')) and not(contains(text(), 'GSTR-1A'))]/ancestor::div[contains(@class, 'card') or contains(@class, 'panel') or contains(@class, 'box') or contains(@class, 'tile') or contains(@class, 'col')])[1]//button[contains(translate(text(), 'view', 'VIEW'), 'VIEW')]",
            "xpath=(//*[(contains(text(), 'GSTR-1') or contains(text(), 'GSTR 1')) and not(contains(text(), 'GSTR-1A'))]/ancestor::div[contains(@class, 'card') or contains(@class, 'panel') or contains(@class, 'box') or contains(@class, 'tile') or contains(@class, 'col')])[1]//a[contains(translate(text(), 'view', 'VIEW'), 'VIEW')]",
            "xpath=//div[contains(., 'GSTR-1') and not(contains(., 'GSTR-1A')) and not(contains(., 'GSTR-2B')) and not(contains(., 'GSTR-3B'))]//button[contains(translate(text(), 'view', 'VIEW'), 'VIEW')]",
            "xpath=//div[contains(., 'GSTR-1') and not(contains(., 'GSTR-1A')) and not(contains(., 'GSTR-2B')) and not(contains(., 'GSTR-3B'))]//a[contains(translate(text(), 'view', 'VIEW'), 'VIEW')]"
        ]

        for xp in xpath_selectors:
            loc = self.page.locator(xp)
            if loc.count() > 0 and loc.first.is_visible():
                Logger.info("Found GSTR-1 VIEW button via semantic XPath.")
                return loc.first

        return None

    def _locate_view_summary_button(self):
        """
        Locates the 'View Summary' button on the GSTR-1 details page.
        Exact user XPath: /html/body/div[2]/div[2]/div/div[2]/div[7]/div/div/button[2]/span[2]
        """
        # Scroll down first so footer buttons are rendered into view
        try:
            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1)
        except Exception:
            pass

        selectors = [
            # User exact XPath
            "xpath=/html/body/div[2]/div[2]/div/div[2]/div[7]/div/div/button[2]/span[2]",
            "xpath=/html/body/div[2]/div[2]/div/div[2]/div[7]/div/div/button[2]",
            # Semantic text selectors
            "button:has-text('View Summary')",
            "button:has-text('VIEW SUMMARY')",
            "button:has-text('Generate Summary')",
            "xpath=//button[contains(translate(., 'view summary', 'VIEW SUMMARY'), 'VIEW SUMMARY')]",
            "xpath=//button[.//span[contains(translate(., 'view summary', 'VIEW SUMMARY'), 'VIEW SUMMARY')]]",
            "xpath=//button[contains(., 'Summary') or contains(., 'summary')]"
        ]

        for sel in selectors:
            loc = self.page.locator(sel)
            if loc.count() > 0 and loc.first.is_visible():
                Logger.info(f"Located 'View Summary' button via '{sel}'.")
                return loc.first

        return None

    def _locate_download_pdf_button(self):
        """
        Locates the 'Download (PDF)' button on the GSTR-1 summary page.
        Exact user XPath: /html/body/div[2]/div[2]/div/div[2]/div/div/div[3]/div[4]/div/button[2]/span[2]
        """
        # Scroll down to bottom of summary page
        try:
            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1)
        except Exception:
            pass

        selectors = [
            # User exact XPath
            "xpath=/html/body/div[2]/div[2]/div/div[2]/div/div/div[3]/div[4]/div/button[2]/span[2]",
            "xpath=/html/body/div[2]/div[2]/div/div[2]/div/div/div[3]/div[4]/div/button[2]",
            # Semantic text selectors
            "button:has-text('Download (PDF)')",
            "button:has-text('DOWNLOAD (PDF)')",
            "button:has-text('Download PDF')",
            "button:has-text('DOWNLOAD PDF')",
            "xpath=//button[contains(translate(., 'download (pdf)', 'DOWNLOAD (PDF)'), 'DOWNLOAD (PDF)')]",
            "xpath=//button[.//span[contains(translate(., 'download (pdf)', 'DOWNLOAD (PDF)'), 'DOWNLOAD (PDF)')]]",
            "xpath=//button[contains(., 'Download (PDF)') or contains(., 'DOWNLOAD (PDF)') or contains(., 'Download PDF')]"
        ]

        for sel in selectors:
            loc = self.page.locator(sel)
            if loc.count() > 0 and loc.first.is_visible():
                Logger.info(f"Located 'Download (PDF)' button via '{sel}'.")
                return loc.first

        return None

    def _return_to_period_selection(self) -> bool:
        """
        Navigates back from GSTR-1 Summary page to the period selection screen
        by clicking the exact 2 BACK buttons:
        1. Back button on Summary page (left side of 'Download (PDF)'):
           Exact XPath: /html/body/div[2]/div[2]/div/div[2]/div/div/div[3]/div[4]/div/button[1]
        2. Back button on GSTR-1 main page:
           Exact XPath: /html/body/div[2]/div[2]/div/div[2]/div[7]/div/a
        """
        Logger.info("Returning to period selection screen via BACK buttons...")

        # Step 1: Click 1st BACK button on Summary page (button 1 on left of Download PDF)
        back1_selectors = [
            "xpath=/html/body/div[2]/div[2]/div/div[2]/div/div/div[3]/div[4]/div/button[1]",
            "xpath=//button[contains(., 'Download (PDF)') or contains(., 'DOWNLOAD (PDF)') or contains(., 'Download PDF')]/preceding-sibling::button[1]",
            "xpath=/html/body/div[2]/div[2]/div/div[2]/div/div/div[3]/div[4]/div//button[contains(translate(., 'back', 'BACK'), 'BACK')]",
            "button:has-text('BACK')",
            "button:has-text('Back')"
        ]

        clicked_back1 = False
        for sel in back1_selectors:
            loc = self.page.locator(sel)
            if loc.count() > 0 and loc.first.is_visible():
                Logger.info(f"Clicking 1st BACK button (Summary -> GSTR-1) via '{sel}'...")
                loc.first.click()
                clicked_back1 = True
                time.sleep(1.5)
                self.wait_for_loading()
                break

        if not clicked_back1:
            Logger.warning("Could not find 1st BACK button by primary selectors, trying generic back button...")
            generic_btn = self.page.locator("button:has-text('BACK'), button:has-text('Back')")
            if generic_btn.count() > 0 and generic_btn.first.is_visible():
                generic_btn.first.click()
                time.sleep(1.5)
                self.wait_for_loading()

        # Check if already on Returns Dashboard
        if self._is_returns_search_ready():
            Logger.success("Returned to Returns Dashboard.")
            return True

        # Step 2: Click 2nd BACK button on GSTR-1 main page
        # Scroll to bottom if needed to ensure div[7] is in view
        try:
            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(0.5)
        except Exception:
            pass

        back2_selectors = [
            "xpath=/html/body/div[2]/div[2]/div/div[2]/div[7]/div/a",
            "xpath=/html/body/div[2]/div[2]/div/div[2]/div[7]/div//a",
            "xpath=//a[contains(translate(text(), 'BACK', 'back'), 'back') or contains(translate(., 'BACK', 'back'), 'back')]",
            "a:has-text('BACK')",
            "a:has-text('Back')",
            "button:has-text('BACK')",
            "button:has-text('Back')"
        ]

        clicked_back2 = False
        for sel in back2_selectors:
            loc = self.page.locator(sel)
            if loc.count() > 0 and loc.first.is_visible():
                Logger.info(f"Clicking 2nd BACK button (GSTR-1 -> Returns Dashboard) via '{sel}'...")
                loc.first.click()
                clicked_back2 = True
                time.sleep(1.5)
                self.wait_for_loading()
                break

        if not clicked_back2:
            Logger.warning("Could not find 2nd BACK button by primary selectors, trying generic back link/button...")
            generic_back = self.page.locator("a:has-text('BACK'), a:has-text('Back'), button:has-text('BACK'), button:has-text('Back')")
            if generic_back.count() > 0 and generic_back.first.is_visible():
                generic_back.first.click()
                time.sleep(1.5)
                self.wait_for_loading()

        # Step 3: Verify if on Returns Dashboard
        if self._wait_for_returns_search_ready(timeout=8000):
            Logger.success("Returned to Returns Dashboard successfully.")
            return True

        # Fallback to general dashboard navigation only if BACK didn't reach
        Logger.info("Returns search not immediately detected, checking popups and dashboard...")
        self.dismiss_portal_popups()
        return self.navigate_to_returns_dashboard()

    def download_for_period(self, fy: str, quarter: str, month: str) -> Optional[Path]:
        """
        Downloads GSTR-1 PDF Summary for a specific period:
        1. Ensure on Returns Dashboard
        2. Select period & Search
        3. Click 'VIEW' on GSTR-1 tile
        4. Click 'View Summary'
        5. Click 'Download (PDF)'
        6. Save PDF to downloads/{GSTIN}/{FY}/GSTR-1/
        7. Click BACK twice to return to period selection
        """
        Logger.header(f"GSTR-1 Download: {self.gstin} | FY: {fy} | Month: {month}")

        # Step 1: Ensure we are on Returns Dashboard
        if not self.navigate_to_returns_dashboard():
            Logger.error("Could not reach Returns Dashboard.")
            return None

        # Step 2: Select period and Search
        if not self.select_period(fy, quarter, month):
            Logger.error(f"Failed to select period {month} ({fy}).")
            return None

        time.sleep(2)
        self.wait_for_loading()

        # Step 3: Locate GSTR-1 card and click VIEW
        Logger.info("Locating GSTR-1 card on Returns Dashboard...")
        gstr1_view_btn = self._locate_gstr1_view_button()

        if not gstr1_view_btn:
            Logger.error(f"GSTR-1 VIEW button not found for {month} {fy}. Ensure return is filed.")
            return None

        Logger.success("Found GSTR-1 card. Clicking 'VIEW'...")
        gstr1_view_btn.click()
        time.sleep(2)
        self.wait_for_loading()

        # Step 4: Scroll down and click 'View Summary'
        Logger.info("Waiting for GSTR-1 page to load and locating 'View Summary' button...")
        start_wait = time.time()
        view_summary_btn = None
        while time.time() - start_wait < 25:
            self.wait_for_loading()
            view_summary_btn = self._locate_view_summary_button()
            if view_summary_btn:
                break
            time.sleep(1)

        if not view_summary_btn:
            Logger.error(f"Could not locate 'View Summary' button on GSTR-1 page for {month} {fy}.")
            self._return_to_period_selection()
            return None

        Logger.success("Clicking 'View Summary' button...")
        view_summary_btn.click()
        time.sleep(2)
        self.wait_for_loading()

        # Step 5: Locate 'Download (PDF)' button and capture download
        Logger.info("Locating 'Download (PDF)' button on summary page...")
        start_wait = time.time()
        download_pdf_btn = None
        while time.time() - start_wait < 25:
            self.wait_for_loading()
            download_pdf_btn = self._locate_download_pdf_button()
            if download_pdf_btn:
                break
            time.sleep(1)

        if not download_pdf_btn:
            Logger.error(f"Could not locate 'Download (PDF)' button for {month} {fy}.")
            self._return_to_period_selection()
            return None

        Logger.success("Found 'Download (PDF)' button. Initiating download...")
        target_dir = FileManager.get_download_path(self.gstin, fy, "GSTR-1", month)

        saved_path = None
        try:
            with self.page.expect_download(timeout=60000) as download_info:
                download_pdf_btn.click()

            download = download_info.value
            ext = Path(download.suggested_filename).suffix or ".pdf"
            sort_month = get_month_sort_prefix(month)
            final_filename = f"GSTR1_{self.gstin}_{sort_month}_{fy.replace('-', '_')}{ext}"

            saved_path = FileManager.save_playwright_download(download, target_dir, final_filename)
            Logger.success(f"GSTR-1 PDF downloaded successfully for {month} {fy}!")

        except PlaywrightTimeoutError:
            Logger.error(f"Download did not start within timeout for {month} {fy}.")
        except Exception as e:
            Logger.error(f"Error during GSTR-1 download: {e}")

        # Step 6: Return to period selection screen via 2 BACK clicks
        self._return_to_period_selection()

        return saved_path

    def download_multiple_periods(self, periods: List[Dict[str, str]]) -> Dict[str, Optional[Path]]:
        """Downloads GSTR-1 PDF for a list of periods [{'fy': ..., 'quarter': ..., 'month': ...}]."""
        results = {}
        total = len(periods)
        Logger.header(f"Starting Batch GSTR-1 PDF Download ({total} Periods)")

        for index, p in enumerate(periods, start=1):
            fy = p["fy"]
            quarter = p["quarter"]
            month = p["month"]

            Logger.info(f"[{index}/{total}] Processing {month} ({fy})...")
            saved_file = self.download_for_period(fy, quarter, month)
            results[f"{month}_{fy}"] = saved_file

            # Brief pause between downloads
            time.sleep(2)

        # Summary report
        success_count = sum(1 for v in results.values() if v is not None)
        Logger.header("GSTR-1 Batch Download Summary")
        Logger.info(f"Total Periods: {total}")
        Logger.info(f"Downloaded Successfully: {success_count}")
        for period_key, path in results.items():
            status = f"[OK] {path.name}" if path else "[FAILED]"
            print(f"  * {period_key}: {status}")

        return results

    def run(self, periods: Optional[List[Dict[str, str]]] = None):
        """Entry point called by main controller."""
        if not periods:
            Logger.error("No period specified for GSTR-1 download.")
            return

        if len(periods) == 1:
            p = periods[0]
            self.download_for_period(p["fy"], p["quarter"], p["month"])
        else:
            self.download_multiple_periods(periods)

# Alias for backward compatibility
GSTR1Handler = GSTR1Downloader
