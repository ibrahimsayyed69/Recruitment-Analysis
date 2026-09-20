from abc import ABC, abstractmethod
from datetime import datetime
import hashlib
import logging
from typing import Set

from scraper.config import UNIFIED_FIELDNAMES


class BaseScraper(ABC):
    """Abstract Base Class for recruitment site scrapers."""

    source_name: str = "base"

    @staticmethod
    def generate_job_id(job_link: str, job_title: str, company_name: str) -> str:
        """Generate a unique deterministic hash for a job posting."""
        raw_str = f"{job_link.lower().strip()}|{job_title.lower().strip()}|{company_name.lower().strip()}"
        return hashlib.md5(raw_str.encode("utf-8")).hexdigest()[:12]

    def normalize_job(self, raw_job: dict, category: str) -> dict:
        """Ensure job dict adheres strictly to UNIFIED_FIELDNAMES schema."""
        scraped_at = datetime.now().isoformat()
        
        job_link = raw_job.get("job_link", "N/A")
        job_title = raw_job.get("job_title", "N/A")
        company_name = raw_job.get("company_name", "N/A")

        job_id = raw_job.get("job_id") or self.generate_job_id(job_link, job_title, company_name)

        normalized = {
            "job_id": job_id,
            "source": self.source_name,
            "category": category,
            "job_title": job_title,
            "company_name": company_name,
            "location": raw_job.get("location", "N/A"),
            "job_link": job_link,
            "posted_date_text": raw_job.get("posted_date_text", "N/A"),
            "posted_datetime": raw_job.get("posted_datetime", "N/A"),
            "description": raw_job.get("description", "N/A"),
            "salary": raw_job.get("salary") or raw_job.get("salary_range") or "N/A",
            "seniority": raw_job.get("seniority", "N/A"),
            "job_type": raw_job.get("job_type") or raw_job.get("employment_type") or "N/A",
            "scraped_at": raw_job.get("scraped_at", scraped_at),
        }

        # Validate all fields present
        for field in UNIFIED_FIELDNAMES:
            if field not in normalized:
                normalized[field] = "N/A"

        return normalized

    @abstractmethod
    def scrape_keyword(
        self,
        driver,
        keyword: str,
        category: str,
        target_count: int,
        output_file_path: str,
        existing_links: Set[str],
        logger: logging.Logger,
    ) -> list[dict]:
        """Scrape jobs for a single keyword up to target_count new items."""
        pass
