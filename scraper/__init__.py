"""
Universal Recruitment Data Scraper Package
"""

from scraper.base import BaseScraper
from scraper.pipeline import UniversalJobPipeline
from scraper.scraper import LinkedInScraper
from scraper.indeed_scraper import IndeedScraper

__all__ = ["BaseScraper", "UniversalJobPipeline", "LinkedInScraper", "IndeedScraper"]
