#!/usr/bin/env python
"""
Universal Recruitment Data Pipeline CLI Entry Point.
Usage:
    python main.py --category data_analyst --limit 200 --sources linkedin indeed
"""

import argparse
import sys
from scraper.config import CATEGORIES, DEFAULT_CATEGORY_LIMIT
from scraper.pipeline import UniversalJobPipeline


def main():
    parser = argparse.ArgumentParser(
        description="Universal Recruitment Data Scraper Pipeline - Scrape job postings with category quota enforcement."
    )
    parser.add_argument(
        "--category",
        "-c",
        type=str,
        default="data_analyst",
        choices=list(CATEGORIES.keys()) + ["all"],
        help="Job category to scrape (default: data_analyst). Use 'all' to scrape all defined categories.",
    )
    parser.add_argument(
        "--limit",
        "-l",
        type=int,
        default=DEFAULT_CATEGORY_LIMIT,
        help=f"Target quota limit for total new jobs saved (default: {DEFAULT_CATEGORY_LIMIT}).",
    )
    parser.add_argument(
        "--sources",
        "-s",
        nargs="+",
        default=["linkedin", "indeed"],
        help="Space-separated list of scrapers to activate (choices: linkedin, indeed, naukrigulf).",
    )
    parser.add_argument(
        "--reset",
        "-r",
        action="store_true",
        help="Wipe previous raw and processed CSV data files before starting fresh scrape.",
    )

    args = parser.parse_args()

    if args.reset:
        import os
        import glob
        print("[INFO] Wiping previous data files for fresh collection...")
        raw_files = glob.glob("data/raw/*.csv")
        proc_files = glob.glob("data/processed/*.csv")
        for f in raw_files + proc_files:
            try:
                os.remove(f)
                print(f"  - Removed {f}")
            except Exception as e:
                print(f"  - Error removing {f}: {e}")

    pipeline = UniversalJobPipeline()

    if args.category == "all":
        categories_to_run = list(CATEGORIES.keys())
    else:
        categories_to_run = [args.category]

    print(f"\n[INFO] Launching Universal Job Pipeline")
    print(f"Categories: {categories_to_run}")
    print(f"Quota Limit: {args.limit} jobs per category")
    print(f"Sources: {args.sources}\n")

    for cat in categories_to_run:
        pipeline.run(category=cat, target_limit=args.limit, sources=args.sources)

    print("\n[SUCCESS] All category scraping tasks completed successfully.")


if __name__ == "__main__":
    main()
