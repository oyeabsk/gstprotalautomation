# GST Portal Automation Hub

A modular, extensible Python automation platform for the Indian Goods and Services Tax (GST) Portal (`services.gst.gov.in`), powered by **Playwright**.

---

## Key Features

- **Master Excel Credential Management**: Safely manage all your clients and GSTINs in `config/clients.xlsx` without hardcoding passwords in scripts.
- **Semi-Automated Login**: Automatically opens the GST portal, fills credentials, focuses the Captcha field, and awaits your Captcha/OTP input before confirming successful dashboard landing.
- **Interactive Menu Hub**: Post-login terminal menu allowing you to select tasks on demand.
- **Multi-Period Return Downloaders**:
  - **GSTR-2B**: Detailed Excel download with direct & table generation handling and auto-return.
  - **GSTR-1**: PDF Summary download with in-page two-step `BACK` navigation.
  - **GSTR-3B**: Filed Return PDF download with instant in-place multi-month transitions.
  - Flexible period selection: Single Month, Month Range, or Full Financial Year (all 12 months).
  - Automatically saves and organizes files into `downloads/{GSTIN}/{FY}/{ReturnType}/` with ascending chronological month sorting (`01_April` to `12_March`).
- **Wider Modular Base**: Pre-structured for upcoming return modules, ledgers (`Cash & Credit Ledgers`), and JSON return uploads.

---

## Directory Structure

```
GST Portal Automation/
│
├── config/
│   ├── settings.py             # URLs, timeouts, FY mappings
│   ├── clients.xlsx            # Your confidential client master (git-ignored)
│   └── clients_template.xlsx   # Sample template for adding clients
│
├── core/
│   ├── browser.py              # Playwright browser manager (headed Chromium)
│   ├── auth.py                 # Login, captcha detection, session tracking
│   └── client_manager.py       # Excel client reader & validator
│
├── modules/
│   ├── base.py                 # BaseModule: returns dashboard navigation & period selection
│   ├── returns/
│   │   ├── gstr2b.py           # GSTR-2B single & batch Excel downloader
│   │   ├── gstr1.py            # [Future] GSTR-1 Excel/JSON download & upload
│   │   └── gstr3b.py           # [Future] GSTR-3B PDF & JSON handler
│   └── ledgers/
│       └── cash_credit.py      # [Future] Electronic Cash & Credit Ledgers
│
├── utils/
│   ├── file_manager.py         # Downloads path manager: downloads/<GSTIN>/<FY>/...
│   ├── period_helper.py        # Indian FY, Quarter, and Month logic
│   └── logger.py               # Colorized terminal logging
│
├── cli/
│   └── menu.py                 # Terminal menus for clients, tasks, and periods
│
├── downloads/                  # Output directory for downloaded statements
├── main.py                     # Application entry point
├── requirements.txt            # Python dependencies
└── .gitignore                  # Keeps credentials and downloads private
```

---

## Getting Started

### 1. Requirements & Setup

Ensure you have Python 3.10+ installed. The following dependencies are used:
```bash
python -m pip install -r requirements.txt
python -m playwright install chromium
```

### 2. Configure Client Credentials

On first run, the system creates `config/clients_template.xlsx`.

To configure your clients:
1. Make a copy of `config/clients_template.xlsx` named `config/clients.xlsx`.
2. Open `config/clients.xlsx` in Excel.
3. Fill in the columns:
   - **Client Name**: e.g., `ABC Enterprises`
   - **GSTIN**: e.g., `27AAAAA0000A1Z5`
   - **Username**: Portal login username
   - **Password**: Portal login password
   - **Active**: `Yes` (or `No` to temporarily disable)
4. Save the file. (Note: `clients.xlsx` is git-ignored for your security).

You can also choose to type credentials manually directly into the terminal if you prefer not to use an Excel file.

### 3. Run the Automation Hub

Launch the application:
```bash
python main.py
```

### 4. Workflow Walkthrough

1. **Select Client**: Pick your client from the numbered list loaded from `clients.xlsx`.
2. **Browser Opens**: A Chromium browser window opens and enters your Username and Password automatically.
3. **Solve Captcha**: Look at the browser window, type the 6 characters in the Captcha box, and click **Login** (complete OTP if prompted).
4. **Task Menu Appears**:
   - Choose `[1] Download GSTR-2B Excel`
   - Select period mode: Single Month, Range of Months, or Full FY
   - Choose Financial Year (e.g. `2024-25`)
   - The script automates navigation to the Returns Dashboard, selects the periods, triggers the download, and saves each file to:
     `downloads/{GSTIN}/{FY}/GSTR-2B/GSTR2B_{GSTIN}_{Month}_{FY}.xlsx`
