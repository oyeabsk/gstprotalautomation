import time
from pathlib import Path
from typing import Optional, List, Dict
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from modules.base import BaseModule
from utils.logger import Logger
from utils.file_manager import FileManager
from utils.period_helper import get_month_sort_prefix


class GSTR3BDownloader(BaseModule):
    """
    Automates downloading GSTR-3B filed returns (PDF format) from the GST Portal.
    Workflow:
      1. Navigate to Returns Dashboard
      2. Select Period (FY, Quarter, Month) -> Click 'SEARCH'
      3. Locate GSTR-3B card and click 'DOWNLOAD'
      4. Save downloaded PDF to downloads/{GSTIN}/{FY}/GSTR-3B/
      5. Directly ready on same page for next period selection
    """

    def _locate_gstr3b_download_button(self):
        """
        Locates the specific DOWNLOAD button inside the GSTR-3B card,
        ensuring it does NOT target GSTR-1, GSTR-1A, GSTR-2A, or GSTR-2B.
        Exact user XPath: /html/body/div[2]/div[2]/div/div[2]/div[4]/div[3]/div[2]/div[1]/div/div/div/div[2]/button
        """
        # Approach 1: User's exact XPath
        user_xpath = "xpath=/html/body/div[2]/div[2]/div/div[2]/div[4]/div[3]/div[2]/div[1]/div/div/div/div[2]/button"
        try:
            btn = self.page.locator(user_xpath)
            if btn.count() > 0 and btn.first.is_visible():
                Logger.info("Found GSTR-3B DOWNLOAD button via user XPath.")
                return btn.first
        except Exception:
            pass

        # Approach 2: Inspect individual cards/panels and check for GSTR-3B exclusivity
        cards = self.page.locator(".card, .panel, .tile, div[class*='col-']").all()
        for card in cards:
            try:
                card_text = card.inner_text()
                # Must contain GSTR-3B / GSTR 3B and NOT GSTR-1 or GSTR-2B or GSTR-2A
                if (("GSTR-3B" in card_text or "GSTR 3B" in card_text or "Monthly Return GSTR-3B" in card_text)
                    and "GSTR-1" not in card_text
                    and "GSTR-2B" not in card_text
                    and "GSTR-2A" not in card_text):
                    
                    btn = card.locator("button:has-text('DOWNLOAD'), a:has-text('DOWNLOAD'), button:has-text('Download'), a:has-text('Download')")
                    if btn.count() > 0 and btn.first.is_visible():
                        Logger.info("Found GSTR-3B DOWNLOAD button via card text isolation.")
                        return btn.first
            except Exception:
                continue

        # Approach 3: Targeted XPath finding the card container of GSTR-3B heading
        xpath_selectors = [
            "xpath=(//*[contains(text(), 'GSTR-3B') or contains(text(), 'GSTR 3B')]/ancestor::div[contains(@class, 'card') or contains(@class, 'panel') or contains(@class, 'box') or contains(@class, 'tile') or contains(@class, 'col')])[1]//button[contains(translate(text(), 'download', 'DOWNLOAD'), 'DOWNLOAD')]",
            "xpath=(//*[contains(text(), 'GSTR-3B') or contains(text(), 'GSTR 3B')]/ancestor::div[contains(@class, 'card') or contains(@class, 'panel') or contains(@class, 'box') or contains(@class, 'tile') or contains(@class, 'col')])[1]//a[contains(translate(text(), 'download', 'DOWNLOAD'), 'DOWNLOAD')]",
            "xpath=//div[contains(., 'GSTR-3B') and not(contains(., 'GSTR-1')) and not(contains(., 'GSTR-2B')) and not(contains(., 'GSTR-2A'))]//button[contains(translate(text(), 'download', 'DOWNLOAD'), 'DOWNLOAD')]",
            "xpath=//div[contains(., 'GSTR-3B') and not(contains(., 'GSTR-1')) and not(contains(., 'GSTR-2B')) and not(contains(., 'GSTR-2A'))]//a[contains(translate(text(), 'download', 'DOWNLOAD'), 'DOWNLOAD')]"
        ]

        for xp in xpath_selectors:
            loc = self.page.locator(xp)
            if loc.count() > 0 and loc.first.is_visible():
                Logger.info("Found GSTR-3B DOWNLOAD button via semantic XPath.")
                return loc.first

        return None

    def download_for_period(self, fy: str, quarter: str, month: str) -> Optional[Path]:
        """
        Downloads GSTR-3B PDF for a specific period:
        1. Ensure on Returns Dashboard
        2. Select period & Search
        3. Click DOWNLOAD button on GSTR-3B tile
        4. Save PDF to downloads/{GSTIN}/{FY}/GSTR-3B/
        """
        Logger.header(f"GSTR-3B Download: {self.gstin} | FY: {fy} | Month: {month}")

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

        # Step 3: Locate GSTR-3B card and click DOWNLOAD
        Logger.info("Locating GSTR-3B card on Returns Dashboard...")
        gstr3b_download_btn = self._locate_gstr3b_download_button()

        if not gstr3b_download_btn:
            Logger.error(f"GSTR-3B DOWNLOAD button not found for {month} {fy}. Ensure return is filed.")
            return None

        Logger.success("Found GSTR-3B card. Clicking 'DOWNLOAD'...")

        target_dir = FileManager.get_download_path(self.gstin, fy, "GSTR-3B", month)

        try:
            with self.page.expect_download(timeout=60000) as download_info:
                gstr3b_download_btn.click()
            
            download = download_info.value
            ext = Path(download.suggested_filename).suffix or ".pdf"
            sort_month = get_month_sort_prefix(month)
            final_filename = f"GSTR3B_{self.gstin}_{sort_month}_{fy.replace('-', '_')}{ext}"
            
            saved_path = FileManager.save_playwright_download(download, target_dir, final_filename)
            Logger.success(f"GSTR-3B PDF downloaded successfully for {month} {fy}!")
            return saved_path

        except PlaywrightTimeoutError:
            Logger.error(f"Download did not start within timeout for {month} {fy}.")
            return None
        except Exception as e:
            Logger.error(f"Error during GSTR-3B download: {e}")
            return None

    def download_multiple_periods(self, periods: List[Dict[str, str]]) -> Dict[str, Optional[Path]]:
        """Downloads GSTR-3B PDF for a list of periods [{'fy': ..., 'quarter': ..., 'month': ...}]."""
        results = {}
        total = len(periods)
        Logger.header(f"Starting Batch GSTR-3B PDF Download ({total} Periods)")

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
        Logger.header("GSTR-3B Batch Download Summary")
        Logger.info(f"Total Periods: {total}")
        Logger.info(f"Downloaded Successfully: {success_count}")
        for period_key, path in results.items():
            status = f"[OK] {path.name}" if path else "[FAILED]"
            print(f"  * {period_key}: {status}")

        return results

    def run(self, periods: Optional[List[Dict[str, str]]] = None):
        """Entry point called by main controller."""
        if not periods:
            Logger.error("No period specified for GSTR-3B download.")
            return

        if len(periods) == 1:
            p = periods[0]
            self.download_for_period(p["fy"], p["quarter"], p["month"])
        else:
            self.download_multiple_periods(periods)

# Alias for backward compatibility
GSTR3BHandler = GSTR3BDownloader
