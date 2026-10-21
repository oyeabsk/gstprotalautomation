import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
CLIENTS_FILE = CONFIG_DIR / "clients.xlsx"
CLIENTS_TEMPLATE_FILE = CONFIG_DIR / "clients_template.xlsx"
DOWNLOADS_DIR = BASE_DIR / "downloads"

# Portal URLs
GST_LOGIN_URL = "https://services.gst.gov.in/services/login"
GST_DASHBOARD_URL = "https://services.gst.gov.in/services/auth/dashboard"
GST_RETURNS_DASHBOARD_URL = "https://return.gst.gov.in/returns/auth/dashboard"
GST_LEDGERS_URL = "https://services.gst.gov.in/services/auth/ledgers"

# Browser Settings
HEADLESS = False  # Headed mode required for Captcha solving
BROWSER_TIMEOUT = 45000  # 45 seconds for page actions
CAPTCHA_TIMEOUT = 120000  # 2 minutes for user to enter captcha / OTP
SLOW_MO = 50  # millisecond delay between actions for human-like pacing

# Financial Years & Return Periods
SUPPORTED_FYS = [
    "2026-27",
    "2025-26",
    "2024-25",
    "2023-24",
    "2022-23",
    "2021-22",
    "2020-21",
    "2019-20",
    "2018-19",
    "2017-18",
]

MONTH_NAMES = [
    "April", "May", "June",
    "July", "August", "September",
    "October", "November", "December",
    "January", "February", "March"
]

QUARTERS = {
    "Q1": ["April", "May", "June"],
    "Q2": ["July", "August", "September"],
    "Q3": ["October", "November", "December"],
    "Q4": ["January", "February", "March"]
}
