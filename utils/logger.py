import sys
from datetime import datetime

class Logger:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    BLUE = "\033[94m"

    @classmethod
    def _timestamp(cls) -> str:
        return datetime.now().strftime("%H:%M:%S")

    @classmethod
    def info(cls, message: str):
        print(f"[{cls._timestamp()}] {cls.CYAN}[INFO]{cls.RESET} {message}")

    @classmethod
    def success(cls, message: str):
        print(f"[{cls._timestamp()}] {cls.GREEN}[SUCCESS]{cls.RESET} {message}")

    @classmethod
    def warning(cls, message: str):
        print(f"[{cls._timestamp()}] {cls.YELLOW}[WARNING]{cls.RESET} {message}")

    @classmethod
    def error(cls, message: str):
        print(f"[{cls._timestamp()}] {cls.RED}[ERROR]{cls.RESET} {message}")

    @classmethod
    def prompt(cls, message: str):
        print(f"\n{cls.BOLD}{cls.BLUE}>>> {message}{cls.RESET}")

    @classmethod
    def header(cls, title: str):
        bar = "=" * 60
        print(f"\n{cls.CYAN}{bar}\n  {cls.BOLD}{title.upper()}{cls.RESET}{cls.CYAN}\n{bar}{cls.RESET}\n")
