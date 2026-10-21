import sys
import time
from core.client_manager import ClientManager
from core.browser import BrowserManager
from core.auth import AuthManager
from modules.returns.gstr2b import GSTR2BDownloader
from modules.returns.gstr1 import GSTR1Handler
from modules.returns.gstr3b import GSTR3BHandler
from modules.ledgers.cash_credit import LedgerHandler
from cli.menu import Menu
from utils.logger import Logger

def main():
    Logger.header("GST Portal Automation Hub")
    
    # Ensure client template exists
    ClientManager.create_template_file()

    browser_mgr = None

    try:
        while True:
            # Step 1: Select client
            client = Menu.select_client()
            if not client:
                Logger.info("Exiting application. Goodbye!")
                break

            gstin = client.get("gstin", "")
            username = client.get("username", "")
            password = client.get("password", "")
            client_name = client.get("client_name", "")

            # Step 2: Launch browser if not already running
            if not browser_mgr:
                browser_mgr = BrowserManager()
                page = browser_mgr.start()
            else:
                page = browser_mgr.page

            # Step 3: Login to portal
            auth = AuthManager(page)
            success = auth.login(username=username, password=password, client_name=client_name, gstin=gstin)

            if not success:
                retry = input("\nLogin failed. Would you like to retry? (y/n): ").strip().lower()
                if retry != "y":
                    auth.logout()
                    continue
                else:
                    success = auth.login(username=username, password=password, client_name=client_name, gstin=gstin)
                    if not success:
                        continue

            # Step 4: Authenticated Task Loop
            while True:
                choice = Menu.show_main_menu(client)

                if choice == "1":
                    # Download GSTR-2B
                    periods = Menu.prompt_gstr2b_periods()
                    if periods:
                        downloader = GSTR2BDownloader(page, gstin=gstin, client_name=client_name)
                        downloader.run(periods)
                        page = downloader.page
                        input("\nPress Enter to return to main menu...")

                elif choice == "2":
                    # Download GSTR-1 PDF (Single or Multiple Periods)
                    periods = Menu.prompt_periods("GSTR-1")
                    if periods:
                        downloader = GSTR1Handler(page, gstin=gstin, client_name=client_name)
                        downloader.run(periods)
                        page = downloader.page
                        input("\nPress Enter to return to main menu...")

                elif choice == "3":
                    # Download GSTR-3B PDF (Single or Multiple Periods)
                    periods = Menu.prompt_periods("GSTR-3B")
                    if periods:
                        downloader = GSTR3BHandler(page, gstin=gstin, client_name=client_name)
                        downloader.run(periods)
                        page = downloader.page
                        input("\nPress Enter to return to main menu...")

                elif choice == "4":
                    # Cash & Credit Ledgers (Future)
                    ledgers = LedgerHandler(page, gstin=gstin, client_name=client_name)
                    ledgers.run()
                    input("\nPress Enter to return to main menu...")

                elif choice == "5":
                    Logger.warning("Return upload module is planned for an upcoming release.")
                    input("\nPress Enter to return to main menu...")

                elif choice == "6":
                    # Switch client
                    Logger.info("Logging out to switch client...")
                    auth.logout()
                    break

                elif choice == "0":
                    # Exit
                    Logger.info("Exiting GST Automation Hub...")
                    if auth.is_logged_in():
                        auth.logout()
                    return

                else:
                    Logger.warning("Invalid choice. Please select from the menu.")

    except KeyboardInterrupt:
        Logger.warning("\nExecution interrupted by user.")
    except Exception as e:
        Logger.error(f"Fatal error: {e}")
    finally:
        if browser_mgr:
            browser_mgr.close()

if __name__ == "__main__":
    main()
