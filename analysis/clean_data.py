"""
Data Cleaning & Preprocessing Module for Recruitment Data.
Reads raw CSV files from data/raw/, deduplicates, extracts skills, salary ranges,
work modality, and exports a unified clean dataset to data/processed/all_jobs_clean.csv.
"""

import os
import re
import glob
import pandas as pd
import numpy as np

# Skills dictionary by domain
SKILLS_TAXONOMY = {
    # Data & Analytics Skills
    "Python": r"\bpython\b",
    "SQL": r"\bsql\b",
    "R": r"\br\b",
    "Excel": r"\bexcel\b",
    "Power BI": r"\bpower\s*bi\b",
    "Tableau": r"\btableau\b",
    "Pandas": r"\bpandas\b",
    "NumPy": r"\bnumpy\b",
    "Spark": r"\bspark\b|pyspark",
    "Hadoop": r"\bhadoop\b",
    "Snowflake": r"\bsnowflake\b",
    "BigQuery": r"\bbigquery\b",
    "ETL": r"\betl\b",
    "Data Warehousing": r"\bdata\s*warehous(ing|e)\b",
    "Machine Learning": r"\bmachine\s*learning\b|\bml\b",
    "AI / GenAI": r"\bartificial\s*intelligence\b|\bai\b|\bgenai\b|\bgenerative\s*ai\b",
    "Statistics": r"\bstatistic(s|al)\b",
    "Looker": r"\blooker\b",
    "SAS": r"\bsas\b",
    "SPSS": r"\bspss\b",
    "PostgreSQL": r"\bpostgres(ql)?\b",
    "MySQL": r"\bmysql\b",

    # Software Engineering Skills
    "Java": r"\bjava\b",
    "C++": r"\bc\+\+\b",
    "C#": r"\bc#\b|\b\.net\b",
    "JavaScript": r"\bjavascript\b|\bjs\b",
    "TypeScript": r"\btypescript\b|\bts\b",
    "React": r"\breact(js)?\b",
    "Node.js": r"\bnode(\.js)?\b",
    "Angular": r"\bangular\b",
    "Vue": r"\bvue(\.js)?\b",
    "Docker": r"\bdocker\b",
    "Kubernetes": r"\bkubernetes\b|\bk8s\b",
    "AWS": r"\baws\b|amazon\s*web\s*services",
    "Azure": r"\bazure\b",
    "GCP": r"\bgcp\b|google\s*cloud",
    "Git": r"\bgit\b",
    "REST API": r"\brest(ful)?\s*api\b|\brest\b",
    "GraphQL": r"\bgraphql\b",
    "Microservices": r"\bmicroservices\b",
    "CI/CD": r"\bci/cd\b|\bcontinuous\s*integration\b",
    "Linux": r"\blinux\b",
    "Spring Boot": r"\bspring\s*boot\b",
    "Django": r"\bdjango\b",
    "Flask": r"\bflask\b",

    # Marketing Skills
    "SEO": r"\bseo\b|search\s*engine\s*optimization",
    "SEM": r"\bsem\b|search\s*engine\s*marketing",
    "Google Analytics": r"\bgoogle\s*analytics\b|\bga4\b",
    "Content Strategy": r"\bcontent\s*strategy\b|\bcontent\s*marketing\b",
    "Social Media": r"\bsocial\s*media\b",
    "Copywriting": r"\bcopywriting\b",
    "HubSpot": r"\bhubspot\b",
    "Marketo": r"\bmarketo\b",
    "Email Marketing": r"\bemail\s*marketing\b",
    "CRM": r"\bcrm\b|salesforce",
    "Google Ads": r"\bgoogle\s*ads\b|\badwords\b",
    "Facebook Ads": r"\bfacebook\s*ads\b|\bmeta\s*ads\b",
    "Brand Strategy": r"\bbrand\s*(strategy|management)\b",
    "Campaign Management": r"\bcampaign\s*management\b",
}


def extract_skills(text: str) -> list:
    """Extract list of skill tags present in text using regex matching."""
    if not isinstance(text, str) or not text.strip():
        return []
    
    found_skills = []
    text_lower = text.lower()
    for skill, pattern in SKILLS_TAXONOMY.items():
        if re.search(pattern, text_lower, re.IGNORECASE):
            found_skills.append(skill)
    return found_skills


def extract_salary(salary_text: str, description_text: str) -> dict:
    """Extract min, max, avg annual salary and pay type from text."""
    combined_text = f"{salary_text or ''} {description_text or ''}"
    
    # Pattern for ranges like $80,000 - $120,000 or $80k - $120k or $45 - $60 / hr
    patterns = [
        # $100,000 - $150,000 / year or a year or annually
        r"\$(\d{2,3}(?:,\d{3})+)\s*(?:-|to)\s*\$(\d{2,3}(?:,\d{3})+)",
        # $100k - $150k
        r"\$(\d{2,3})\s*k\s*(?:-|to)\s*\$(\d{2,3})\s*k",
        # $45.00 - $65.00 an hour / per hour
        r"\$(\d{2,3}(?:\.\d{2})?)\s*(?:-|to)\s*\$(\d{2,3}(?:\.\d{2})?)\s*(?:per\s*hour|an\s*hour|/hr|\bhr\b)",
    ]
    
    for pat in patterns:
        match = re.search(pat, combined_text, re.IGNORECASE)
        if match:
            g1, g2 = match.group(1).replace(",", ""), match.group(2).replace(",", "")
            val1, val2 = float(g1), float(g2)
            
            # Check if hourly rate
            is_hourly = ("hour" in match.group(0).lower() or "/hr" in match.group(0).lower()) or (val1 < 200 and val2 < 200)
            
            if is_hourly:
                min_sal = val1 * 2080  # 40 hrs/wk * 52 wks
                max_sal = val2 * 2080
                pay_type = "hourly"
            else:
                if "k" in match.group(0).lower() and val1 < 1000:
                    val1 *= 1000
                    val2 *= 1000
                min_sal = val1
                max_sal = val2
                pay_type = "yearly"
                
            return {
                "salary_min": round(min_sal, 2),
                "salary_max": round(max_sal, 2),
                "salary_avg": round((min_sal + max_sal) / 2.0, 2),
                "pay_type": pay_type,
            }
            
    return {
        "salary_min": np.nan,
        "salary_max": np.nan,
        "salary_avg": np.nan,
        "pay_type": "N/A",
    }


def extract_work_modality(location: str, description: str, job_title: str) -> str:
    """Classify job as Remote, Hybrid, or On-site."""
    combined = f"{location or ''} {description or ''} {job_title or ''}".lower()
    
    if "hybrid" in combined:
        return "Hybrid"
    elif "remote" in combined or "work from home" in combined or "wfh" in combined:
        return "Remote"
    else:
        return "On-site"


def normalize_seniority(seniority_raw: str, job_title: str) -> str:
    """Normalize seniority level."""
    raw = str(seniority_raw).lower() if pd.notna(seniority_raw) else ""
    title = str(job_title).lower() if pd.notna(job_title) else ""
    
    if "senior" in raw or "sr" in title or "senior" in title or "lead" in title or "principal" in title:
        return "Senior"
    elif "mid" in raw or "mid-senior" in raw:
        return "Mid-Senior"
    elif "entry" in raw or "junior" in title or "jr" in title or "associate" in title or "intern" in title:
        return "Entry level"
    elif "director" in raw or "director" in title or "head of" in title or "vp" in title:
        return "Director"
    elif "executive" in raw or "exec" in title or "c-level" in title:
        return "Executive"
    else:
        return "Not Specified"


def clean_recruitment_data(raw_dir: str = "data/raw", output_file: str = "data/processed/all_jobs_clean.csv") -> pd.DataFrame:
    """Load all raw CSVs, clean, deduplicate, extract features, and export processed dataset."""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    raw_files = glob.glob(os.path.join(raw_dir, "*_raw.csv"))
    if not raw_files:
        print(f"[WARN] No raw CSV files found in {raw_dir}")
        return pd.DataFrame()
        
    print(f"[INFO] Found {len(raw_files)} raw data files: {[os.path.basename(f) for f in raw_files]}")
    
    df_list = []
    for f in raw_files:
        try:
            df = pd.read_csv(f)
            df_list.append(df)
        except Exception as e:
            print(f"[ERROR] Failed to read {f}: {e}")
            
    if not df_list:
        return pd.DataFrame()
        
    raw_df = pd.concat(df_list, ignore_index=True)
    initial_count = len(raw_df)
    print(f"[INFO] Total raw records loaded: {initial_count}")
    
    # 1. Deduplication
    # Deduplicate by job_link if present, or by combination of job_title and company_name
    raw_df.drop_duplicates(subset=["job_link"], keep="first", inplace=True)
    raw_df.drop_duplicates(subset=["job_title", "company_name", "category"], keep="first", inplace=True)
    dedup_count = len(raw_df)
    print(f"[INFO] Records after deduplication: {dedup_count} (Removed {initial_count - dedup_count} duplicates)")
    
    # 2. Text Cleaning
    raw_df["job_title"] = raw_df["job_title"].astype(str).str.strip()
    raw_df["company_name"] = raw_df["company_name"].astype(str).str.strip().replace("N/A", "Unknown Company")
    raw_df["location"] = raw_df["location"].astype(str).str.strip().replace("N/A", "Unknown Location")
    raw_df["description"] = raw_df["description"].astype(str).str.strip().replace("N/A", "")
    
    # 3. Feature Extractions
    # Skills
    raw_df["extracted_skills_list"] = raw_df.apply(
        lambda row: extract_skills(f"{row['job_title']} {row['description']}"), axis=1
    )
    raw_df["extracted_skills"] = raw_df["extracted_skills_list"].apply(lambda skills: ", ".join(skills) if skills else "None")
    raw_df["skill_count"] = raw_df["extracted_skills_list"].apply(len)
    
    # Salary Extraction
    salary_data = raw_df.apply(
        lambda row: extract_salary(str(row.get("salary", "")), str(row.get("description", ""))), axis=1
    )
    salary_df = pd.DataFrame(list(salary_data))
    raw_df["salary_min"] = salary_df["salary_min"]
    raw_df["salary_max"] = salary_df["salary_max"]
    raw_df["salary_avg"] = salary_df["salary_avg"]
    raw_df["pay_type"] = salary_df["pay_type"]
    
    # Work Modality
    raw_df["work_modality"] = raw_df.apply(
        lambda row: extract_work_modality(str(row["location"]), str(row["description"]), str(row["job_title"])), axis=1
    )
    
    # Seniority Level
    raw_df["seniority_clean"] = raw_df.apply(
        lambda row: normalize_seniority(str(row.get("seniority", "")), str(row["job_title"])), axis=1
    )
    
    # Category normalization and filtering
    raw_df["category"] = raw_df["category"].astype(str).str.lower().str.strip()
    valid_categories = ["data_analyst", "software_engineer", "marketing"]
    raw_df = raw_df[raw_df["category"].isin(valid_categories)].copy()

    
    # Save processed CSV
    raw_df.to_csv(output_file, index=False, encoding="utf-8")
    print(f"[SUCCESS] Cleaned dataset saved to: {output_file} (Total clean records: {len(raw_df)})")
    
    return raw_df


if __name__ == "__main__":
    clean_recruitment_data()
