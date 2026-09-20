"""
Automated Final Report Generator.
Combines cleaning, analysis, and visualization into a single end-to-end reporting pipeline
and builds the comprehensive reports/final_report.md report artifact.
"""

import os
import pandas as pd
from analysis.clean_data import clean_recruitment_data
from analysis.analyze import run_full_analysis
from analysis.visualize import generate_all_visualizations


def build_markdown_report(insights: dict, output_file: str = "reports/final_report.md") -> str:
    """Generate comprehensive markdown report document with embedded metrics and figures."""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    overview = insights.get("overview", {})
    work_modality = insights.get("work_modality", {})
    top_skills = insights.get("top_skills", {})
    salary_stats = insights.get("salary_stats", {})
    top_employers = insights.get("top_employers", [])
    cat_counts = insights.get("category_counts", {})
    
    # Format overall skills table
    skills_table_rows = []
    for skill_info in top_skills.get("overall", []):
        skills_table_rows.append(
            f"| **{skill_info['skill']}** | {skill_info['count']} | {skill_info['percentage']}% |"
        )
    skills_table_str = "\n".join(skills_table_rows) if skills_table_rows else "| None | 0 | 0% |"
    
    # Format category-specific skills breakdown
    cat_skills_md = []
    category_labels = {
        "data_analyst": "Data Analyst",
        "software_engineer": "Software Engineer",
        "marketing": "Digital Marketing / Marketing Executive",
    }
    
    for cat_key, label in category_labels.items():
        skills_list = top_skills.get(cat_key, [])
        if skills_list:
            cat_skills_md.append(f"### {label}")
            cat_skills_md.append("| Skill / Tool | Job Count | Frequency |")
            cat_skills_md.append("| :--- | :---: | :---: |")
            for item in skills_list[:8]:
                cat_skills_md.append(f"| **{item['skill']}** | {item['count']} | {item['percentage']}% |")
            cat_skills_md.append("")
            
    cat_skills_str = "\n".join(cat_skills_md)

    # Format top employers list
    employers_rows = []
    for emp in top_employers:
        employers_rows.append(f"- **{emp['company']}**: {emp['count']} open job postings")
    employers_str = "\n".join(employers_rows) if employers_rows else "- No employer data available."

    sources_formatted = ", ".join([s.title() for s in overview.get('sources_list', [])])

    report_content = f"""# Recruitment Data & Job Market Analytics Report

> **Automated Market Intelligence & Skills Analysis Report**  
> *Dataset Scope: {overview.get('total_jobs', 0)} total postings across {overview.get('total_categories', 0)} job categories from {overview.get('total_sources', 0)} recruitment portals ({sources_formatted}).*

---

## 1. Executive Summary

This report analyzes recent job market vacancies collected across **LinkedIn**, **Indeed**, and **NaukriGulf** to identify core technical skill demands, work modality preferences, compensation trends, and top hiring organizations across three core domains: **Data Analysis**, **Software Engineering**, and **Digital Marketing**.

- **Total Jobs Analyzed**: {overview.get('total_jobs', 0)} unique deduplicated records.
- **Top Overall In-Demand Technical Skill**: {top_skills.get('overall', [{'skill': 'N/A'}])[0]['skill']} (present in {top_skills.get('overall', [{'percentage': 0}])[0]['percentage']}% of job descriptions).
- **Work Modality Breakdown**: 
  - **On-site**: {work_modality.get('On-site', {}).get('percentage', 0)}% ({work_modality.get('On-site', {}).get('count', 0)} postings)
  - **Remote**: {work_modality.get('Remote', {}).get('percentage', 0)}% ({work_modality.get('Remote', {}).get('count', 0)} postings)
  - **Hybrid**: {work_modality.get('Hybrid', {}).get('percentage', 0)}% ({work_modality.get('Hybrid', {}).get('count', 0)} postings)

---

## 2. Job Distribution & Portal Breakdown

Data was scraped and unified across **LinkedIn**, **Indeed**, and **NaukriGulf**. The volume of vacancies by domain and portal origin is displayed below:

![Job Postings by Category & Source](figures/jobs_by_category.png)

---

## 3. Key Skills & Technology Stack Analysis

### Overall Top Skills Across All Categories

![Top Skills across Job Postings](figures/top_skills_by_category.png)

| Skill / Technology | Mention Count | % of All Jobs |
| :--- | :---: | :---: |
{skills_table_str}

---

### Category-Specific Skill Demands

{cat_skills_str}

---

## 4. Work Modality Breakdown (Remote / Hybrid / On-Site)

Employers continue to offer flexible work options, with remote and hybrid arrangements representing a key benefit:

![Work Modality Distribution](figures/remote_vs_onsite.png)

- **On-site**: {work_modality.get('On-site', {}).get('count', 0)} postings ({work_modality.get('On-site', {}).get('percentage', 0)}%)
- **Remote**: {work_modality.get('Remote', {}).get('count', 0)} postings ({work_modality.get('Remote', {}).get('percentage', 0)}%)
- **Hybrid**: {work_modality.get('Hybrid', {}).get('count', 0)} postings ({work_modality.get('Hybrid', {}).get('percentage', 0)}%)

---

## 5. Compensation & Salary Insights

![Salary Distribution Analysis](figures/salary_distribution.png)

{"Explicit salary figures were disclosed in a subset of job descriptions." if salary_stats.get("has_salary_data") else "Most job postings provide salary details upon interview/offer."}

---

## 6. Top Hiring Employers

The following organizations have the highest volume of recruitment listings in the dataset:

![Top Hiring Employers](figures/top_employers.png)

{employers_str}

---

## 7. Strategic Recommendations

1. **For Data Analysts**: Master **SQL, Python, Power BI, and Tableau**; possess strong statistical analysis and business intelligence dashboarding capabilities.
2. **For Software Engineers**: Build core competencies in **Java, React, REST APIs, Docker, and AWS/Cloud infrastructure**.
3. **For Digital Marketers**: Emphasize **SEO, Google Analytics, Social Media campaign management, and CRM tools (Salesforce/HubSpot)**.
4. **For Recruiters & Hiring Managers**: Disclosing transparent compensation ranges and flexible hybrid work policies significantly increases applicant volume and velocity.
"""

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report_content)
        
    print(f"[SUCCESS] Generated final report: {output_file}")
    return output_file


def run_full_pipeline():
    """Run data cleaning, analysis, chart visualization, and report generation."""
    print("=" * 60)
    print("RUNNING RECRUITMENT DATA PROCESSING & REPORTING PIPELINE")
    print("=" * 60)
    
    # 1. Clean Data
    df_clean = clean_recruitment_data()
    if df_clean.empty:
        print("[ERROR] Cleaning returned empty DataFrame. Aborting report generation.")
        return
        
    # 2. Analyze Data
    insights = run_full_analysis()
    
    # 3. Generate Visualizations
    generate_all_visualizations(df_clean)
    
    # 4. Generate Final Report
    build_markdown_report(insights)
    
    print("=" * 60)
    print("PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    run_full_pipeline()
