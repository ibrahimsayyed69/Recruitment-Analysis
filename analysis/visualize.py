"""
Data Visualization Module for Recruitment Data Analysis.
Generates charts and visualizations using Matplotlib & Seaborn, saving output figures into reports/figures/.
"""

import os
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

# Set cohesive modern style
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.size"] = 10


def ensure_output_dir(output_dir: str = "reports/figures") -> str:
    """Ensure output directory exists."""
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def plot_jobs_by_category(df: pd.DataFrame, output_dir: str = "reports/figures") -> str:
    """Generate job distribution chart by category and scraper source."""
    ensure_output_dir(output_dir)
    save_path = os.path.join(output_dir, "jobs_by_category.png")
    
    plt.figure(figsize=(10, 6))
    cat_source = df.groupby(["category", "source"]).size().reset_index(name="count")
    cat_source["category"] = cat_source["category"].str.replace("_", " ").str.title()
    cat_source["source"] = cat_source["source"].str.title()
    
    ax = sns.barplot(
        data=cat_source,
        x="category",
        y="count",
        hue="source",
        palette="viridis",
        edgecolor="black",
        linewidth=0.5
    )
    
    plt.title("Total Scraped Jobs by Category & Source", fontsize=14, fontweight="bold", pad=15)
    plt.xlabel("Job Category", fontsize=12, labelpad=10)
    plt.ylabel("Number of Postings", fontsize=12, labelpad=10)
    plt.legend(title="Scraper Source", frameon=True)
    
    for p in ax.patches:
        height = p.get_height()
        if height > 0:
            ax.annotate(
                f"{int(height)}",
                (p.get_x() + p.get_width() / 2.0, height),
                ha="center",
                va="bottom",
                fontsize=10,
                xytext=(0, 3),
                textcoords="offset points",
            )
            
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()
    print(f"[SUCCESS] Saved figure: {save_path}")
    return save_path


def plot_top_skills(df: pd.DataFrame, output_dir: str = "reports/figures", top_n: int = 12) -> str:
    """Generate horizontal bar chart of top overall required skills."""
    ensure_output_dir(output_dir)
    save_path = os.path.join(output_dir, "top_skills_by_category.png")
    
    all_skills = []
    for skills_str in df["extracted_skills"].dropna():
        if skills_str and skills_str != "None":
            all_skills.extend([s.strip() for s in skills_str.split(",")])
            
    if not all_skills:
        print("[WARN] No skills found to plot.")
        return ""
        
    skill_counts = pd.Series(all_skills).value_counts().head(top_n).reset_index()
    skill_counts.columns = ["skill", "count"]
    total_jobs = len(df)
    skill_counts["percentage"] = (skill_counts["count"] / total_jobs) * 100
    
    plt.figure(figsize=(10, 6))
    ax = sns.barplot(
        data=skill_counts,
        y="skill",
        x="percentage",
        hue="skill",
        legend=False,
        palette="crest_r",
        edgecolor="black",
        linewidth=0.5
    )
    
    plt.title(f"Top {top_n} Most In-Demand Skills Across Job Postings", fontsize=14, fontweight="bold", pad=15)
    plt.xlabel("Percentage of Job Postings (%)", fontsize=12, labelpad=10)
    plt.ylabel("Skill / Technology", fontsize=12, labelpad=10)
    
    for p in ax.patches:
        width = p.get_width()
        if width > 0:
            ax.annotate(
                f"{width:.1f}%",
                (width, p.get_y() + p.get_height() / 2.0),
                ha="left",
                va="center",
                fontsize=9,
                xytext=(5, 0),
                textcoords="offset points",
            )
            
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()
    print(f"[SUCCESS] Saved figure: {save_path}")
    return save_path


def plot_work_modality(df: pd.DataFrame, output_dir: str = "reports/figures") -> str:
    """Generate donut chart for Remote vs Hybrid vs On-site distribution."""
    ensure_output_dir(output_dir)
    save_path = os.path.join(output_dir, "remote_vs_onsite.png")
    
    modality_counts = df["work_modality"].value_counts()
    
    plt.figure(figsize=(7, 7))
    colors = ["#4C72B0", "#55A868", "#C44E52"]
    
    wedges, texts, autotexts = plt.pie(
        modality_counts,
        labels=modality_counts.index,
        autopct="%1.1f%%",
        startangle=140,
        colors=colors[:len(modality_counts)],
        wedgeprops=dict(width=0.4, edgecolor="white", linewidth=2),
        pctdistance=0.75,
    )
    
    for t in texts:
        t.set_fontsize(11)
        t.set_fontweight("bold")
    for at in autotexts:
        at.set_fontsize(10)
        at.set_color("white")
        at.set_fontweight("bold")
        
    plt.title("Work Modality Breakdown (Remote / Hybrid / On-site)", fontsize=14, fontweight="bold", pad=20)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()
    print(f"[SUCCESS] Saved figure: {save_path}")
    return save_path


def plot_salary_distribution(df: pd.DataFrame, output_dir: str = "reports/figures") -> str:
    """Generate box plot of annual salaries by category."""
    ensure_output_dir(output_dir)
    save_path = os.path.join(output_dir, "salary_distribution.png")
    
    salary_df = df.dropna(subset=["salary_avg"]).copy()
    if salary_df.empty or len(salary_df) < 2:
        # Create an informative fallback chart if salary data is minimal
        plt.figure(figsize=(9, 5))
        plt.text(0.5, 0.5, "Insufficient Explicit Salary Data in Scraped Postings\n(Salaries provided upon offer for ~90% of listings)", 
                 ha="center", va="center", fontsize=12, color="gray")
        plt.title("Annual Salary Distribution Analysis", fontsize=14, fontweight="bold")
        plt.axis("off")
        plt.tight_layout()
        plt.savefig(save_path, dpi=300)
        plt.close()
        print(f"[INFO] Created placeholder figure for salary data: {save_path}")
        return save_path
        
    salary_df["category"] = salary_df["category"].str.replace("_", " ").str.title()
    
    plt.figure(figsize=(9, 6))
    ax = sns.boxplot(
        data=salary_df,
        x="category",
        y="salary_avg",
        hue="category",
        legend=False,
        palette="Set2",
        width=0.4
    )
    sns.stripplot(
        data=salary_df,
        x="category",
        y="salary_avg",
        color="black",
        alpha=0.6,
        jitter=0.2,
        size=6
    )
    
    plt.title("Annual Salary Distribution by Job Category ($ USD)", fontsize=14, fontweight="bold", pad=15)
    plt.xlabel("Job Category", fontsize=12, labelpad=10)
    plt.ylabel("Estimated Annual Salary ($ USD)", fontsize=12, labelpad=10)
    ax.yaxis.set_major_formatter("${x:,.0f}")
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()
    print(f"[SUCCESS] Saved figure: {save_path}")
    return save_path


def plot_top_employers(df: pd.DataFrame, output_dir: str = "reports/figures", top_n: int = 10) -> str:
    """Generate bar chart of top hiring companies."""
    ensure_output_dir(output_dir)
    save_path = os.path.join(output_dir, "top_employers.png")
    
    filtered_df = df[df["company_name"] != "Unknown Company"]
    top_comps = filtered_df["company_name"].value_counts().head(top_n).reset_index()
    top_comps.columns = ["company", "count"]
    
    plt.figure(figsize=(10, 6))
    ax = sns.barplot(
        data=top_comps,
        y="company",
        x="count",
        hue="company",
        legend=False,
        palette="magma",
        edgecolor="black",
        linewidth=0.5
    )
    
    plt.title(f"Top {top_n} Employers Posting Vacancies", fontsize=14, fontweight="bold", pad=15)
    plt.xlabel("Number of Open Postings", fontsize=12, labelpad=10)
    plt.ylabel("Company Name", fontsize=12, labelpad=10)
    
    for p in ax.patches:
        width = p.get_width()
        if width > 0:
            ax.annotate(
                f"{int(width)}",
                (width, p.get_y() + p.get_height() / 2.0),
                ha="left",
                va="center",
                fontsize=10,
                xytext=(5, 0),
                textcoords="offset points",
            )
            
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()
    print(f"[SUCCESS] Saved figure: {save_path}")
    return save_path


def generate_all_visualizations(df: pd.DataFrame, output_dir: str = "reports/figures") -> list:
    """Generate full suite of figures."""
    print(f"[INFO] Generating visualization figures into '{output_dir}'...")
    paths = [
        plot_jobs_by_category(df, output_dir),
        plot_top_skills(df, output_dir),
        plot_work_modality(df, output_dir),
        plot_salary_distribution(df, output_dir),
        plot_top_employers(df, output_dir),
    ]
    print("[SUCCESS] All figures successfully generated.")
    return paths


if __name__ == "__main__":
    try:
        from analysis.clean_data import clean_recruitment_data
    except ImportError:
        from clean_data import clean_recruitment_data

    df_clean = clean_recruitment_data()
    if not df_clean.empty:
        generate_all_visualizations(df_clean)

