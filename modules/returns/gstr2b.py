import time
from pathlib import Path
from typing import List, Dict, Optional
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from modules.base import BaseModule
from utils.file_manager import FileManager
from utils.logger import Logger
from utils.period_helper import get_month_sort_prefix


class GSTR2BDownloader(BaseModule):
    """Handles downloading GSTR-2B Detailed Excel files for single or multiple periods."""

    def _locate_gstr2b_download_button(self):
        """
        Locates the specific DOWNLOAD button inside the GSTR-2B card,
        ensuring it does NOT target GSTR-1, GSTR-1A, GSTR-2A, or GSTR-3B.
        """
        # Approach 1: Inspect individual cards/panels and check for GSTR-2B exclusivity
        cards = self.page.locator(".card, .panel, .tile, div[class*='col-']").all()
        for card in cards:
            try:
                card_text = card.inner_text()
                # Must contain GSTR-2B / GSTR 2B and NOT GSTR-1 or GSTR-3B or GSTR-2A
                if (("GSTR-2B" in card_text or "GSTR 2B" in card_text or "Auto-drafted ITC Statement" in card_text)
                    and "GSTR-1" not in card_text
                    and "GSTR-3B" not in card_text
                    and "GSTR-2A" not in card_text):
                    
                    btn = card.locator("button:has-text('DOWNLOAD'), a:has-text('DOWNLOAD'), button:has-text('Download'), a:has-text('Download')")
                    if btn.count() > 0 and btn.first.is_visible():
                        return btn.first
            except Exception:
                continue

        # Approach 2: Targeted XPath finding the card container of GSTR-2B heading
        xpath_selectors = [
            "xpath=(//*[contains(text(), 'GSTR-2B') or contains(text(), 'GSTR 2B')]/ancestor::div[contains(@class, 'card') or contains(@class, 'panel') or contains(@class, 'box') or contains(@class, 'tile') or contains(@class, 'col')])[1]//button[contains(translate(text(), 'download', 'DOWNLOAD'), 'DOWNLOAD')]",
            "xpath=(//*[contains(text(), 'GSTR-2B') or contains(text(), 'GSTR 2B')]/ancestor::div[contains(@class, 'card') or contains(@class, 'panel') or contains(@class, 'box') or contains(@class, 'tile') or contains(@class, 'col')])[1]//a[contains(translate(text(), 'download', 'DOWNLOAD'), 'DOWNLOAD')]",
            "xpath=//div[contains(., 'GSTR-2B') and not(contains(., 'GSTR-1')) and not(contains(., 'GSTR-3B')) and not(contains(., 'GSTR-2A'))]//button[contains(translate(text(), 'download', 'DOWNLOAD'), 'DOWNLOAD')]",
            "xpath=//div[contains(., 'GSTR-2B') and not(contains(., 'GSTR-1')) and not(contains(., 'GSTR-3B')) and not(contains(., 'GSTR-2A'))]//a[contains(translate(text(), 'download', 'DOWNLOAD'), 'DOWNLOAD')]"
        ]

        for xp in xpath_selectors:
            loc = self.page.locator(xp)
            if loc.count() > 0 and loc.first.is_visible():
                return loc.first

        return None

    def _locate_generate_excel_button(self):
        """
        Locates the 'Generate Excel' button on https://gstr2b.gst.gov.in/gstr2b/auth/gstr2bdwld.
        Exact user XPath: /html/body/app-root/div[2]/app-gstr2bdwld/block-ui/div/div[2]/div/div[6]/button
        """
        selectors = [
            # User exact XPath
            "xpath=/html/body/app-root/div[2]/app-gstr2bdwld/block-ui/div/div[2]/div/div[6]/button",
            # Angular component scoped
            "xpath=//app-gstr2bdwld//div[contains(@class, 'block-ui')]//button[contains(translate(., 'EXCEL', 'excel'), 'excel')]",
            "xpath=//app-gstr2bdwld//button[contains(translate(., 'EXCEL', 'excel'), 'excel')]",
            # Button text matches
            "button:has-text('Generate Excel')",
            "button:has-text('General Excel')",
            "button:has-text('GENERATE EXCEL')",
            "button:has-text('Generate Excel File to Download')",
            "button:has-text('Generate Excel File')",
            "xpath=//button[contains(translate(., 'EXCEL', 'excel'), 'excel')]",
            "xpath=//button[contains(., 'Excel')]"
        ]

        for sel in selectors:
            loc = self.page.locator(sel)
            if loc.count() > 0 and loc.first.is_visible():
                Logger.info(f"Located 'Generate Excel' button via '{sel}': '{loc.first.inner_text().strip()}'")
                return loc.first

        return None

    def _locate_detailed_download_option(self):
        """
        Locates the 'GSTR-2B Details - Part 1' download link in the download table.
        Exact user XPath: /html/body/app-root/div[2]/app-gstr2bdwld/block-ui/div/div[2]/div/div[7]/table/tr[2]/td[2]/a
        """
        selectors = [
            # 1. Exact user XPath
            "xpath=/html/body/app-root/div[2]/app-gstr2bdwld/block-ui/div/div[2]/div/div[7]/table/tr[2]/td[2]/a",
            # 2. Scoped inside app-gstr2bdwld table
            "xpath=//app-gstr2bdwld//table//tr[2]/td[2]/a",
            "xpath=//app-gstr2bdwld//table//tr[2]//a",
            "xpath=//app-gstr2bdwld//table//tr[contains(., 'Details') or contains(., 'Part 1')]//td[2]//a",
            "xpath=//app-gstr2bdwld//table//tr[contains(., 'Details') or contains(., 'Part 1')]//a",
            # 3. Row matching across any table
            "xpath=//tr[contains(., 'Details') or contains(., 'Part 1')]//td[2]//a",
            "xpath=//tr[contains(., 'Details') or contains(., 'Part 1')]//a",
            "xpath=//tr[contains(., 'GSTR-2B Details')]//a",
            # 4. By link text 'Download here' (the 2nd one is Details - Part 1)
            "xpath=(//a[contains(translate(., 'DOWNLOAD HERE', 'download here'), 'download here')])[2]",
            "xpath=//a[contains(translate(., 'DOWNLOAD HERE', 'download here'), 'download here') and ancestor::tr[contains(., 'Details') or contains(., 'Part 1')]]",
            "xpath=//tr[contains(translate(., 'DETAILED', 'detailed'), 'detailed')]//a",
            # 5. Fallbacks
            "a:has-text('Download here')",
            "a:has-text('Detailed')",
            "button:has-text('Detailed')"
        ]

        for sel in selectors:
            loc = self.page.locator(sel)
            if loc.count() > 0:
                for i in range(loc.count()):
                    item = loc.nth(i)
                    if item.is_visible():
                        Logger.info(f"Located 'GSTR-2B Details - Part 1' link via '{sel}': '{item.inner_text().strip()}'")
                        return item

        return None

    def _click_back_button(self) -> bool:
        """
        Clicks the BACK button on the GSTR-2B download page to return directly
        to the period selection page.
        Exact user XPath: /html/body/app-root/div[2]/app-gstr2bdwld/block-ui/div/div[2]/div/div[8]/div[2]/button
        """
        back_selectors = [
            "xpath=/html/body/app-root/div[2]/app-gstr2bdwld/block-ui/div/div[2]/div/div[8]/div[2]/button",
            "xpath=//app-gstr2bdwld//div[contains(@class, 'block-ui')]//button[contains(translate(text(), 'BACK', 'back'), 'back')]",
            "xpath=//app-gstr2bdwld//button[contains(translate(text(), 'BACK', 'back'), 'back')]",
            "button:has-text('BACK')",
            "button:has-text('Back')",
            "xpath=//button[contains(text(), 'BACK') or contains(text(), 'Back')]"
        ]
        for sel in back_selectors:
            loc = self.page.locator(sel)
            if loc.count() > 0 and loc.first.is_visible():
                Logger.info("Clicking 'BACK' button to return to period selection...")
                loc.first.click()
                time.sleep(1)
                self.wait_for_loading()
                if self._wait_for_returns_search_ready(timeout=10000):
                    Logger.success("Returned to period selection screen.")
                    return True
        return False

    def download_for_period(self, fy: str, quarter: str, month: str) -> Optional[Path]:
        """
        Full workflow according to GST Portal:
        1. Dashboard -> File Returns
        2. Select FY, Quarter, Month -> Search
        3. Identify GSTR-2B card -> Click 'DOWNLOAD'
        4. Navigates to https://gstr2b.gst.gov.in/gstr2b/auth/gstr2bdwld
        5. If 'Details - Part 1' is already available, click it directly.
        6. Otherwise, click 'Generate Excel' button:
           - Case A: If company data is not huge, direct Excel download starts automatically!
           - Case B: If company data is huge, 'GSTR-2B Details - Part 1' link appears in table -> Click it!
        7. Save to downloads/{GSTIN}/{FY}/GSTR-2B/
        8. Click 'BACK' to return to period selection for the next period.
        """
        Logger.header(f"GSTR-2B Download: {self.gstin} | FY: {fy} | Month: {month}")

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

        # Step 3: Locate GSTR-2B tile and click DOWNLOAD
        Logger.info("Locating GSTR-2B card on Returns Dashboard...")
        gstr2b_download_btn = self._locate_gstr2b_download_button()

        if not gstr2b_download_btn:
            Logger.error(f"GSTR-2B DOWNLOAD button not found for {month} {fy}. Ensure return data is generated on portal.")
            return None

        Logger.success("Found GSTR-2B card. Clicking 'DOWNLOAD'...")
        gstr2b_download_btn.click()
        time.sleep(2)
        self.wait_for_loading()

        # Target directory setup
        target_dir = FileManager.get_download_path(self.gstin, fy, "GSTR-2B", month)
        download = None

        try:
            # Wait for GSTR-2B download screen to stabilize
            try:
                self.page.wait_for_selector(
                    "app-gstr2bdwld, button:has-text('Generate'), button:has-text('Excel')",
                    timeout=15000
                )
            except Exception:
                pass

            def _do_save(dl) -> Optional[Path]:
                """Saves a Playwright Download object immediately using save_as() before cleanup."""
                try:
                    ext = Path(dl.suggested_filename).suffix or ".xlsx"
                    sort_month = get_month_sort_prefix(month)
                    final_filename = f"GSTR2B_{self.gstin}_{sort_month}_{fy.replace('-', '_')}_Detailed{ext}"
                    path = FileManager.save_playwright_download(dl, target_dir, final_filename)
                    # Automatically click BACK to return to period selection for multi-month runs
                    self._click_back_button()
                    return path
                except Exception as save_err:
                    Logger.error(f"Error saving file: {save_err}")
                    return None

            # Step 4: Check if 'GSTR-2B Details - Part 1' table is ALREADY present
            detailed_link = self._locate_detailed_download_option()

            if detailed_link:
                Logger.info("Found 'GSTR-2B Details - Part 1' already displayed on screen. Initiating download...")
                try:
                    with self.page.expect_download(timeout=60000) as download_info:
                        detailed_link.click()
                    saved_path = _do_save(download_info.value)
                    if saved_path:
                        Logger.success(f"GSTR-2B Detailed Excel downloaded successfully for {month} {fy}!")
                        return saved_path
                    return None
                except PlaywrightTimeoutError:
                    Logger.error("Download did not start within timeout.")
                    return None

            # Step 5: Locate the 'Generate Excel' button
            generate_btn = self._locate_generate_excel_button()
            if not generate_btn:
                Logger.error("Could not locate 'Generate Excel' button on download page.")
                return None

            Logger.info("Clicking 'Generate Excel' button...")

            # Case A: Direct download for smaller datasets (wait 8s for immediate download)
            try:
                with self.page.expect_download(timeout=8000) as download_info:
                    generate_btn.click()
                Logger.success("Direct Excel download started automatically!")
                saved_path = _do_save(download_info.value)
                if saved_path:
                    Logger.success(f"GSTR-2B Detailed Excel downloaded successfully for {month} {fy}!")
                    return saved_path
                return None
            except PlaywrightTimeoutError:
                Logger.info("Direct download did not start immediately. Waiting for 'GSTR-2B Details - Part 1' table...")

            # Case B: Large dataset — wait for table with 'GSTR-2B Details - Part 1' link
            self.wait_for_loading()
            start_wait = time.time()
            detailed_link = None
            while time.time() - start_wait < 30:
                self.wait_for_loading()
                detailed_link = self._locate_detailed_download_option()
                if detailed_link:
                    break
                time.sleep(1)

            if detailed_link:
                Logger.success("Found 'GSTR-2B Details - Part 1' download link. Initiating download...")
                try:
                    with self.page.expect_download(timeout=60000) as download_info:
                        detailed_link.click()
                    saved_path = _do_save(download_info.value)
                    if saved_path:
                        Logger.success(f"GSTR-2B Detailed Excel downloaded successfully for {month} {fy}!")
                        return saved_path
                    return None
                except PlaywrightTimeoutError:
                    Logger.error("Download did not start within timeout.")
                    return None
            else:
                notice = self.page.locator(".alert-info, .alert-warning, .success-msg, .err-msg, span.text-info, p.text-info")
                if notice.count() > 0:
                    Logger.warning(f"Portal message: {notice.first.inner_text().strip()}")
                all_links = [l.inner_text().strip() for l in self.page.locator("a, button").all() if l.is_visible() and l.inner_text().strip()]
                Logger.error(f"Could not find 'GSTR-2B Details - Part 1' for {month} {fy}. Visible on page: {all_links[:10]}")
                return None

        except PlaywrightTimeoutError:
            Logger.error(f"Download request timed out for {month} {fy}.")
            return None
        except Exception as e:
            Logger.error(f"Error during GSTR-2B download: {e}")
            return None

    def download_multiple_periods(self, periods: List[Dict[str, str]]) -> Dict[str, Optional[Path]]:
        """Downloads GSTR-2B Detailed Excel for a list of periods [{'fy': ..., 'quarter': ..., 'month': ...}]."""
        results = {}
        total = len(periods)
        Logger.header(f"Starting Batch GSTR-2B Detailed Download ({total} Periods)")

        for index, p in enumerate(periods, start=1):
            fy = p["fy"]
            quarter = p["quarter"]
            month = p["month"]
            
            Logger.info(f"[{index}/{total}] Processing {month} ({fy})...")
            saved_file = self.download_for_period(fy, quarter, month)
            results[f"{month}_{fy}"] = saved_file

            # Brief pause between downloads to maintain portal session health
            time.sleep(2)

        # Summary report
        success_count = sum(1 for v in results.values() if v is not None)
        Logger.header("GSTR-2B Batch Download Summary")
        Logger.info(f"Total Periods: {total}")
        Logger.info(f"Downloaded Successfully: {success_count}")
        if success_count < total:
            Logger.warning(f"Failed / Unavailable: {total - success_count}")

        return results

    def run(self, periods: List[Dict[str, str]]) -> Dict[str, Optional[Path]]:
        """Main execution entrypoint for GSTR-2B."""
        if len(periods) == 1:
            p = periods[0]
            path = self.download_for_period(p["fy"], p["quarter"], p["month"])
            return {f"{p['month']}_{p['fy']}": path}
        else:
            return self.download_multiple_periods(periods)
