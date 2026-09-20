import os

from scraper.config import CATEGORIES, DATA_RAW_DIR, DEFAULT_CATEGORY_LIMIT, UNIFIED_FIELDNAMES
from scraper.indeed_scraper import IndeedScraper, init_driver as init_indeed_driver
from scraper.naukrigulf_scraper import NaukriGulfScraper, init_driver as init_naukrigulf_driver
from scraper.scraper import LinkedInScraper, init_driver as init_linkedin_driver
from scraper.utils import init_csv, load_existing_links, setup_logger


class UniversalJobPipeline:
    """Universal Recruitment Data Pipeline for multi-source job scraping with quota control."""

    SCRAPER_REGISTRY = {
        "linkedin": (LinkedInScraper, init_linkedin_driver),
        "indeed": (IndeedScraper, init_indeed_driver),
        "naukrigulf": (NaukriGulfScraper, init_naukrigulf_driver),
    }


    def __init__(self, output_dir: str = DATA_RAW_DIR):
        self.output_dir = output_dir
        self.logger = setup_logger("pipeline.log")

    def run(
        self,
        category: str = "data_analyst",
        target_limit: int = DEFAULT_CATEGORY_LIMIT,
        sources: list[str] = None,
    ) -> list[dict]:
        """Run multi-source scraping for a category until total new jobs target_limit is reached."""
        if sources is None:
            sources = ["linkedin", "indeed"]

        keywords = CATEGORIES.get(category, [category.replace("_", " ")])
        if isinstance(keywords, str):
            keywords = [keywords]

        output_filename = f"{category}_raw.csv"
        output_file_path = os.path.join(self.output_dir, output_filename)

        self.logger.info("=" * 60)
        self.logger.info(f"STARTING UNIVERSAL PIPELINE")
        self.logger.info(f"Category: '{category}' | Target Limit: {target_limit} jobs")
        self.logger.info(f"Active Sources: {sources} | Keywords: {keywords}")
        self.logger.info(f"Output File: {output_file_path}")
        self.logger.info("=" * 60)

        init_csv(output_file_path, UNIFIED_FIELDNAMES)
        existing_links = load_existing_links(output_file_path)
        self.logger.info(f"Loaded {len(existing_links)} existing job links for deduplication.")

        valid_sources = [s.lower() for s in sources if s.lower() in self.SCRAPER_REGISTRY]
        if not valid_sources:
            self.logger.error(f"No valid scrapers specified in {sources}. Available: {list(self.SCRAPER_REGISTRY.keys())}")
            return []

        total_collected = 0
        all_new_jobs = []

        # Equal quota distribution with failover spillover
        quota_per_source = target_limit // len(valid_sources)
        remaining_target = target_limit

        for idx, source_name in enumerate(valid_sources):
            if remaining_target <= 0:
                self.logger.info(f"Target quota of {target_limit} jobs already reached!")
                break

            # If last source, give it all remaining quota
            is_last = (idx == len(valid_sources) - 1)
            source_target = remaining_target if is_last else min(quota_per_source, remaining_target)

            self.logger.info(f"\n--- Launching [{source_name.upper()}] (Target: {source_target} jobs) ---")

            scraper_cls, driver_init_fn = self.SCRAPER_REGISTRY[source_name]
            scraper_instance = scraper_cls()
            driver = None

            source_jobs_scraped = 0
            try:
                driver = driver_init_fn(headless=True)

                for keyword in keywords:
                    if source_jobs_scraped >= source_target:
                        break

                    kw_target = source_target - source_jobs_scraped
                    jobs = scraper_instance.scrape_keyword(
                        driver=driver,
                        keyword=keyword,
                        category=category,
                        target_count=kw_target,
                        output_file_path=output_file_path,
                        existing_links=existing_links,
                        logger=self.logger,
                    )

                    source_jobs_scraped += len(jobs)
                    all_new_jobs.extend(jobs)

            except Exception as e:
                self.logger.error(f"Error executing [{source_name}] scraper: {e}", exc_info=True)
            finally:
                if driver:
                    try:
                        driver.quit()
                        self.logger.info(f"[{source_name}] Driver closed.")
                    except Exception:
                        pass

            self.logger.info(f"[{source_name.upper()}] Finished. Collected {source_jobs_scraped} jobs.")
            total_collected += source_jobs_scraped
            remaining_target -= source_jobs_scraped

        self.logger.info("=" * 60)
        self.logger.info(
            f"PIPELINE COMPLETE for '{category}'. Total New Jobs Saved: {total_collected}/{target_limit}"
        )
        self.logger.info("=" * 60)

        return all_new_jobs
