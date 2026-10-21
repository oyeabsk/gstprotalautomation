from pathlib import Path
from typing import Optional
from modules.base import BaseModule
from utils.logger import Logger

class LedgerHandler(BaseModule):
    """Placeholder module for Electronic Cash & Credit Ledgers downloads."""

    def download_cash_ledger(self, from_date: str, to_date: str) -> Optional[Path]:
        Logger.info(f"[Ledgers] Download Cash Ledger requested from {from_date} to {to_date}. (Coming soon)")
        return None

    def download_credit_ledger(self, from_date: str, to_date: str) -> Optional[Path]:
        Logger.info(f"[Ledgers] Download Credit Ledger requested from {from_date} to {to_date}. (Coming soon)")
        return None

    def run(self, *args, **kwargs):
        Logger.warning("Ledgers module is under development and will be available in the next release.")
