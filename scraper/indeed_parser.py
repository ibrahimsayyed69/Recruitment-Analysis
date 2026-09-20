import re
from bs4 import BeautifulSoup, Tag


def parse_indeed_card(card: Tag) -> dict | None:
    """Extract job fields from an Indeed search-results card."""
    if not isinstance(card, Tag):
        return None

    # Job Title
    title_el = card.select_one("h2.jobTitle span, a.jcs-JobTitle span, h2 a")
    job_title = title_el.get_text(strip=True) if title_el else "N/A"

    # Company Name
    company_el = card.select_one("span.companyName, [data-testid='company-name']")
    company_name = company_el.get_text(strip=True) if company_el else "N/A"

    # Location
    location_el = card.select_one("div.companyLocation, [data-testid='text-location']")
    location = location_el.get_text(strip=True) if location_el else "N/A"

    # Job Link
    link_el = card.select_one("h2.jobTitle a, a.jcs-JobTitle")
    job_link = "N/A"
    if link_el and link_el.has_attr("href"):
        href = link_el["href"].strip()
        match = re.search(r"jk=([a-f0-9]+)", href)

        if match:
            job_key = match.group(1)
            job_link = f"https://www.indeed.com/viewjob?jk={job_key}"
        else:
            job_link = "https://www.indeed.com" + href if href.startswith("/") else href

    # Salary (Indeed often shows this on-card, unlike LinkedIn)
    salary_el = card.select_one(
        "div.metadata.salary-snippet-container, div.salary-snippet-container, [data-testid='attribute_snippet_testid']"
    )
    salary_range = salary_el.get_text(strip=True) if salary_el else "N/A"

    # Job type (full-time/part-time/contract)
    job_type_el = card.select_one("div.metadata.jobMetaDataGroup, [data-testid='attribute_snippet_testid']")
    job_type = job_type_el.get_text(strip=True) if job_type_el else "N/A"

    # Company rating (Indeed shows review count/rating, LinkedIn doesn't on cards)
    rating_el = card.select_one("span.ratingNumber, [data-testid='holistic-rating']")
    company_rating = rating_el.get_text(strip=True) if rating_el else "N/A"

    # Posted date
    posted_el = card.select_one("span.date, [data-testid='myJobsStateDate']")
    posted_date_text = posted_el.get_text(strip=True) if posted_el else "N/A"

    # Urgently hiring / sponsored badges
    badge_el = card.select_one("span.urgentlyHiring, [data-testid='indeedApplyBadge']")
    badge_text = badge_el.get_text(strip=True) if badge_el else "N/A"

    if job_title == "N/A" and company_name == "N/A" and job_link == "N/A":
        return None

    return {
        "job_title": job_title,
        "company_name": company_name,
        "location": location,
        "job_link": job_link,
        "salary_range": salary_range,
        "job_type": job_type,
        "company_rating": company_rating,
        "posted_date_text": posted_date_text,
        "badge_text": badge_text,
    }


def parse_indeed_page(html_content: str) -> list[dict]:
    """Parse an Indeed search-results page and return a list of job dicts."""
    soup = BeautifulSoup(html_content, "html.parser")

    cards = soup.select("div.job_seen_beacon, div.jobsearch-SerpJobCard, td.resultContent")
    if not cards:
        cards = soup.select("div.cardOutline")

    jobs = []
    seen_links = set()

    for card in cards:
        job_data = parse_indeed_card(card)
        if job_data:
            link = job_data.get("job_link")
            if link and link not in seen_links and link != "N/A":
                seen_links.add(link)
                jobs.append(job_data)

    return jobs