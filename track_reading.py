#!/usr/bin/env python3
"""
track_reading.py
Logs daily reading progress snapshots and generates:
  - reading_chart.svg  → embeds in README
  - reading_report.html → full interactive dashboard (GitHub Pages)
"""

from py_apple_books import PyAppleBooks
from datetime import datetime, timedelta
import json, os, math

LOG_FILE    = "reading_log.json"
SVG_FILE    = "reading_chart.svg"
HTML_FILE   = "reading_report.html"

# Tokyo Night palette
BG          = "#1a1b26"
BG2         = "#24283b"
BORDER      = "#414868"
TEXT        = "#c0caf5"
TEXT_DIM    = "#565f89"
ACCENT      = "#7aa2f7"
GREEN       = "#9ece6a"
YELLOW      = "#e0af68"
RED         = "#f7768e"
PURPLE      = "#bb9af7"
CYAN        = "#7dcfff"

BOOK_COLORS = [ACCENT, GREEN, YELLOW, PURPLE, CYAN, RED]

TODAY = datetime.now().strftime("%Y-%m-%d")


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_log() -> dict:
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE) as f:
            return json.load(f)
    return {}


def save_log(log: dict):
    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)


def append_today(log: dict, books):
    """Add today's snapshot for all in-progress and finished books."""
    for book in books:
        progress = getattr(book, "reading_progress", None) or 0.0
        if progress <= 0.0:
            continue
        title = book.title or "Unknown"
        if title not in log:
            log[title] = []
        # Avoid duplicate entries for today
        if not any(e["date"] == TODAY for e in log[title]):
            log[title].append({"date": TODAY, "progress": round(progress, 2)})
        else:
            # Update today's entry
            for e in log[title]:
                if e["date"] == TODAY:
                    e["progress"] = round(progress, 2)
    return log


def compute_stats(entries: list) -> dict:
    """Compute pace, streak, predicted finish for a book's entry list."""
    if len(entries) < 2:
        return {"pace": 0, "streak": 0, "eta": None}

    sorted_entries = sorted(entries, key=lambda e: e["date"])

    # Daily pace over last 7 days
    recent = [e for e in sorted_entries
              if e["date"] >= (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")]
    if len(recent) >= 2:
        delta_progress = recent[-1]["progress"] - recent[0]["progress"]
        delta_days     = max(1, (datetime.strptime(recent[-1]["date"], "%Y-%m-%d") -
                                 datetime.strptime(recent[0]["date"], "%Y-%m-%d")).days)
        pace = delta_progress / delta_days  # % per day
    else:
        pace = 0

    # Streak — consecutive days with progress increase
    streak = 0
    prev_progress = None
    prev_date     = None
    for e in reversed(sorted_entries):
        d = datetime.strptime(e["date"], "%Y-%m-%d")
        if prev_date is None:
            prev_date     = d
            prev_progress = e["progress"]
            streak        = 1
            continue
        if (prev_date - d).days == 1 and prev_progress > e["progress"]:
            streak       += 1
            prev_date     = d
            prev_progress = e["progress"]
        else:
            break

    # ETA
    current_progress = sorted_entries[-1]["progress"]
    remaining        = 100 - current_progress
    if pace > 0 and current_progress < 100:
        days_left = math.ceil(remaining / pace)
        eta = (datetime.now() + timedelta(days=days_left)).strftime("%b %d, %Y")
    else:
        eta = None

    return {"pace": round(pace, 2), "streak": streak, "eta": eta}


# ── SVG Generator ─────────────────────────────────────────────────────────────

def generate_svg(log: dict, active_books: list) -> str:
    active_titles = [b.title for b in active_books if b.title in log]
    if not active_titles:
        return _empty_svg()

    W, H        = 800, 300
    PAD_L       = 50
    PAD_R       = 20
    PAD_T       = 40
    PAD_B       = 50
    CHART_W     = W - PAD_L - PAD_R
    CHART_H     = H - PAD_T - PAD_B

    # Collect all dates across active books
    all_dates = sorted(set(
        e["date"]
        for title in active_titles
        for e in log[title]
    ))
    if len(all_dates) < 2:
        all_dates = all_dates * 2  # duplicate to avoid division by zero

    def x_pos(date):
        idx = all_dates.index(date)
        return PAD_L + (idx / max(1, len(all_dates) - 1)) * CHART_W

    def y_pos(pct):
        return PAD_T + CHART_H - (pct / 100) * CHART_H

    lines_svg  = []
    dots_svg   = []
    legend_svg = []

    for i, title in enumerate(active_titles):
        color   = BOOK_COLORS[i % len(BOOK_COLORS)]
        entries = sorted(log[title], key=lambda e: e["date"])
        points  = [(x_pos(e["date"]), y_pos(e["progress"])) for e in entries
                   if e["date"] in all_dates]
        if len(points) < 1:
            continue

        # Line
        d = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in points)
        lines_svg.append(
            f'<path d="{d}" fill="none" stroke="{color}" '
            f'stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round" opacity="0.9"/>'
        )

        # Dots
        for x, y in points:
            dots_svg.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="{color}" stroke="{BG}" stroke-width="1.5"/>'
            )

        # Legend
        lx = PAD_L + (i % 3) * 240
        ly = H - 14
        short = title[:28] + "…" if len(title) > 28 else title
        legend_svg.append(
            f'<rect x="{lx}" y="{ly - 8}" width="10" height="10" rx="2" fill="{color}"/>'
            f'<text x="{lx + 14}" y="{ly}" fill="{TEXT_DIM}" font-size="11" font-family="monospace">{short}</text>'
        )

    # Y-axis labels
    y_labels = ""
    for pct in [0, 25, 50, 75, 100]:
        y = y_pos(pct)
        y_labels += (
            f'<line x1="{PAD_L}" y1="{y:.1f}" x2="{W - PAD_R}" y2="{y:.1f}" '
            f'stroke="{BORDER}" stroke-width="0.5" stroke-dasharray="4,4"/>'
            f'<text x="{PAD_L - 6}" y="{y + 4:.1f}" fill="{TEXT_DIM}" '
            f'font-size="10" font-family="monospace" text-anchor="end">{pct}%</text>'
        )

    # X-axis labels (show up to 6 dates)
    x_labels = ""
    step = max(1, len(all_dates) // 6)
    for idx in range(0, len(all_dates), step):
        date = all_dates[idx]
        x    = x_pos(date)
        short_date = date[5:]  # MM-DD
        x_labels += (
            f'<text x="{x:.1f}" y="{PAD_T + CHART_H + 18}" fill="{TEXT_DIM}" '
            f'font-size="10" font-family="monospace" text-anchor="middle">{short_date}</text>'
        )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <rect width="{W}" height="{H}" rx="12" fill="{BG}"/>
  <rect x="1" y="1" width="{W-2}" height="{H-2}" rx="11" fill="none" stroke="{BORDER}" stroke-width="1"/>
  <text x="{PAD_L}" y="22" fill="{TEXT}" font-size="13" font-family="monospace" font-weight="bold">📖 Reading Progress</text>
  <text x="{W - PAD_R}" y="22" fill="{TEXT_DIM}" font-size="10" font-family="monospace" text-anchor="end">Updated {TODAY}</text>
  {y_labels}
  {x_labels}
  {"".join(lines_svg)}
  {"".join(dots_svg)}
  {"".join(legend_svg)}
</svg>'''

    return svg


def _empty_svg() -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="120" viewBox="0 0 800 120">
  <rect width="800" height="120" rx="12" fill="{BG}"/>
  <text x="400" y="65" fill="{TEXT_DIM}" font-size="14" font-family="monospace" text-anchor="middle">No reading data yet — check back tomorrow 📚</text>
</svg>'''


# ── HTML Report ───────────────────────────────────────────────────────────────

def generate_html(log: dict) -> str:
    books_data = {}
    for title, entries in log.items():
        if not entries:
            continue
        stats = compute_stats(entries)
        sorted_entries = sorted(entries, key=lambda e: e["date"])
        books_data[title] = {
            "entries":  sorted_entries,
            "current":  sorted_entries[-1]["progress"],
            "stats":    stats,
        }

    books_json = json.dumps(books_data)

    cards_html = ""
    for i, (title, data) in enumerate(books_data.items()):
        color   = BOOK_COLORS[i % len(BOOK_COLORS)]
        current = data["current"]
        stats   = data["stats"]
        eta_str = f"ETA: {stats['eta']}" if stats["eta"] else ("Finished! 🎉" if current >= 100 else "Keep reading for ETA")
        streak_str = f"🔥 {stats['streak']} day streak" if stats["streak"] > 1 else "—"
        pace_str   = f"{stats['pace']}% / day" if stats["pace"] > 0 else "—"

        cards_html += f'''
        <div class="book-card" data-color="{color}">
          <div class="book-header">
            <div class="book-color-dot" style="background:{color}"></div>
            <div class="book-title">{title}</div>
          </div>
          <div class="progress-bar-wrap">
            <div class="progress-bar-fill" style="width:{min(current,100):.1f}%;background:{color}"></div>
          </div>
          <div class="book-meta">
            <span class="meta-item">📊 {current:.1f}%</span>
            <span class="meta-item">⚡ {pace_str}</span>
            <span class="meta-item">{streak_str}</span>
            <span class="meta-item">📅 {eta_str}</span>
          </div>
        </div>'''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Reading Tracker</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Sora:wght@300;400;600&display=swap');

  :root {{
    --bg:      {BG};
    --bg2:     {BG2};
    --border:  {BORDER};
    --text:    {TEXT};
    --dim:     {TEXT_DIM};
    --accent:  {ACCENT};
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    background: var(--bg);
    color: var(--text);
    font-family: 'Sora', sans-serif;
    min-height: 100vh;
    padding: 40px 24px;
  }}

  .container {{ max-width: 900px; margin: 0 auto; }}

  header {{
    display: flex;
    align-items: baseline;
    gap: 16px;
    margin-bottom: 40px;
    border-bottom: 1px solid var(--border);
    padding-bottom: 20px;
  }}

  header h1 {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.6rem;
    font-weight: 700;
    letter-spacing: -0.5px;
  }}

  header .updated {{
    font-size: 0.75rem;
    color: var(--dim);
    font-family: 'JetBrains Mono', monospace;
  }}

  .section-title {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--dim);
    margin-bottom: 16px;
  }}

  .cards-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 16px;
    margin-bottom: 40px;
  }}

  .book-card {{
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 18px;
    transition: border-color 0.2s;
  }}

  .book-card:hover {{ border-color: var(--accent); }}

  .book-header {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 14px;
  }}

  .book-color-dot {{
    width: 10px; height: 10px;
    border-radius: 50%;
    flex-shrink: 0;
  }}

  .book-title {{
    font-size: 0.9rem;
    font-weight: 600;
    line-height: 1.3;
  }}

  .progress-bar-wrap {{
    height: 4px;
    background: var(--border);
    border-radius: 4px;
    margin-bottom: 14px;
    overflow: hidden;
  }}

  .progress-bar-fill {{
    height: 100%;
    border-radius: 4px;
    transition: width 0.6s ease;
  }}

  .book-meta {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }}

  .meta-item {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    color: var(--dim);
    background: var(--bg);
    border: 1px solid var(--border);
    padding: 3px 8px;
    border-radius: 4px;
  }}

  .chart-wrap {{
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 24px;
    margin-bottom: 24px;
  }}

  .chart-wrap canvas {{ max-height: 280px; }}

  footer {{
    text-align: center;
    color: var(--dim);
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    margin-top: 40px;
    padding-top: 20px;
    border-top: 1px solid var(--border);
  }}
</style>
</head>
<body>
<div class="container">
  <header>
    <h1>📚 Reading Tracker</h1>
    <span class="updated">updated {TODAY}</span>
  </header>

  <p class="section-title">Books</p>
  <div class="cards-grid">
    {cards_html}
  </div>

  <p class="section-title">Progress Over Time</p>
  <div class="chart-wrap">
    <canvas id="progressChart"></canvas>
  </div>

  <p class="section-title">Daily Reading Pace (7-day)</p>
  <div class="chart-wrap">
    <canvas id="paceChart"></canvas>
  </div>

  <footer>auto-updated daily by github actions · mianmuhammadse</footer>
</div>

<script>
const BOOKS = {books_json};
const COLORS = {json.dumps(BOOK_COLORS)};

const titles = Object.keys(BOOKS);
const allDates = [...new Set(
  titles.flatMap(t => BOOKS[t].entries.map(e => e.date))
)].sort();

// ── Progress Chart ────────────────────────────────────────────────────────────
const progressCtx = document.getElementById('progressChart').getContext('2d');
new Chart(progressCtx, {{
  type: 'line',
  data: {{
    labels: allDates.map(d => d.slice(5)),
    datasets: titles.map((title, i) => {{
      const dateMap = Object.fromEntries(BOOKS[title].entries.map(e => [e.date, e.progress]));
      return {{
        label: title,
        data: allDates.map(d => dateMap[d] ?? null),
        borderColor: COLORS[i % COLORS.length],
        backgroundColor: COLORS[i % COLORS.length] + '18',
        tension: 0.3,
        fill: true,
        spanGaps: true,
        pointRadius: 4,
        pointHoverRadius: 6,
      }};
    }}),
  }},
  options: {{
    responsive: true,
    plugins: {{
      legend: {{ labels: {{ color: '{TEXT}', font: {{ family: 'JetBrains Mono', size: 11 }} }} }},
      tooltip: {{ backgroundColor: '{BG2}', borderColor: '{BORDER}', borderWidth: 1, titleColor: '{TEXT}', bodyColor: '{TEXT_DIM}' }}
    }},
    scales: {{
      x: {{ ticks: {{ color: '{TEXT_DIM}', font: {{ family: 'JetBrains Mono', size: 10 }} }}, grid: {{ color: '{BORDER}40' }} }},
      y: {{ min: 0, max: 100, ticks: {{ color: '{TEXT_DIM}', font: {{ family: 'JetBrains Mono', size: 10 }}, callback: v => v + '%' }}, grid: {{ color: '{BORDER}40' }} }}
    }}
  }}
}});

// ── Pace Chart ────────────────────────────────────────────────────────────────
const paceCtx = document.getElementById('paceChart').getContext('2d');
const last7 = allDates.slice(-8);
new Chart(paceCtx, {{
  type: 'bar',
  data: {{
    labels: last7.slice(1).map(d => d.slice(5)),
    datasets: titles.map((title, i) => {{
      const entries = BOOKS[title].entries.filter(e => last7.includes(e.date));
      const dateMap = Object.fromEntries(entries.map(e => [e.date, e.progress]));
      const paces = last7.slice(1).map((d, idx) => {{
        const today = dateMap[d];
        const prev  = dateMap[last7[idx]];
        return (today != null && prev != null) ? Math.max(0, today - prev) : 0;
      }});
      return {{
        label: title,
        data: paces,
        backgroundColor: COLORS[i % COLORS.length] + 'cc',
        borderRadius: 4,
      }};
    }}),
  }},
  options: {{
    responsive: true,
    plugins: {{
      legend: {{ labels: {{ color: '{TEXT}', font: {{ family: 'JetBrains Mono', size: 11 }} }} }},
      tooltip: {{ backgroundColor: '{BG2}', borderColor: '{BORDER}', borderWidth: 1, titleColor: '{TEXT}', bodyColor: '{TEXT_DIM}', callbacks: {{ label: ctx => ` ${{ctx.dataset.label}}: ${{ctx.parsed.y.toFixed(2)}}%` }} }}
    }},
    scales: {{
      x: {{ ticks: {{ color: '{TEXT_DIM}', font: {{ family: 'JetBrains Mono', size: 10 }} }}, grid: {{ color: '{BORDER}40' }} }},
      y: {{ ticks: {{ color: '{TEXT_DIM}', font: {{ family: 'JetBrains Mono', size: 10 }}, callback: v => v + '%' }}, grid: {{ color: '{BORDER}40' }} }}
    }}
  }}
}});
</script>
</body>
</html>'''


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    api   = PyAppleBooks()
    books = list(api.list_books())

    active = [b for b in books
              if (getattr(b, "reading_progress", None) or 0) > 0]

    log = load_log()
    log = append_today(log, books)
    save_log(log)
    print(f"✅ Log updated → {LOG_FILE}")

    svg = generate_svg(log, active)
    with open(SVG_FILE, "w") as f:
        f.write(svg)
    print(f"✅ SVG generated → {SVG_FILE}")

    html = generate_html(log)
    with open(HTML_FILE, "w") as f:
        f.write(html)
    print(f"✅ HTML report generated → {HTML_FILE}")


if __name__ == "__main__":
    main()
