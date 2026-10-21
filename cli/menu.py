import getpass
from typing import Optional, Dict, List
from core.client_manager import ClientManager
from config.settings import SUPPORTED_FYS, MONTH_NAMES, CLIENTS_FILE, CLIENTS_TEMPLATE_FILE
from utils.period_helper import get_single_period, get_period_range, get_all_periods_for_fy
from utils.logger import Logger

class Menu:
    """Provides interactive CLI menus for client selection and task configuration."""

    @staticmethod
    def select_client() -> Optional[Dict[str, str]]:
        """Displays available clients from master sheet or allows manual input."""
        while True:
            clients = ClientManager.get_active_clients()
            
            Logger.header("GST Portal Automation - Client Selection")
            if clients:
                print(f"Loaded {len(clients)} client(s) from '{CLIENTS_FILE.name}':\n")
                for idx, c in enumerate(clients, start=1):
                    name = c.get("client_name") or "Unnamed"
                    gstin = c.get("gstin") or "No GSTIN"
                    user = c.get("username")
                    print(f"  [{idx}] {name} ({gstin}) | User: {user}")
                print()
                print("  [M] Enter credentials manually")
                print("  [R] Reload clients.xlsx")
                print("  [0] Exit")

                choice = input("\nSelect an option: ").strip()
                if choice == "0":
                    return None
                elif choice.upper() == "M":
                    return Menu._prompt_manual_client()
                elif choice.upper() == "R":
                    continue
                elif choice.isdigit():
                    idx = int(choice)
                    if 1 <= idx <= len(clients):
                        return clients[idx - 1]
                    else:
                        Logger.warning("Invalid choice, please select a valid number.")
                else:
                    Logger.warning("Invalid option. Please try again.")
            else:
                Logger.warning(f"No active clients found in '{CLIENTS_FILE}'.")
                print(f"Template is available at: {CLIENTS_TEMPLATE_FILE}")
                print("\nOptions:")
                print("  [1] Enter credentials manually for this session")
                print("  [2] Reload after populating 'config/clients.xlsx'")
                print("  [0] Exit")
                
                choice = input("\nSelect an option: ").strip()
                if choice == "1":
                    return Menu._prompt_manual_client()
                elif choice == "2":
                    continue
                elif choice == "0":
                    return None
                else:
                    Logger.warning("Invalid option.")

    @staticmethod
    def _prompt_manual_client() -> Dict[str, str]:
        """Prompts user to enter credentials manually."""
        Logger.header("Manual Credential Input")
        client_name = input("Client / Trade Name (optional): ").strip()
        gstin = input("GSTIN: ").strip().upper()
        username = input("Username: ").strip()
        password = getpass.getpass("Password (hidden): ").strip()

        return {
            "client_name": client_name or gstin,
            "gstin": gstin,
            "username": username,
            "password": password,
            "active": True
        }

    @staticmethod
    def show_main_menu(client_info: Dict[str, str]) -> str:
        """Displays main task menu post-login."""
        name = client_info.get("client_name") or client_info.get("gstin")
        Logger.header(f"Active Session: {name}")
        print("Please choose an operation:")
        print("  [1] Download GSTR-2B Excel (Single or Multiple Periods)")
        print("  [2] Download GSTR-1 PDF (Single or Multiple Periods)")
        print("  [3] Download GSTR-3B PDF (Single or Multiple Periods)")
        print("  [4] Download Cash & Credit Ledgers (Future)")
        print("  [5] Upload Returns JSON (Future)")
        print("  [6] Switch Client / Re-login")
        print("  [0] Exit & Close Browser")

        choice = input("\nEnter your choice: ").strip()
        return choice

    @staticmethod
    def prompt_periods(return_name: str = "Return") -> Optional[List[Dict[str, str]]]:
        """Interactively asks for period configuration for return download."""
        Logger.header(f"Configure {return_name} Download Period")
        print("Select Period Mode:")
        print("  [1] Single Month (e.g., April)")
        print("  [2] Month Range (e.g., April to September)")
        print("  [3] Full Financial Year (All 12 Months)")
        print("  [0] Back to Main Menu")

        mode = input("\nSelect mode (1/2/3/0): ").strip()
        if mode == "0":
            return None

        # Select FY
        print("\nSelect Financial Year:")
        for idx, fy in enumerate(SUPPORTED_FYS, start=1):
            tag = " (Current FY)" if idx == 1 else ""
            print(f"  [{idx:2d}] {fy}{tag}")
        
        fy_choice = input(f"\nSelect FY (1-{len(SUPPORTED_FYS)}) or type directly (e.g. 2026-27 / 2026-2027) [Default 1: {SUPPORTED_FYS[0]}]: ").strip()
        selected_fy = SUPPORTED_FYS[0]
        if fy_choice.isdigit():
            idx = int(fy_choice)
            if 1 <= idx <= len(SUPPORTED_FYS):
                selected_fy = SUPPORTED_FYS[idx - 1]
            elif len(fy_choice) == 4:
                # e.g. user typed 2026
                next_yr = str(int(fy_choice) + 1)[-2:]
                selected_fy = f"{fy_choice}-{next_yr}"
        elif "-" in fy_choice:
            # User typed e.g. "2026-27" or "2026-2027"
            selected_fy = fy_choice

        if mode == "1":
            # Single Month
            print(f"\nSelect Month for FY {selected_fy}:")
            for idx, m in enumerate(MONTH_NAMES, start=1):
                print(f"  [{idx:2d}] {m}")
            
            m_choice = input(f"Select month (1-12): ").strip()
            if m_choice.isdigit() and 1 <= int(m_choice) <= 12:
                chosen_month = MONTH_NAMES[int(m_choice) - 1]
                return [get_single_period(selected_fy, chosen_month)]
            else:
                Logger.warning("Invalid month selected.")
                return None

        elif mode == "2":
            # Month Range
            print(f"\nSelect Start Month for FY {selected_fy}:")
            for idx, m in enumerate(MONTH_NAMES, start=1):
                print(f"  [{idx:2d}] {m}")
            
            start_choice = input("Start Month (1-12): ").strip()
            end_choice = input("End Month (1-12): ").strip()

            if (start_choice.isdigit() and end_choice.isdigit() and
                1 <= int(start_choice) <= 12 and 1 <= int(end_choice) <= 12):
                start_month = MONTH_NAMES[int(start_choice) - 1]
                end_month = MONTH_NAMES[int(end_choice) - 1]
                try:
                    periods = get_period_range(selected_fy, start_month, end_month)
                    Logger.info(f"Selected {len(periods)} periods: {start_month} to {end_month} ({selected_fy})")
                    return periods
                except Exception as e:
                    Logger.error(f"Invalid range: {e}")
                    return None
            else:
                Logger.warning("Invalid month inputs.")
                return None

        elif mode == "3":
            # Full FY
            periods = get_all_periods_for_fy(selected_fy)
            Logger.info(f"Selected full financial year {selected_fy} (12 months).")
            return periods

        else:
            Logger.warning("Invalid choice.")
            return None

    @staticmethod
    def prompt_gstr2b_periods() -> Optional[List[Dict[str, str]]]:
        """Backward compatibility wrapper for GSTR-2B period prompt."""
        return Menu.prompt_periods("GSTR-2B")

