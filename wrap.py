import os
import re
import pandas as pd
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt

# =============================
# CONFIG
# =============================
BASE_DIR = "/Users/vidhi/Desktop/wrap"
HISTORY_DIR = os.path.join(BASE_DIR, "history")
WATCH_HTML = os.path.join(HISTORY_DIR, "watch-history.html")
OUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUT_DIR, exist_ok=True)

# =============================
# PARSE WATCH HISTORY HTML (channel extraction)
# =============================
def parse_watch_history_html(filepath: str) -> pd.DataFrame:
    with open(filepath, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "lxml")

    cells = soup.find_all("div", class_="content-cell")

    month_pat = r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
    time_regex = re.compile(rf"{month_pat}\s+\d{{1,2}},\s+\d{{4}}.*")

    rows = []
    for c in cells:
        txt = c.get_text(" ", strip=True)
        if not txt.startswith("Watched"):
            continue

        # Title: first link is usually the video
        links = c.find_all("a")
        title = None
        channel = None
        url = None

        if links:
            # first link tends to be video link
            title = links[0].get_text(strip=True)
            url = links[0].get("href")

            # channel is usually the SECOND link (subtitles "by CHANNEL")
            # Many Takeout HTMLs show: Watched <video> <br> <a>CHANNEL</a> <br> timestamp
            if len(links) >= 2:
                channel = links[1].get_text(strip=True)
        if channel is None:
            m = re.search(
                r"by\s+(.+?)\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4}",
                txt
            )
            if m:
                channel = m.group(1).strip()

        if not title:
            title = txt.replace("Watched", "").strip()

        # timestamp
        m = time_regex.search(txt)
        raw_time = m.group(0) if m else None

        rows.append({
            "title": title,
            "channel": channel,
            "url": url,
            "raw_time": raw_time,
            "raw_text": txt
        })

    # fallback if zero rows
    if not rows:
        text = soup.get_text("\n", strip=True)
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if line.startswith("Watched"):
                title = line.replace("Watched", "").strip()
                raw_time = None
                for j in range(i + 1, min(i + 8, len(lines))):
                    if time_regex.search(lines[j]):
                        raw_time = lines[j]
                        break
                rows.append({"title": title, "channel": None, "url": None, "raw_time": raw_time, "raw_text": line})

    return pd.DataFrame(rows)

# =============================
# CLEAN TIME + FEATURES
# =============================
def clean_and_feature(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["raw_time_clean"] = (
        df["raw_time"]
        .astype(str)
        .str.replace("\u202f", " ", regex=False)
        .str.replace("\xa0", " ", regex=False)
        .str.replace(r"\s+[A-Z]{2,4}$", "", regex=True)  # drop timezone suffix
    )

    df["time"] = pd.to_datetime(df["raw_time_clean"], errors="coerce")
    df = df.dropna(subset=["time"])

    df["date"] = df["time"].dt.date
    df["hour"] = df["time"].dt.hour
    df["weekday"] = df["time"].dt.day_name()
    df["month"] = df["time"].dt.to_period("M").astype(str)
    df["is_late_night"] = df["hour"].between(0, 4)
    return df

# =============================
# MUSIC FILTER (removes ads + noise)
# =============================
def music_filter(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()

    # Strong ad/noise removal
    # If title contains "commercial", "ad", "promo", etc. it's likely not music
    ad_like = d["title"].str.contains(
        r"(?:commercial|advert|promotion|promo|sponsored|coupon|deal|sale|order now)",
        case=False, na=False, regex=True
    )

    # Also remove common non-music categories (optional but helps)
    non_music = d["title"].str.contains(
        r"(?:tutorial|review|unboxing|trailer|gameplay|podcast|interview|news)",
        case=False, na=False, regex=True
    )

    # Keep music-ish titles
    music_like = d["title"].str.contains(
        r"(?: - |official|lyrics|audio|mv|m/v|performance|live|vevo)",
        case=False, na=False, regex=True
    )

    # Keep devotional songs too
    devotional = d["title"].str.contains(
        r"(?:stotra|stotram|aarti|bhajan|kirtan|mantra|chalisa)",
        case=False, na=False, regex=True
    )

    keep = (music_like | devotional) & ~(ad_like | non_music)
    return d[keep].copy()

# =============================
# PLOTS
# =============================
def save_plots(music: pd.DataFrame):
    top_channels = music["channel"].fillna("Unknown").value_counts().head(15)

    plt.figure()
    top_channels.sort_values().plot(kind="barh")
    plt.title("Top Artists/Channels (Filtered)")
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "01_top_channels.png"))
    plt.close()

    by_hour = music.groupby("hour").size()
    plt.figure()
    by_hour.plot(kind="bar")
    plt.title("Music Watches by Hour")
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "02_by_hour.png"))
    plt.close()

    daily = music.groupby("date").size()
    plt.figure()
    daily.plot(kind="line")
    plt.title("Music Watches Over Time (Daily)")
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "03_over_time_daily.png"))
    plt.close()

    pivot = music.pivot_table(index="weekday", columns="hour", values="title", aggfunc="count", fill_value=0)
    order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    pivot = pivot.reindex(order)

    plt.figure()
    plt.imshow(pivot.values, aspect="auto")
    plt.xticks(range(len(pivot.columns)), pivot.columns, rotation=90)
    plt.yticks(range(len(pivot.index)), pivot.index)
    plt.title("Weekday x Hour Heatmap (Music Count)")
    plt.colorbar()
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "04_weekday_hour_heatmap.png"))
    plt.close()

# =============================
# MAIN
# =============================
def main():
    print("=== Project A: YouTube Music Taste Audit ===")
    print("Reading:", WATCH_HTML)

    if not os.path.exists(WATCH_HTML):
        print("❌ Can't find watch-history.html at:", WATCH_HTML)
        return

    df = parse_watch_history_html(WATCH_HTML)
    print("Parsed watch rows:", len(df))

    raw_csv = os.path.join(OUT_DIR, "watch_parsed_raw.csv")
    df.to_csv(raw_csv, index=False)
    print("✅ Saved raw parsed CSV:", raw_csv)

    df = clean_and_feature(df)
    print("Rows with valid timestamps:", len(df))

    music = music_filter(df)
    print("Music-ish rows after improved filter:", len(music))

    cleaned_csv = os.path.join(OUT_DIR, "watch_cleaned.csv")
    music_csv = os.path.join(OUT_DIR, "music_only.csv")
    df.to_csv(cleaned_csv, index=False)
    music.to_csv(music_csv, index=False)
    print("✅ Saved cleaned CSV:", cleaned_csv)
    print("✅ Saved music-only CSV:", music_csv)

    print("\n--- Top 10 Channels/Artists ---")
    print(music["channel"].fillna("Unknown").value_counts().head(10).to_string())

    print("\n--- Top 10 Titles ---")
    print(music["title"].value_counts().head(10).to_string())

    print("\n--- Peak Hour ---")
    print(music.groupby("hour").size().sort_values(ascending=False).head(1).to_string())

    save_plots(music)
    print("\n✅ Saved 4 plots into:", OUT_DIR)

    report_path = os.path.join(OUT_DIR, "mini_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("Mini Report (fill after looking at plots)\n")
        f.write("1) My peak music hour is: ______\n")
        f.write("2) My most watched artist/channel is: ______\n")
        f.write("3) I watch most music on (weekday): ______\n")
        f.write("4) Late-night listening is mostly: ______\n")
        f.write("5) Over time, my music watching: increased / decreased around ______\n")
    print("✅ Saved mini report template:", report_path)

if __name__ == "__main__":
    main()