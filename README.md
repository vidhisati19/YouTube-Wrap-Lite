# YouTube Music Taste Audit (Google Takeout Analysis)

## Overview
This project analyzes my **YouTube watch history** (exported via Google Takeout) to understand my **music listening habits over time**.  
The goal was to build a **data-heavy, end-to-end analysis pipeline** — starting from raw HTML files and ending with cleaned datasets, visualizations, and behavioral insights.

The project focuses on:
- Time-based listening patterns (hour, weekday, trends)
- Artist / channel preferences
- Late-night listening behavior
- Long-term changes in music consumption

---

## Dataset
- Source: **Google Takeout → YouTube Watch History**
- Format: HTML (`watch-history.html`)
- Raw size: **~72,000 watch events**
- Time span: **2022 – early 2026**

Only **watch-history** data is used (search history is ignored).

---

## Project Pipeline

### 1. HTML Parsing
- Parsed YouTube Takeout HTML using **BeautifulSoup**
- Extracted:
  - Video title
  - Channel / artist (with multiple fallbacks)
  - Timestamp
  - URL (when available)
- Robust handling of inconsistent HTML structures

### 2. Data Cleaning & Feature Engineering
- Cleaned timestamps (Unicode spaces, timezone suffixes)
- Converted to datetime
- Engineered features:
  - `hour`
  - `weekday`
  - `date`
  - `month`
  - `is_late_night` (00:00–04:00)

### 3. Music Classification
Used a **rule-based filter** to identify music-related content:
- Included: Official videos, lyrics, audio, MV, live performances, devotional music
- Excluded: Ads, promotions, tutorials, reviews, trailers, podcasts

Final music dataset:
- **~17,000 music watch events**

### 4. Analysis & Visualization
Generated the following insights:
- Top artists / channels
- Music watches by hour
- Music watches over time (daily trend)
- Weekday × hour heatmap

All plots are saved automatically.

---

## Key Findings

- **Peak listening hour:** 10 PM (22:00)
- **Most active listening days:** Sundays and Wednesday nights
- **Top music sources:**  
  - SonyMusicIndiaVEVO  
  - HYBE LABELS  
  - Zee Music Company  
  - T-Series  
- Strong presence of **Indian music, K-pop, Western pop, and devotional music**
- Music consumption increased significantly from **mid-2024 onward**

---

## Outputs

All outputs are saved in the `output/` folder:
output/
1. watch_parsed_raw.csv # Raw parsed watch history
2. watch_cleaned.csv # Cleaned timestamps + features
3. music_only.csv # Music-filtered dataset
4. 1_top_channels.png
5. 2_by_hour.png
6. 03_over_time_daily.png
7. 04_weekday_hour_heatmap.png
8. mini_report.txt # Summary template

---

## Technologies Used
- Python 3
- pandas
- BeautifulSoup (bs4)
- matplotlib
- Regular expressions

---

## How to Run

1. Place `watch-history.html` in:
   wrap/history/

2. Run:
  ```bash
  python3 wrap.py

3. View results in:
   wrap/output/
