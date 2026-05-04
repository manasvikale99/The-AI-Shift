import pandas as pd
import numpy as np
import os
from pathlib import Path

BASE = Path("/Users/manasvikale/Desktop/511 Dataset")
AI_DIR = BASE / "AI Model Releases"
BLS_DIR = BASE / "BLS Occupational Employment Data - 5 Years"
INDEED_DIR = BASE / "Indeed Postings"
OUT = BASE / "processed"
OUT.mkdir(exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — AI models timeline
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("STEP 1 — AI Models Timeline")
print("="*60)

df_ai = pd.read_csv(AI_DIR / "Copy of all_ai_models - ai models sorted.csv")

# Parse and filter dates
df_ai["Publication date"] = pd.to_datetime(df_ai["Publication date"], errors="coerce")
df_ai = df_ai[
    df_ai["Publication date"].notna() &
    (df_ai["Publication date"] >= "2020-01-01") &
    (df_ai["Publication date"] <= "2026-05-01")
].copy()

keep_cols = [
    "Model", "Organization", "Domain", "Task",
    "Publication date", "Model accessibility",
    "Organization categorization", "Open model weights?"
]
df_ai = df_ai[keep_cols].sort_values("Publication date").reset_index(drop=True)

# Milestone flag
milestones = [
    "GPT-3", "GPT-4", "GPT-4o", "ChatGPT", "DALL-E",
    "Stable Diffusion", "Midjourney", "Claude 2", "Claude 3",
    "Gemini", "Llama 2", "Llama 3", "Sora", "o1", "o3"
]
pattern = "|".join(milestones)
df_ai["is_milestone"] = df_ai["Model"].str.contains(pattern, case=False, na=False)

# domain_simplified
def simplify_domain(d):
    if pd.isna(d):
        return "Other"
    d = str(d)
    if "Language" in d:
        return "Language"
    if "Image generation" in d:
        return "Image/Vision"
    if "Video" in d:
        return "Video"
    if "Speech" in d:
        return "Speech"
    if "Vision" in d:
        return "Image/Vision"
    return "Other"

df_ai["domain_simplified"] = df_ai["Domain"].apply(simplify_domain)

df_ai.to_csv(OUT / "ai_milestones.csv", index=False)
print(f"  Total rows saved : {len(df_ai)}")
print(f"  Milestones        : {df_ai['is_milestone'].sum()}")
print(f"  Date range        : {df_ai['Publication date'].min().date()} → {df_ai['Publication date'].max().date()}")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — BLS wage data
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("STEP 2 — BLS Wage Data")
print("="*60)

KEEP_OCC = ["11-0000", "13-0000", "15-0000", "17-0000", "19-0000", "27-0000"]
SECTOR_LABELS = {
    "11-0000": "Management",
    "13-0000": "Business & Finance",
    "15-0000": "Tech & Computing",
    "17-0000": "Engineering",
    "19-0000": "Science & Research",
    "27-0000": "Arts & Media",
}
WAGE_COLS = ["TOT_EMP", "A_MEDIAN", "A_MEAN", "A_PCT10", "A_PCT25", "A_PCT75", "A_PCT90", "H_MEDIAN"]

frames = []
for year in range(2020, 2025):
    path = BLS_DIR / f"all_data_M_{year}.xlsx"
    df = pd.read_excel(path, dtype=str)
    df["year"] = year

    # Normalise column names (strip whitespace)
    df.columns = df.columns.str.strip()

    # Filters
    df = df[df["AREA_TYPE"].astype(str).str.strip() == "1"]
    df = df[df["NAICS_TITLE"].astype(str).str.strip() == "Cross-industry"]
    df = df[df["O_GROUP"].astype(str).str.strip() == "major"]
    df = df[df["OCC_CODE"].astype(str).str.strip().isin(KEEP_OCC)]

    keep = ["year", "OCC_CODE", "OCC_TITLE"] + WAGE_COLS
    # Only keep columns that exist in this file
    keep = [c for c in keep if c in df.columns]
    df = df[keep].copy()
    frames.append(df)
    print(f"  {year}: {len(df)} rows after filters")

df_bls = pd.concat(frames, ignore_index=True)

# Clean wage columns
def clean_numeric(series):
    return pd.to_numeric(
        series.astype(str).str.strip().replace({"#": np.nan, "*": np.nan, "**": np.nan}),
        errors="coerce"
    )

for col in WAGE_COLS:
    if col in df_bls.columns:
        df_bls[col] = clean_numeric(df_bls[col])

df_bls["OCC_CODE"] = df_bls["OCC_CODE"].astype(str).str.strip()
df_bls["sector_label"] = df_bls["OCC_CODE"].map(SECTOR_LABELS)

df_bls.to_csv(OUT / "bls_wages_clean.csv", index=False)
print(f"  Total rows        : {len(df_bls)}")
print(f"  Unique OCC_CODEs  : {df_bls['OCC_CODE'].nunique()} → {sorted(df_bls['OCC_CODE'].unique())}")
print(f"  Unique years      : {sorted(df_bls['year'].unique())}")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — Indeed sector postings
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("STEP 3 — Indeed Sector Postings")
print("="*60)

KW_SECTORS = [
    "Accounting", "Data & Analytics", "Software Development",
    "IT Infrastructure, Operations & Support", "IT Systems & Solutions",
    "Arts & Entertainment", "Marketing", "Media & Communications",
    "Scientific Research & Development", "Human Resources", "Project Management"
]
SECTOR_GROUP = {
    "Accounting": "Business & Finance",
    "Data & Analytics": "Tech & Computing",
    "Software Development": "Tech & Computing",
    "IT Infrastructure, Operations & Support": "Tech & Computing",
    "IT Systems & Solutions": "Tech & Computing",
    "Arts & Entertainment": "Arts & Media",
    "Marketing": "Business & Finance",
    "Media & Communications": "Arts & Media",
    "Scientific Research & Development": "Science & Research",
    "Human Resources": "Management",
    "Project Management": "Management",
}

df_sec = pd.read_csv(INDEED_DIR / "job_postings_by_sector_US.csv")
df_sec["date"] = pd.to_datetime(df_sec["date"], errors="coerce")
df_sec = df_sec[df_sec["display_name"].isin(KW_SECTORS)].copy()

# Pivot variable column
df_sec_pivot = df_sec.pivot_table(
    index=["date", "display_name"],
    columns="variable",
    values="indeed_job_postings_index",
    aggfunc="first"
).reset_index()
df_sec_pivot.columns.name = None

# Rename pivoted columns
rename_map = {}
if "new postings" in df_sec_pivot.columns:
    rename_map["new postings"] = "new_postings_index"
if "total postings" in df_sec_pivot.columns:
    rename_map["total postings"] = "total_postings_index"
df_sec_pivot = df_sec_pivot.rename(columns=rename_map)

df_sec_pivot["sector_group"] = df_sec_pivot["display_name"].map(SECTOR_GROUP)

# Join job titles — with fallbacks for the 3 sectors not in the lookup file
df_titles = pd.read_csv(INDEED_DIR / "sector-job-title-examples.csv")
# "Data & Analytics" ↔ Software Development titles; IT sectors ↔ IT Operations & Helpdesk
TITLE_FALLBACKS = {
    "Data & Analytics": "Software Development",
    "IT Infrastructure, Operations & Support": "IT Operations & Helpdesk",
    "IT Systems & Solutions": "IT Operations & Helpdesk",
}
titles_map = df_titles.set_index("sector")["job_titles"].to_dict()
def lookup_titles(name):
    return titles_map.get(name) or titles_map.get(TITLE_FALLBACKS.get(name, ""))

df_sec_pivot["job_titles"] = df_sec_pivot["display_name"].apply(lookup_titles)

df_sec_pivot.to_csv(OUT / "indeed_sectors_clean.csv", index=False)
print(f"  Total rows        : {len(df_sec_pivot)}")
print(f"  Date range        : {df_sec_pivot['date'].min().date()} → {df_sec_pivot['date'].max().date()}")
print(f"  Unique sectors    : {df_sec_pivot['display_name'].nunique()} → {sorted(df_sec_pivot['display_name'].unique())}")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — Indeed aggregate postings
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("STEP 4 — Indeed Aggregate Postings")
print("="*60)

df_agg = pd.read_csv(INDEED_DIR / "aggregate_job_postings_US.csv")
df_agg["date"] = pd.to_datetime(df_agg["date"], errors="coerce")
df_agg = df_agg[df_agg["variable"] == "new postings"].copy()
df_agg = df_agg[["date", "indeed_job_postings_index_SA", "indeed_job_postings_index_NSA"]].rename(columns={
    "indeed_job_postings_index_SA": "new_postings_SA",
    "indeed_job_postings_index_NSA": "new_postings_NSA",
})

df_agg.to_csv(OUT / "indeed_aggregate_clean.csv", index=False)
print(f"  Total rows        : {len(df_agg)}")
print(f"  Date range        : {df_agg['date'].min().date()} → {df_agg['date'].max().date()}")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 — AI pressure score (monthly)
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("STEP 5 — AI Pressure Score")
print("="*60)

df_mil = pd.read_csv(OUT / "ai_milestones.csv")
df_mil["Publication date"] = pd.to_datetime(df_mil["Publication date"])
df_mil["month"] = df_mil["Publication date"].dt.to_period("M").dt.to_timestamp()

monthly = df_mil.groupby("month").agg(
    total_releases=("Model", "count"),
    milestone_releases=("is_milestone", "sum")
).reset_index()
monthly["weighted_pressure"] = (
    monthly["milestone_releases"] * 3 +
    (monthly["total_releases"] - monthly["milestone_releases"]) * 1
)

# Full monthly spine 2020-02 to 2026-04
full_index = pd.date_range("2020-02-01", "2026-04-01", freq="MS")
df_pressure = pd.DataFrame({"month": full_index})
df_pressure = df_pressure.merge(monthly, on="month", how="left").fillna(0)
for col in ["total_releases", "milestone_releases", "weighted_pressure"]:
    df_pressure[col] = df_pressure[col].astype(int)

df_pressure = df_pressure.sort_values("month")
df_pressure["rolling_3m_pressure"] = (
    df_pressure["weighted_pressure"].rolling(3, min_periods=1).mean().round(2)
)

df_pressure.to_csv(OUT / "ai_pressure_monthly.csv", index=False)

top10 = df_pressure.nlargest(10, "weighted_pressure")[["month", "weighted_pressure", "milestone_releases", "total_releases"]]
print("  Top 10 highest-pressure months:")
print(top10.to_string(index=False))

# ─────────────────────────────────────────────────────────────────────────────
# STEP 6 — Wage growth summary
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("STEP 6 — Wage Growth Summary")
print("="*60)

df_bls2 = pd.read_csv(OUT / "bls_wages_clean.csv")

# Baseline from 2020
baseline = df_bls2[df_bls2["year"] == 2020][["OCC_CODE", "A_MEDIAN", "TOT_EMP"]].rename(
    columns={"A_MEDIAN": "baseline_median", "TOT_EMP": "baseline_emp"}
)

df_growth = df_bls2.merge(baseline, on="OCC_CODE", how="left")
df_growth["wage_growth_pct"] = (
    (df_growth["A_MEDIAN"] - df_growth["baseline_median"]) / df_growth["baseline_median"] * 100
).round(2)
df_growth["emp_growth_pct"] = (
    (df_growth["TOT_EMP"] - df_growth["baseline_emp"]) / df_growth["baseline_emp"] * 100
).round(2)

out_cols = ["year", "OCC_CODE", "OCC_TITLE", "sector_label",
            "A_MEDIAN", "TOT_EMP", "wage_growth_pct", "emp_growth_pct",
            "A_PCT10", "A_PCT90"]
df_growth = df_growth[[c for c in out_cols if c in df_growth.columns]]
df_growth.to_csv(OUT / "wage_growth_summary.csv", index=False)

# Print highlights for 2024
df_2024 = df_growth[df_growth["year"] == 2024]
if not df_2024.empty:
    best_wage = df_2024.loc[df_2024["wage_growth_pct"].idxmax()]
    best_emp  = df_2024.loc[df_2024["emp_growth_pct"].idxmax()]
    print(f"  Biggest wage growth 2020→2024  : {best_wage['sector_label']} ({best_wage['wage_growth_pct']:+.1f}%)")
    print(f"  Biggest emp growth  2020→2024  : {best_emp['sector_label']}  ({best_emp['emp_growth_pct']:+.1f}%)")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 7 — Verification report
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("STEP 7 — Verification Report")
print("="*60)

files = {
    "ai_milestones.csv":        (None, ["Publication date"]),
    "bls_wages_clean.csv":      (None, None),
    "indeed_sectors_clean.csv": (None, ["date"]),
    "indeed_aggregate_clean.csv":(None, ["date"]),
    "ai_pressure_monthly.csv":  (None, ["month"]),
    "wage_growth_summary.csv":  (None, None),
}

all_exist = True
for fname, (_, date_cols) in files.items():
    fpath = OUT / fname
    if not fpath.exists():
        print(f"  ❌ MISSING: {fname}")
        all_exist = False
        continue
    df = pd.read_csv(fpath)
    date_range_str = ""
    if date_cols:
        for dc in date_cols:
            if dc in df.columns:
                col = pd.to_datetime(df[dc], errors="coerce")
                date_range_str = f"  [{col.min().date()} → {col.max().date()}]"
    print(f"\n  ✅ {fname}")
    print(f"     Rows: {len(df)}{date_range_str}")
    # Flag columns with >15% nulls
    null_pct = df.isnull().mean()
    flagged = null_pct[null_pct > 0.15]
    if not flagged.empty:
        for col, pct in flagged.items():
            print(f"     ⚠️  '{col}' has {pct*100:.1f}% nulls")

if all_exist:
    print("\n  All 6 processed files confirmed ✅")
