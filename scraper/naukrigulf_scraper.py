"""
NaukriGulf Job Scraper Implementation.
Inherits from BaseScraper and integrates with UniversalJobPipeline.
"""

import os
from typing import Set
from urllib.parse import quote
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

from scraper.base import BaseScraper
from scraper.config import DEFAULT_USER_AGENT, LOGS_DIR, MAX_DELAY, MAX_PAGES_PER_KEYWORD, MIN_DELAY, UNIFIED_FIELDNAMES
from scraper.utils import append_to_csv, random_delay

NAUKRIGULF_BASE_URL = "https://www.naukrigulf.com"


def init_driver(headless: bool = True) -> webdriver.Chrome:
    """Initialize Chrome driver for NaukriGulf scraping."""
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


def parse_naukrigulf_page(html_source: str) -> list[dict]:
    """Parse job tuples from NaukriGulf search page HTML."""
    soup = BeautifulSoup(html_source, "html.parser")
    jobs = []
    
    tuples = (
        soup.find_all(class_=lambda c: c and "srp-tuple" in str(c))
        or soup.find_all("article")
    )
    
    for t in tuples:
        try:
            title_a = t.find("a", href=lambda h: h and "-jid-" in str(h)) or t.find("a", href=lambda h: h and "-jobs-" in str(h))
            if not title_a:
                continue
                
            job_title = title_a.get_text(strip=True)
            job_link = title_a.get("href", "N/A")
            if not job_title or len(job_title) < 3:
                continue
                
            if job_link != "N/A" and not job_link.startswith("http"):
                job_link = NAUKRIGULF_BASE_URL + (job_link if job_link.startswith("/") else "/" + job_link)
                
            comp_elem = t.find(class_=lambda c: c and any(k in str(c).lower() for k in ["org", "company", "employer"]))
            company_name = comp_elem.get_text(strip=True) if comp_elem else "NaukriGulf Employer"
            
            loc_elem = t.find(class_=lambda c: c and any(k in str(c).lower() for k in ["loc", "city", "location"]))
            location = loc_elem.get_text(strip=True) if loc_elem else "Gulf Region / Remote"
            
            desc_elem = t.find(class_=lambda c: c and any(k in str(c).lower() for k in ["desc", "summary", "detail"]))
            description = desc_elem.get_text(strip=True) if desc_elem else f"{job_title} position at {company_name}"
            
            jobs.append({
                "job_title": job_title,
                "company_name": company_name,
                "location": location,
                "job_link": job_link,
                "description": description,
            })
        except Exception:
            continue
            
    return jobs


class NaukriGulfScraper(BaseScraper):
    """Scraper implementation for NaukriGulf job portal."""

    source_name: str = "naukrigulf"

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
        """Scrape NaukriGulf postings for a single keyword up to target_count new records."""
        scraped_jobs = []
        page = 1
        max_pages = MAX_PAGES_PER_KEYWORD

        safe_keyword = keyword.lower().replace(" ", "-")

        while len(scraped_jobs) < target_count and page <= max_pages:
            url = f"{NAUKRIGULF_BASE_URL}/{safe_keyword}-jobs" if page == 1 else f"{NAUKRIGULF_BASE_URL}/{safe_keyword}-jobs-{page}"
            logger.info(f"[NaukriGulf] [{keyword}] Page {page} (Progress: {len(scraped_jobs)}/{target_count}) -> {url}")

            try:
                driver.get(url)
            except Exception as e:
                logger.error(f"[NaukriGulf] [{keyword}] Page {page} navigation error: {e}")
                break

            random_delay(MIN_DELAY, MAX_DELAY)

            html_source = driver.page_source
            os.makedirs(LOGS_DIR, exist_ok=True)
            debug_path = os.path.join(LOGS_DIR, f"naukrigulf_debug_{safe_keyword}_page_{page}.html")
            try:
                with open(debug_path, "w", encoding="utf-8") as f:
                    f.write(html_source)
            except Exception:
                pass

            cards = parse_naukrigulf_page(html_source)
            new_cards = [card for card in cards if card.get("job_link") and card["job_link"] not in existing_links]

            if not new_cards:
                logger.info(f"[NaukriGulf] [{keyword}] Page {page}: No new un-saved jobs parsed ({len(cards)} total parsed).")
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
                logger.info(f"[NaukriGulf] [{keyword}] Saved {len(page_new_jobs)} new jobs.")

            page += 1

        return scraped_jobs
