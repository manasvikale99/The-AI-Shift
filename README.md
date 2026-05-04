# The AI Shift

**How artificial intelligence reshaped knowledge work in America, 2020–2026**

An interactive data visualization exploring the relationship between the pace of AI model releases and U.S. knowledge worker job markets — wages, hiring, and employment across six occupation groups.

## Live Demo

**[View the interactive visualization →](https://manasvikale.github.io/511-ai-shift/)**

## What You'll See

- **Section 1 — Hero:** 128 AI model releases animated across the screen, milestones glowing pink
- **Section 2 — The Pulse:** U.S. job posting index overlaid with AI release pressure, 2020–2026. Click sector cards to overlay individual sectors. Drag to zoom.
- **Section 3 — Inside the Numbers:** Wage range bars (10th–90th percentile) and employment trends for each occupation group, 2020–2024
- **Section 4 — Augmented or Disrupted?:** Animated bubble chart — each bubble is one occupation group in one year, positioned by AI pressure vs. wage growth

## Data Sources

| Dataset | Source |
|---|---|
| AI model releases | [Epoch AI Notable Models Database](https://epochai.org/data/notable-ai-models) |
| U.S. job postings index | [Indeed Hiring Lab](https://www.hiringlab.org/) |
| Occupation wages & employment | [BLS Occupational Employment & Wage Statistics](https://www.bls.gov/oes/tables.htm) |

> **Note:** BLS raw XLSX files (~380MB) are not included in this repo due to size. Download them from [bls.gov/oes/tables.htm](https://www.bls.gov/oes/tables.htm) and place them in `BLS Occupational Employment Data - 5 Years/` before running the pipeline.

## Reproducing the Data Pipeline

```bash
# 1. Install dependencies
pip install pandas openpyxl

# 2. Run the data preparation script
python prepare_data.py

# 3. Open the visualization
open viz/index.html
```

The script produces 6 cleaned CSV files in `processed/` and the visualization reads from those.

## Project Structure

```
├── AI Model Releases/          # Raw AI model CSV (Epoch AI)
├── Indeed Postings/            # Indeed job postings CSVs
├── processed/                  # Cleaned data outputs
│   ├── ai_milestones.csv
│   ├── ai_pressure_monthly.csv
│   ├── bls_wages_clean.csv
│   ├── indeed_aggregate_clean.csv
│   ├── indeed_sectors_clean.csv
│   └── wage_growth_summary.csv
├── viz/
│   └── index.html              # Self-contained D3.js visualization
└── prepare_data.py             # Data pipeline script
```
