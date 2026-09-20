from numbers import Number
from unicodedata import category
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="Recruitment Data Dashboard", layout="wide")
sns.set_theme(style="whitegrid")

@st.cache_data
def load_data():
    return pd.read_csv("data/processed/all_jobs_clean.csv")

df = load_data()

st.title("Recruitment Data Dashboard - Employer Hiring Behavior")
st.caption("Source: LinkedIn public job search (logged out) | Data Analyst, Software Engineer, Marketing")


categories = st.sidebar.multiselect(
    "Filter by category",
    options=df["category"].unique(),
    default=list(df["category"].unique())
)
filtered = df[df["category"].isin(categories)]


col1, col2, col3 = st.columns(3)
col1.metric("Total Postings", len(filtered))
col2.metric("Unique Companies", filtered["company_name"].nunique())
if "salary_disclosed" in filtered.columns:
    rate = filtered["salary_disclosed"].mean() * 100
    col3.metric("Salary Dsiclosed Rate", f"{rate:.1f}%")

st.divider()

st.subheader("Posting by Category")
counts = filtered["category"].value_counts()
fig, ax = plt.subplots(figsize=(8, 4))
sns.barplot(x=counts.index, y=counts.values, ax=ax)
ax.set_ylabel("Number of Ppsting")
st.pyplot(fig)

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Top 10 Hiring Companies")
    top_companies = filtered["company_name"].value_counts().head(10)
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.barplot(x=top_companies.values, y=top_companies.index, orient="h", ax=ax)
    ax.set_xlabel("Posting")
    st.pyplot(fig)

with col_right:
    st.subheader("Top 10 Locations")
    top_locations = filtered["location"].value_counts().head(10)
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.barplot(x=top_locations.values, y=top_locations.index, orient="h", ax=ax)
    ax.set_xlabel("Posting")
    st.pyplot(fig)

if "seniority" in filtered.columns:
    st.subheader("Seniority Level Breakdown")
    seniority_counts= filtered["seniority"].value_counts()
    fig, ax = plt.subplots(figsize=(8, 4))
    sns.barplot(x=seniority_counts.values, y=seniority_counts.index, orient="h", ax=ax)
    ax.set_xlabel("Posting")
    st.pyplot(fig)

st.divider()
st.subheader("Raw Data")
st.dataframe(filtered[["job_title", "company_name", "location", "category", "posted_date_text"]], use_container_width=True)

