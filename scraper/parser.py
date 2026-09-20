from bs4 import BeautifulSoup, Tag


def parse_job_card(card: Tag) -> dict | None:
    """Extract job fields from a BeautifulSoup card Tag (LinkedIn, logged-out search results)."""
    if not isinstance(card, Tag):
        return None

    # Job Title
    title_el = card.select_one(".base-search-card__title, .job-search-card__title, h3")
    job_title = title_el.get_text(strip=True) if title_el else "N/A"

    # Company Name
    company_el = card.select_one(
        ".base-search-card__subtitle, a.hidden-nested-link, .job-search-card__company-name, h4"
    )
    company_name = company_el.get_text(strip=True) if company_el else "N/A"

    # Location
    location_el = card.select_one(".job-search-card__location, .base-search-card__metadata span")
    location = location_el.get_text(strip=True) if location_el else "N/A"

    # Job Link
    link_el = card.select_one("a.base-card__full-link, a.job-search-card__link, a")
    job_link = "N/A"
    if link_el and link_el.has_attr("href"):
        href = link_el["href"].strip()
        job_link = href.split("?")[0] if "?" in href else href

    # Posted Date
    posted_el = card.select_one("time, .job-search-card__listdate, .job-search-card__listdate--new")
    posted_date_text = posted_el.get_text(strip=True) if posted_el else "N/A"
    posted_datetime = posted_el["datetime"] if posted_el and posted_el.has_attr("datetime") else "N/A"

    if job_title == "N/A" and company_name == "N/A" and job_link == "N/A":
        return None

    return {
        "job_title": job_title,
        "company_name": company_name,
        "location": location,
        "job_link": job_link,
        "posted_date_text": posted_date_text,
        "posted_datetime": posted_datetime,
    }


def parse_page_html(html_content: str) -> list[dict]:
    """Parse entire HTML page source and return a list of extracted job dicts."""
    soup = BeautifulSoup(html_content, "html.parser")

    cards = soup.select(".jobs-search__results-list li, .job-search-card, div.base-card")
    if not cards:
        return []

    jobs = []
    seen_links = set()

    for card in cards:
        job_data = parse_job_card(card)
        if job_data:
            link = job_data.get("job_link")
            if link and link not in seen_links and link != "N/A":
                seen_links.add(link)
                jobs.append(job_data)

    return jobs

def parse_job_detail_html(html_content: str) -> dict:
    """"Parse a single job's detail page for extra fields."""
    soup = BeautifulSoup(html_content, "html.parser")

    desc_el = soup.select_one(".description__text, .show-more-less-html__markup")
    description = desc_el.get_text(" ", strip=True) if desc_el else "N/A"

    salary_el = soup.select_one(".compensation__salary, .salary")
    salary = salary_el.get_text(strip=True) if salary_el else "N/A"

    criteria_itmes = soup.select(".description__job-criteria-item")
    seniority = "N/A"
    employment_type = "N/A"
    for item in criteria_itmes:
        label = item.select_one(".description__job-criteria-subheader")
        value = item.select_one(".description__job-criteria-text")
        if not label or not value:
            continue
        label_text = label.get_text(strip=True).lower()
        value_text = value.get_text(strip=True)
        if "seniority" in label_text:
            seniority = value_text
        elif "employment type" in label_text:
            employment_type = value_text

    return {
        "description": description,
        "salary": salary,
        "seniority": seniority,
        "employment_type": employment_type,
    }