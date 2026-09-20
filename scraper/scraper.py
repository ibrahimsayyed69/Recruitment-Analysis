import os
import sys
from typing import Set
from urllib.parse import quote

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from scraper.base import BaseScraper
from scraper.config import (
    BASE_URL,
    CATEGORIES,
    DATA_RAW_DIR,
    DEFAULT_USER_AGENT,
    JOBS_PER_PAGE,
    LOGS_DIR,
    MAX_DELAY,
    MAX_PAGES_PER_KEYWORD,
    MIN_DELAY,
    SEE_MORE_URL,
    UNIFIED_FIELDNAMES,
)
from scraper.parser import parse_job_detail_html, parse_page_html
from scraper.utils import append_to_csv, init_csv, load_existing_links, random_delay, setup_logger



def enrich_job_with_details(driver, job: dict, logger) -> dict:
    """Visit a job's detail page via HTTP request (fast) or Selenium fallback and merge extra fields."""
    url = job.get("job_link")
    if not url or url == "N/A":
        return job

    html_content = None

    # Try fast HTTP request first
    try:
        response = requests.get(url, headers={"User-Agent": DEFAULT_USER_AGENT}, timeout=8)
        if response.status_code == 200 and len(response.text) > 500:
            html_content = response.text
    except Exception as e:
        logger.debug(f"[LinkedIn] Fast HTTP fetch failed for {url}: {e}")

    # Fallback to driver navigation if HTTP request did not yield detail HTML
    if not html_content and driver:
        try:
            driver.get(url)
            random_delay(MIN_DELAY, MAX_DELAY)
            html_content = driver.page_source
        except Exception as e:
            logger.warning(f"[LinkedIn] Failed to fetch detail page via driver for {url}: {e}")

    if html_content:
        try:
            details = parse_job_detail_html(html_content)
            job.update(details)
        except Exception as e:
            logger.warning(f"[LinkedIn] Error parsing detail HTML for {url}: {e}")
    else:
        job.update({"description": "N/A", "salary": "N/A", "seniority": "N/A", "employment_type": "N/A"})

    return job


def init_driver(headless: bool = True) -> webdriver.Chrome:
    """Initialize and configure Chrome WebDriver."""
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


def check_blocked_or_captcha(driver: webdriver.Chrome) -> bool:
    """Check if page is a CAPTCHA, block page, or login challenge."""
    current_url = driver.current_url.lower()
    page_title = driver.title.lower()

    if "authwall" in current_url or "checkpoint/challenge" in current_url:
        return True

    if any(
        term in page_title
        for term in ["security verification", "captcha", "access denied", "sign in"]
    ):
        return True

    try:
        source = driver.page_source.lower()
        if (
            "please enter the characters you see below" in source
            or "verify you are a human" in source
            or "g-recaptcha" in source
            or "captcha-internal" in source
        ):
            return True
    except Exception:
        pass

    return False


class LinkedInScraper(BaseScraper):
    """Scraper implementation for LinkedIn Public Job Search."""

    source_name: str = "linkedin"

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
        """Scrape LinkedIn postings for a single keyword up to target_count new records."""
        scraped_jobs = []
        page = 0
        max_pages = MAX_PAGES_PER_KEYWORD  # capped at 3 pages per keyword variant


        while len(scraped_jobs) < target_count and page < max_pages:
            start_offset = page * JOBS_PER_PAGE
            if page == 0:
                search_url = f"{BASE_URL}?keywords={quote(keyword)}"
            else:
                search_url = f"{SEE_MORE_URL}?keywords={quote(keyword)}&start={start_offset}"

            logger.info(
                f"[LinkedIn] [{keyword}] Page {page + 1} (Progress: {len(scraped_jobs)}/{target_count}) -> {search_url}"
            )

            try:
                driver.get(search_url)
            except Exception as e:
                logger.error(f"[LinkedIn] [{keyword}] Page {page + 1} navigation error: {e}")
                break

            random_delay(MIN_DELAY, MAX_DELAY)

            if check_blocked_or_captcha(driver):
                logger.warning(
                    f"[LinkedIn] [{keyword}] CAPTCHA or Authwall detected! Stopping LinkedIn scrape gracefully."
                )
                break

            try:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                random_delay(1, 2)
            except Exception:
                pass

            html_source = driver.page_source
            safe_keyword = keyword.replace(" ", "_")
            os.makedirs(LOGS_DIR, exist_ok=True)
            debug_path = os.path.join(LOGS_DIR, f"debug_linkedin_{safe_keyword}_page_{page+1}.html")
            try:
                with open(debug_path, "w", encoding="utf-8") as f:
                    f.write(html_source)
            except Exception:
                pass

            cards = parse_page_html(html_source)
            new_cards = [
                card for card in cards
                if card.get("job_link") and card["job_link"] not in existing_links
            ]

            if not new_cards:
                if cards:
                    logger.info(f"[LinkedIn] [{keyword}] Page {page + 1}: {len(cards)} jobs parsed, all duplicates.")
                else:
                    logger.warning(f"[LinkedIn] [{keyword}] Page {page + 1}: No job cards found in DOM.")
                page += 1
                continue

            page_new_jobs = []
            for raw_job in new_cards:
                if len(scraped_jobs) + len(page_new_jobs) >= target_count:
                    break

                enriched = enrich_job_with_details(driver, raw_job, logger)
                normalized = self.normalize_job(enriched, category)
                page_new_jobs.append(normalized)
                existing_links.add(normalized["job_link"])

            if page_new_jobs:
                append_to_csv(output_file_path, UNIFIED_FIELDNAMES, page_new_jobs)
                scraped_jobs.extend(page_new_jobs)
                logger.info(
                    f"[LinkedIn] [{keyword}] Saved {len(page_new_jobs)} new jobs. (Total keyword: {len(scraped_jobs)}/{target_count})"
                )

            page += 1

        return scraped_jobs


def scrape_category(category_key: str = "data_analyst", max_pages: int = 2) -> list[dict]:
    """Legacy helper for running LinkedIn standalone scrape."""
    logger = setup_logger("scraper_log.txt")
    keywords = CATEGORIES.get(category_key, [category_key])

    output_filename = f"{category_key}_raw.csv"
    output_file_path = os.path.join(DATA_RAW_DIR, output_filename)
    init_csv(output_file_path, UNIFIED_FIELDNAMES)
    existing_links = load_existing_links(output_file_path)

    scraper = LinkedInScraper()
    driver = None
    all_jobs = []

    try:
        driver = init_driver(headless=True)
        target_per_keyword = max_pages * JOBS_PER_PAGE
        for kw in keywords:
            jobs = scraper.scrape_keyword(driver, kw, category_key, target_per_keyword, output_file_path, existing_links, logger)
            all_jobs.extend(jobs)
    finally:
        if driver:
            driver.quit()

    return all_jobs


if __name__ == "__main__":
    pages_to_scrape = 2
    category = "data_analyst"

    if len(sys.argv) > 1:
        try:
            pages_to_scrape = int(sys.argv[1])
        except ValueError:
            category = sys.argv[1]

    if len(sys.argv) > 2:
        category = sys.argv[2]

    scrape_category(category, max_pages=pages_to_scrape)