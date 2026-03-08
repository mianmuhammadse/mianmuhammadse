#!/usr/bin/env python3
"""
fetch_books.py
Reads your Apple Books library using py-apple-books and writes
a markdown snippet to books_output.md for injection into your README.

Requirements:
    pip install py_apple_books

Usage:
    python fetch_books.py
"""

from py_apple_books import PyAppleBooks
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────
MAX_CURRENTLY_READING = 5   # books with progress > 0% and < 100%
MAX_FINISHED          = 5   # recently finished books
OUTPUT_FILE           = "books_output.md"
# ──────────────────────────────────────────────────────────────────────────────

PROGRESS_BAR_LEN = 10  # characters


def progress_bar(pct: float) -> str:
    """Return a simple unicode progress bar for a 0–1 float."""
    filled = round(pct * PROGRESS_BAR_LEN)
    return "█" * filled + "░" * (PROGRESS_BAR_LEN - filled)


def pct_label(pct: float) -> str:
    return f"{round(pct * 100)}%"


def build_section(api: PyAppleBooks) -> str:
    books = list(api.list_books())

    currently_reading = []
    finished          = []

    for book in books:
        progress = getattr(book, "reading_progress", None) or 0.0
        if progress >= 100.0:
            finished.append(book)
        elif progress > 0.0:
            currently_reading.append(book)

    # Sort currently reading by descending progress
    currently_reading.sort(
        key=lambda b: getattr(b, "reading_progress", 0) or 0,
        reverse=True,
    )

    lines = []

    # ── Currently Reading ─────────────────────────────────────────────────────
    lines.append("### 📖 Currently Reading\n")
    if currently_reading:
        lines.append("| Book | Author | Progress |")
        lines.append("|------|--------|----------|")
        for book in currently_reading[:MAX_CURRENTLY_READING]:
            pct   = (getattr(book, "reading_progress", 0) or 0.0) / 100
            bar   = progress_bar(pct)
            label = pct_label(pct)
            title  = (book.title  or "Unknown").replace("|", "\\|")
            author = (book.author or "Unknown").replace("|", "\\|")
            lines.append(f"| **{title}** | {author} | `{bar}` {label} |")
    else:
        lines.append("_Nothing in progress right now._")

    lines.append("")

    # ── Finished ──────────────────────────────────────────────────────────────
    lines.append("### ✅ Recently Finished\n")
    if finished:
        lines.append("| Book | Author |")
        lines.append("|------|--------|")
        for book in finished[:MAX_FINISHED]:
            title  = (book.title  or "Unknown").replace("|", "\\|")
            author = (book.author or "Unknown").replace("|", "\\|")
            lines.append(f"| **{title}** | {author} |")
    else:
        lines.append("_No finished books yet._")

    lines.append("")

    # ── Stats ─────────────────────────────────────────────────────────────────
    total_finished = len(finished)
    total_reading  = len(currently_reading)
    total_books    = len(books)
    updated_at     = datetime.now().strftime("%B %d, %Y")

    lines.append(f"**{total_finished}** finished &nbsp;·&nbsp; "
                 f"**{total_reading}** in progress &nbsp;·&nbsp; "
                 f"**{total_books}** total in library")
    lines.append("")
    lines.append(f"<sub>Last updated: {updated_at}</sub>")

    return "\n".join(lines)


def main():
    api     = PyAppleBooks()
    section = build_section(api)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(section)

    print(f"✅  Written to {OUTPUT_FILE}")
    print("─" * 50)
    print(section)


if __name__ == "__main__":
    main()
