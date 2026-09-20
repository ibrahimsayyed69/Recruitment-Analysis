import csv
import logging
import os
import random
import time
from scraper.config import DEFAULT_USER_AGENT, LOGS_DIR, MAX_DELAY, MIN_DELAY


def random_delay(min_seconds: float = MIN_DELAY, max_seconds: float = MAX_DELAY) -> None:
    """Pause execution for a random float duration between min_seconds and max_seconds."""
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)


def setup_logger(log_file_name: str = "scraper_log.txt") -> logging.Logger:
    """Configure logger to log messages to both file and console."""
    os.makedirs(LOGS_DIR, exist_ok=True)
    log_file_path = os.path.join(LOGS_DIR, log_file_name)

    logger = logging.getLogger("LinkedInScraper")
    logger.setLevel(logging.INFO)

    # Avoid duplicate handlers if already configured
    if not logger.handlers:
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        file_formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter("[%(levelname)s] %(message)s")
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    return logger


def init_csv(file_path: str, fieldnames: list[str]) -> None:
    """Initialize CSV file with header if it doesn't exist."""
    dir_name = os.path.dirname(file_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    if not os.path.exists(file_path):
        with open(file_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()


def append_to_csv(file_path: str, fieldnames: list[str], rows: list[dict]) -> None:
    """Append rows incrementally to CSV file."""
    if not rows:
        return
    init_csv(file_path, fieldnames)
    with open(file_path, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        for row in rows:
            writer.writerow(row)

def load_existing_links(file_path: str) -> set:
    """Read a CSV file and return a set of all job_link values already saved."""
    existing_links = set()

    if not os.path.exists(file_path):
        return existing_links
    
    with open(file_path, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            link = row.get("job_link")
            if link:
                existing_links.add(link)
    return existing_links