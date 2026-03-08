#!/usr/bin/env python3
"""
fetch_books.py
Reads your Apple Books library using py-apple-books and writes
an HTML snippet to books_output.md for injection into your README.
"""

from py_apple_books import PyAppleBooks
from datetime import datetime

MAX_CURRENTLY_READING = 5
MAX_FINISHED          = 5
OUTPUT_FILE           = "books_output.md"
PROGRESS_BAR_LEN      = 10


def progress_bar_html(pct_raw: float) -> str:
    """Return an HTML progress bar given a 0-100 float."""
    pct = pct_raw / 100
    filled = round(pct * PROGRESS_BAR_LEN)
    bar = "█" * filled + "░" * (PROGRESS_BAR_LEN - filled)
    return f'<code>{bar}</code> {round(pct_raw)}%'


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

    currently_reading.sort(
        key=lambda b: getattr(b, "reading_progress", 0) or 0,
        reverse=True,
    )

    total_finished = len(finished)
    total_reading  = len(currently_reading)
    total_books    = len(books)
    updated_at     = datetime.now().strftime("%B %d, %Y")

    lines = []

    # ── Stats ─────────────────────────────────────────────────────────────────
    lines.append(
        f'<sub><b>{total_finished}</b> finished &nbsp;·&nbsp; '
        f'<b>{total_reading}</b> in progress &nbsp;·&nbsp; '
        f'<b>{total_books}</b> total in library &nbsp;·&nbsp; '
        f'Last updated: {updated_at}</sub>'
    )
    lines.append("")

    # ── Currently Reading ─────────────────────────────────────────────────────
    lines.append("<h4>📖 Currently Reading</h4>")
    if currently_reading:
        lines.append("<table>")
        lines.append("<tr><th>Book</th><th>Author</th><th>Progress</th></tr>")
        for book in currently_reading[:MAX_CURRENTLY_READING]:
            progress = getattr(book, "reading_progress", 0) or 0.0
            bar      = progress_bar_html(progress)
            title    = (book.title  or "Unknown").replace("<", "&lt;").replace(">", "&gt;")
            author   = (book.author or "Unknown").replace("<", "&lt;").replace(">", "&gt;")
            lines.append(f"<tr><td><b>{title}</b></td><td>{author}</td><td>{bar}</td></tr>")
        lines.append("</table>")
    else:
        lines.append("<p><em>Nothing in progress right now.</em></p>")

    lines.append("")

    # ── Finished ──────────────────────────────────────────────────────────────
    lines.append("<h4>✅ Recently Finished</h4>")
    if finished:
        lines.append("<table>")
        lines.append("<tr><th>Book</th><th>Author</th></tr>")
        for book in finished[:MAX_FINISHED]:
            title  = (book.title  or "Unknown").replace("<", "&lt;").replace(">", "&gt;")
            author = (book.author or "Unknown").replace("<", "&lt;").replace(">", "&gt;")
            lines.append(f"<tr><td><b>{title}</b></td><td>{author}</td></tr>")
        lines.append("</table>")
    else:
        lines.append("<p><em>No finished books yet.</em></p>")

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
