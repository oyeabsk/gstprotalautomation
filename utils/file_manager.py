import os
import shutil
from pathlib import Path
from config.settings import DOWNLOADS_DIR
from utils.logger import Logger

class FileManager:
    @staticmethod
    def get_download_path(gstin: str, fy: str, return_type: str, month: str = "") -> Path:
        """
        Builds a structured folder path:
        downloads/{GSTIN}/{FY}/{return_type}/
        """
        clean_gstin = gstin.strip().upper()
        clean_fy = fy.strip()
        clean_type = return_type.strip().upper()

        target_dir = DOWNLOADS_DIR / clean_gstin / clean_fy / clean_type
        target_dir.mkdir(parents=True, exist_ok=True)
        return target_dir

    @staticmethod
    def save_playwright_download(download, target_dir: Path, target_filename: str) -> Path:
        """
        Saves a Playwright Download object to the target directory using download.save_as().
        This is the correct, race-free way to persist a Playwright download.
        NEVER use download.path() + shutil.move() — Playwright deletes the temp file
        as soon as the expect_download context exits on Windows.
        """
        target_file = target_dir / target_filename
        if target_file.exists():
            target_file.unlink()

        # save_as() is atomic and handles the internal temp path correctly
        download.save_as(str(target_file))
        Logger.success(f"Saved file to: {target_file}")
        return target_file

    @staticmethod
    def save_downloaded_file(source_temp_path: str, target_dir: Path, target_filename: str) -> Path:
        """
        Legacy: moves a raw temp file path. Prefer save_playwright_download() for Playwright downloads.
        """
        target_file = target_dir / target_filename
        if target_file.exists():
            target_file.unlink()

        shutil.copy2(source_temp_path, str(target_file))
        Logger.success(f"Saved file to: {target_file}")
        return target_file
