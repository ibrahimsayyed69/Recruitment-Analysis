"""
Recruitment Data Analysis & Market Intelligence Module.
Loads cleaned dataset from data/processed/all_jobs_clean.csv and computes statistical insights:
- Job volumes per category and source
- Top skills frequency per category
- Salary distributions by category and seniority
- Work modality breakdown
- Top hiring employers & location clusters
"""

import os
from collections import Counter
import pandas as pd
import numpy as np


def load_processed_data(filepath: str = "data/processed/all_jobs_clean.csv") -> pd.DataFrame:
    """Load cleaned job dataset."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Cleaned dataset not found at {filepath}. Run clean_data.py first.")
    return pd.read_csv(filepath)


def get_dataset_overview(df: pd.DataFrame) -> dict:
    """Compute top-level summary metrics of the dataset."""
    return {
        "total_jobs": len(df),
        "total_categories": df["category"].nunique(),
        "categories_list": list(df["category"].unique()),
        "total_sources": df["source"].nunique(),
        "sources_list": list(df["source"].unique()),
        "total_companies": df["company_name"].nunique(),
        "total_locations": df["location"].nunique(),
        "date_scraped_range": {
            "min": str(df["scraped_at"].min()) if "scraped_at" in df.columns else "N/A",
            "max": str(df["scraped_at"].max()) if "scraped_at" in df.columns else "N/A",
        },
    }


def get_category_counts(df: pd.DataFrame) -> pd.DataFrame:
    """Compute job count distribution per category and source."""
    return df.groupby(["category", "source"]).size().unstack(fill_value=0)


def get_top_skills_by_category(df: pd.DataFrame, top_n: int = 15) -> dict:
    """Calculate the most requested skills per category and overall."""
    category_skills = {}
    
    for category, cat_df in df.groupby("category"):
        skill_counts = Counter()
        total_cat_jobs = len(cat_df)
        
        for skills_str in cat_df["extracted_skills"].dropna():
            if skills_str and skills_str != "None":
                skills_list = [s.strip() for s in skills_str.split(",")]
                skill_counts.update(skills_list)
                
        top_skills = []
        for skill, count in skill_counts.most_common(top_n):
            top_skills.append({
                "skill": skill,
                "count": count,
                "percentage": round((count / total_cat_jobs) * 100, 1),
            })
            
        category_skills[category] = top_skills
        
    # Overall top skills
    overall_counts = Counter()
    total_jobs = len(df)
    for skills_str in df["extracted_skills"].dropna():
        if skills_str and skills_str != "None":
            overall_counts.update([s.strip() for s in skills_str.split(",")])
            
    category_skills["overall"] = [
        {"skill": skill, "count": count, "percentage": round((count / total_jobs) * 100, 1)}
        for skill, count in overall_counts.most_common(top_n)
    ]
    
    return category_skills


def get_salary_analysis(df: pd.DataFrame) -> dict:
    """Compute salary statistics by category and seniority."""
    salary_df = df.dropna(subset=["salary_avg"])
    
    if salary_df.empty:
        return {"has_salary_data": False, "summary": "No salary data available in dataset."}
        
    category_salary = {}
    for category, cat_df in salary_df.groupby("category"):
        category_salary[category] = {
            "count": len(cat_df),
            "mean": round(cat_df["salary_avg"].mean(), 2),
            "median": round(cat_df["salary_avg"].median(), 2),
            "min": round(cat_df["salary_avg"].min(), 2),
            "max": round(cat_df["salary_avg"].max(), 2),
            "p25": round(cat_df["salary_avg"].quantile(0.25), 2),
            "p75": round(cat_df["salary_avg"].quantile(0.75), 2),
        }
        
    seniority_salary = {}
    for seniority, sen_df in salary_df.groupby("seniority_clean"):
        seniority_salary[seniority] = {
            "count": len(sen_df),
            "mean": round(sen_df["salary_avg"].mean(), 2),
            "median": round(sen_df["salary_avg"].median(), 2),
        }
        
    return {
        "has_salary_data": True,
        "total_jobs_with_salary": len(salary_df),
        "overall_mean": round(salary_df["salary_avg"].mean(), 2),
        "overall_median": round(salary_df["salary_avg"].median(), 2),
        "by_category": category_salary,
        "by_seniority": seniority_salary,
    }


def get_work_modality_distribution(df: pd.DataFrame) -> dict:
    """Compute distribution of Remote, Hybrid, and On-site jobs."""
    counts = df["work_modality"].value_counts().to_dict()
    total = len(df)
    return {
        modality: {"count": count, "percentage": round((count / total) * 100, 1)}
        for modality, count in counts.items()
    }


def get_top_employers(df: pd.DataFrame, top_n: int = 10) -> list:
    """Get companies posting the highest number of jobs."""
    filtered_df = df[df["company_name"] != "Unknown Company"]
    counts = filtered_df["company_name"].value_counts().head(top_n).to_dict()
    return [{"company": comp, "count": cnt} for comp, cnt in counts.items()]


def run_full_analysis(filepath: str = "data/processed/all_jobs_clean.csv") -> dict:
    """Run all analytics routines and return complete insights payload."""
    df = load_processed_data(filepath)
    
    print(f"[INFO] Running full data analysis on {len(df)} records...")
    
    insights = {
        "overview": get_dataset_overview(df),
        "category_counts": get_category_counts(df).to_dict(),
        "top_skills": get_top_skills_by_category(df),
        "salary_stats": get_salary_analysis(df),
        "work_modality": get_work_modality_distribution(df),
        "top_employers": get_top_employers(df),
    }
    
    print("[SUCCESS] Data analysis complete.")
    return insights


if __name__ == "__main__":
    results = run_full_analysis()
    print("\n=== DATASET OVERVIEW ===")
    print(results["overview"])
    print("\n=== WORK MODALITY ===")
    print(results["work_modality"])
    print("\n=== TOP SKILLS OVERALL ===")
    print(results["top_skills"].get("overall", []))
