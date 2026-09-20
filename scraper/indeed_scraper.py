import os
from typing import Set
from urllib.parse import quote

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from scraper.base import BaseScraper
from scraper.config import DATA_RAW_DIR, DEFAULT_USER_AGENT, LOGS_DIR, MAX_DELAY, MAX_PAGES_PER_KEYWORD, MIN_DELAY, UNIFIED_FIELDNAMES
from scraper.indeed_parser import parse_indeed_page
from scraper.utils import append_to_csv, init_csv, load_existing_links, random_delay, setup_logger

INDEED_BASE_URL = "https://www.indeed.com/jobs"


def init_driver(headless: bool = True) -> webdriver.Chrome:
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(f"user-agent={DEFAULT_USER_AGENT}")
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(30)
    return driver


class IndeedScraper(BaseScraper):
    """Scraper implementation for Indeed job search."""

    source_name: str = "indeed"

    def scrape_keyword(
        self,
        driver,
        keyword: str,
        category: str,
        target_count: int,
        output_file_path: str,
        existing_links: Set[str],
        logger,
    ) -> list[dict]:
        """Scrape Indeed postings for a single keyword up to target_count new records."""
        scraped_jobs = []
        page = 0
        max_pages = MAX_PAGES_PER_KEYWORD  # capped at 3 pages per keyword variant

        while len(scraped_jobs) < target_count and page < max_pages:
            start = page * 10

            url = f"{INDEED_BASE_URL}?q={quote(keyword)}&start={start}"
            logger.info(
                f"[Indeed] [{keyword}] Page {page + 1} (Progress: {len(scraped_jobs)}/{target_count}) -> {url}"
            )

            try:
                driver.get(url)
            except Exception as e:
                logger.error(f"[Indeed] [{keyword}] Page {page + 1} navigation error: {e}")
                break

            random_delay(MIN_DELAY, MAX_DELAY)

            html_source = driver.page_source
            safe_keyword = keyword.replace(" ", "_")
            os.makedirs(LOGS_DIR, exist_ok=True)
            debug_path = os.path.join(LOGS_DIR, f"indeed_debug_{safe_keyword}_page_{page+1}.html")
            try:
                with open(debug_path, "w", encoding="utf-8") as f:
                    f.write(html_source)
            except Exception:
                pass

            cards = parse_indeed_page(html_source)
            new_cards = [
                card for card in cards
                if card.get("job_link") and card["job_link"] not in existing_links
            ]

            if not new_cards:
                if cards:
                    logger.info(f"[Indeed] [{keyword}] Page {page + 1}: {len(cards)} parsed, all duplicates.")
                else:
                    logger.warning(f"[Indeed] [{keyword}] Page {page + 1}: No jobs parsed from HTML.")
                page += 1
                continue

            page_new_jobs = []
            for raw_job in new_cards:
                if len(scraped_jobs) + len(page_new_jobs) >= target_count:
                    break

                normalized = self.normalize_job(raw_job, category)
                page_new_jobs.append(normalized)
                existing_links.add(normalized["job_link"])

            if page_new_jobs:
                append_to_csv(output_file_path, UNIFIED_FIELDNAMES, page_new_jobs)
                scraped_jobs.extend(page_new_jobs)
                logger.info(
                    f"[Indeed] [{keyword}] Saved {len(page_new_jobs)} new jobs. (Total keyword: {len(scraped_jobs)}/{target_count})"
                )

            page += 1

        return scraped_jobs


def scrape_indeed(keyword: str = "data analyst", max_pages: int = 1) -> list[dict]:
    """Legacy helper for running Indeed standalone scrape."""
    logger = setup_logger("indeed_scraper_log.txt")
    output_file_path = os.path.join(DATA_RAW_DIR, "indeed_data_analyst_raw.csv")

    init_csv(output_file_path, UNIFIED_FIELDNAMES)
    existing_links = load_existing_links(output_file_path)

    scraper = IndeedScraper()
    driver = None
    all_jobs = []

    try:
        driver = init_driver(headless=True)
        target_count = max_pages * 10
        all_jobs = scraper.scrape_keyword(driver, keyword, "data_analyst", target_count, output_file_path, existing_links, logger)
    finally:
        if driver:
            driver.quit()

    return all_jobs


if __name__ == "__main__":
    scrape_indeed("data analyst", max_pages=1)