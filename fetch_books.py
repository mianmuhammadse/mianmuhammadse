#!/usr/bin/env python3
"""
fetch_books.py
Reads your Apple Books library using py-apple-books and writes
an HTML snippet to books_output.md for injection into your README.
"""

from py_apple_books import PyAppleBooks
from datetime import datetime
import urllib.parse
import urllib.request
import json
import os

MAX_CURRENTLY_READING = 5
MAX_FINISHED          = 5
OUTPUT_FILE           = "books_output.md"
PROGRESS_BAR_LEN      = 10
ISBN_CACHE_FILE       = ".isbn_cache.json"


def load_isbn_cache() -> dict:
    if os.path.exists(ISBN_CACHE_FILE):
        with open(ISBN_CACHE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_isbn_cache(cache: dict):
    with open(ISBN_CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)


def fetch_isbn(title: str, author: str, cache: dict) -> str | None:
    """Look up ISBN via Open Library search API, with local cache."""
    key = f"{title}|{author}".lower()
    if key in cache:
        return cache[key]

    try:
        query = urllib.parse.quote(f"{title} {author}")
        url   = f"https://openlibrary.org/search.json?q={query}&fields=isbn&limit=1"
        req   = urllib.request.Request(url, headers={"User-Agent": "github-readme-books/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
        docs = data.get("docs", [])
        if docs and docs[0].get("isbn"):
            isbn = docs[0]["isbn"][0]
            cache[key] = isbn
            save_isbn_cache(cache)
            return isbn
    except Exception:
        pass

    cache[key] = None
    save_isbn_cache(cache)
    return None


def cover_url(isbn: str | None, title: str) -> str:
    if isbn:
        return f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg?default=false"
    # fallback to title if no ISBN found
    query = urllib.parse.quote(title)
    return f"https://covers.openlibrary.org/b/title/{query}-M.jpg?default=false"


def progress_bar_html(pct_raw: float) -> str:
    pct    = pct_raw / 100
    filled = round(pct * PROGRESS_BAR_LEN)
    bar    = "█" * filled + "░" * (PROGRESS_BAR_LEN - filled)
    return f'<code>{bar}</code> {round(pct_raw)}%'


def esc(text: str) -> str:
    return (text or "Unknown").replace("<", "&lt;").replace(">", "&gt;")


def build_section(api: PyAppleBooks) -> str:
    books        = list(api.list_books())
    isbn_cache   = load_isbn_cache()

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
        lines.append("<tr><th></th><th>Book</th><th>Author</th><th>Progress</th></tr>")
        for book in currently_reading[:MAX_CURRENTLY_READING]:
            progress = getattr(book, "reading_progress", 0) or 0.0
            bar      = progress_bar_html(progress)
            title    = esc(book.title)
            author   = esc(book.author)
            isbn     = fetch_isbn(book.title or "", book.author or "", isbn_cache)
            img      = cover_url(isbn, book.title or "")
            cover    = f'<img src="{img}" width="30" height="45" style="border-radius:3px" onerror="this.style.display=\'none\'"/>'
            lines.append(f"<tr><td>{cover}</td><td><b>{title}</b></td><td>{author}</td><td>{bar}</td></tr>")
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
            title  = esc(book.title)
            author = esc(book.author)
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
