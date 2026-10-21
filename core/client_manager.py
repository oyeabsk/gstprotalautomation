from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd
from config.settings import CLIENTS_FILE, CLIENTS_TEMPLATE_FILE, CONFIG_DIR
from utils.logger import Logger

class ClientManager:
    COLUMNS = ["Client Name", "GSTIN", "Username", "Password", "Active"]

    @classmethod
    def create_template_file(cls, path: Optional[Path] = None) -> Path:
        """Creates a sample clients template excel file."""
        target_path = path or CLIENTS_TEMPLATE_FILE
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        
        sample_data = [
            {
                "Client Name": "Sample Client 1",
                "GSTIN": "27AAAAA0000A1Z5",
                "Username": "sample_user_1",
                "Password": "YourPasswordHere",
                "Active": "Yes"
            },
            {
                "Client Name": "Sample Client 2",
                "GSTIN": "24BBBBB0000B1Z8",
                "Username": "sample_user_2",
                "Password": "YourPasswordHere",
                "Active": "No"
            }
        ]
        
        df = pd.DataFrame(sample_data, columns=cls.COLUMNS)
        df.to_excel(target_path, index=False, engine="openpyxl")
        Logger.info(f"Created credentials template file at: {target_path}")
        return target_path

    @classmethod
    def get_credentials_file(cls) -> Path:
        """Returns the clients file path, creating template if missing."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        if not CLIENTS_FILE.exists():
            if not CLIENTS_TEMPLATE_FILE.exists():
                cls.create_template_file(CLIENTS_TEMPLATE_FILE)
            # If clients.xlsx doesn't exist, we also offer the user to copy or use clients.xlsx
            return CLIENTS_FILE
        return CLIENTS_FILE

    @classmethod
    def load_clients(cls) -> List[Dict[str, str]]:
        """
        Reads clients from config/clients.xlsx.
        If file doesn't exist or is empty, prompts user to fill it.
        """
        file_path = cls.get_credentials_file()
        
        if not file_path.exists():
            Logger.warning(f"Master credentials file '{file_path.name}' not found.")
            Logger.info(f"A template has been prepared for you at: {CLIENTS_TEMPLATE_FILE}")
            Logger.info(f"Please fill in your details and save it as: {CLIENTS_FILE}")
            return []

        try:
            df = pd.read_excel(file_path, engine="openpyxl", dtype=str)
            df = df.fillna("")
            
            # Check required columns
            for col in cls.COLUMNS:
                if col not in df.columns:
                    Logger.error(f"Missing required column '{col}' in {file_path.name}")
                    return []

            clients = []
            for _, row in df.iterrows():
                client_dict = {
                    "client_name": str(row["Client Name"]).strip(),
                    "gstin": str(row["GSTIN"]).strip().upper(),
                    "username": str(row["Username"]).strip(),
                    "password": str(row["Password"]).strip(),
                    "active": str(row["Active"]).strip().lower() in ["yes", "y", "true", "1"]
                }
                # Include if at least username and password are provided
                if client_dict["username"] and client_dict["password"]:
                    clients.append(client_dict)

            return clients
        except Exception as e:
            Logger.error(f"Error reading {file_path}: {e}")
            return []

    @classmethod
    def get_active_clients(cls) -> List[Dict[str, str]]:
        """Returns only clients marked as active."""
        all_clients = cls.load_clients()
        return [c for c in all_clients if c.get("active", True)]
