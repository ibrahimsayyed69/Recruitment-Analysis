# Recruitment-Analysis
An automated recruitment data pipeline and market intelligence generator that cleans job postings, analyzes in-demand technical skills, and publishes a comprehensive markdown analytics report

---

## 📊 Dataset Scope & Overview
This project aggregates and analyzes recent job market vacancies to uncover insights on technical skill demands, work modalities, and top hiring companies.
* **Total Jobs Analyzed:** 127 unique deduplicated records.
* **Portals Tracked:** LinkedIn, Indeed, and NaukriGulf.
* **Job Categories:** Data Analysis, Software Engineering, and Digital Marketing / Marketing Executive.

### Work Modality Breakdown
* **On-site:** 70.1% (89 postings)
* **Remote:** 19.7% (25 postings)
* **Hybrid:** 10.2% (13 postings)

---

## 🛠️ Key Skills & Technology Stack Insights

### Overall Top Skills
* **SQL:** 14.2% (18 mentions)
* **SEO:** 14.2% (18 mentions)
* **Python:** 11.0% (14 mentions)
* **AI / GenAI:** 11.0% (14 mentions)
* **CRM & Social Media:** 10.2% each (~13 mentions)

### Category-Specific Breakdown
* **Data Analyst:** Heavily driven by **SQL** (34.1%), **Statistics** (29.3%), **Power BI** / **Tableau** (26.8%), and **Python / Excel** (22.0%).
* **Software Engineer:** Focused on **AWS** (19.5%), **Java** (17.1%), **CI/CD** (14.6%), **AI / GenAI** (14.6%), and **Kubernetes / React / Python** (12.2%).
* **Digital Marketing:** Dominated by **SEO** (40.0%), **Social Media** (28.9%), **CRM** (26.7%), **Google Analytics** (24.4%), and **Google Ads** (22.2%).

---

## 🏢 Top Hiring Employers
Key organizations driving recruitment volume in the dataset include:
* **Dicetek LLC** & **Confidential Company** (6 open postings each)
* **Xcel Energy**, **Corporate Tools**, **General Motors**, **JPMorganChase**, **AWS**, **Affirm**, and **Tarpon Health** (2 open postings each)

---

## 🚀 Key Dashboard Features
* **Automated Data Pipeline:** Cleans and normalizes multi-source job postings into unified metrics.
* **Interactive Filtering:** Filter recruitment trends by domain, work modality, portal origin, and required tech stacks.
* **Market Intelligence Visualization:** Dynamic charts highlighting critical hiring gaps and in-demand tech stacks.

---

## 💻 Tech Stack Used
* **Frontend / UI:** [Streamlit]([Recruitment_Analysis](https://attendance-system-using-face-recognition-gptdprzy3ykwyv93tmi7b.streamlit.app/))
* **Data Processing:** Python, Pandas
* **Deployment:** Streamlit Community Cloud & GitHub

---

# Project Structure

```
├── __pycache__
├── .venv
|── analysis
│   ├── __pycache__
│   ├── __init__.py
│   ├── analyze.py
│   ├── clean_data.py
│   ├── generate_report.py
│   └── visualize.py
├── data
│   ├── processed
│   │   └── all_jobs_clean.csv
│   └── raw
│       ├── data_analyst_raw.csv
│       ├── marketing_raw.csv
│       └── software_engineer_raw.csv
├── logs
├── reports
│   ├── figures
│   └── final_report.md
├── scraper
│   ├── __pycache__
│   ├── __init__.py
│   ├── base.py
│   ├── config.py
│   ├── dashboard.py
│   ├── parser.py
│   ├── pipeline.py
│   ├── scraper.py
│   └── utils.py
├── main.py
├── README.md
└── requirements.txt
