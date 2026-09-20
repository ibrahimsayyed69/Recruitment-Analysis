import os

# Base LinkedIn Public Job Search URL
BASE_URL = "https://www.linkedin.com/jobs/search"
SEE_MORE_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"

# Scraping categories and their search keyword variants
CATEGORIES = {
    "data_analyst": "Data Analyst",
    "software_engineer": "Software Engineer",
    "marketing": "Digital Marketing",
}



# Delays in seconds (random range between actions)
MIN_DELAY = 3
MAX_DELAY = 6

# Pagination & Quota defaults
JOBS_PER_PAGE = 2
DEFAULT_CATEGORY_LIMIT = 200
MAX_PAGES_PER_KEYWORD = 3


# Unified Data Schema Across All Scrapers
UNIFIED_FIELDNAMES = [
    "job_id",
    "source",
    "category",
    "job_title",
    "company_name",
    "location",
    "job_link",
    "posted_date_text",
    "posted_datetime",
    "description",
    "salary",
    "seniority",
    "job_type",
    "scraped_at",
]

# Project directory paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# Chrome User-Agent header
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
