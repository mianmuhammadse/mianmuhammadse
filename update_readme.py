#!/usr/bin/env python3
"""
update_readme.py
Injects the contents of books_output.md into README.md between these markers:

    <!-- BOOKS:START -->
    <!-- BOOKS:END -->

Usage:
    python update_readme.py
    python update_readme.py --readme path/to/README.md --input books_output.md
"""

import argparse
import re
import sys
from pathlib import Path

START_MARKER = "<!-- BOOKS:START -->"
END_MARKER   = "<!-- BOOKS:END -->"


def inject(readme_path: Path, input_path: Path) -> bool:
    """
    Replace the content between START_MARKER and END_MARKER in readme_path
    with the content of input_path.

    Returns True if the file was changed, False if it was already up-to-date.
    """
    readme_text = readme_path.read_text(encoding="utf-8")
    new_content = input_path.read_text(encoding="utf-8").strip()

    pattern = re.compile(
        rf"({re.escape(START_MARKER)})(.*?)({re.escape(END_MARKER)})",
        re.DOTALL,
    )

    if not pattern.search(readme_text):
        print(
            "❌  Markers not found in README.\n"
            f"   Add the following to your README where you want the section:\n\n"
            f"   {START_MARKER}\n"
            f"   {END_MARKER}\n"
        )
        sys.exit(1)

    replacement = f"{START_MARKER}\n{new_content}\n{END_MARKER}"
    new_readme, count = pattern.subn(replacement, readme_text)

    if new_readme == readme_text:
        print("ℹ️   README already up-to-date, no changes made.")
        return False

    readme_path.write_text(new_readme, encoding="utf-8")
    print(f"✅  README updated ({count} section(s) replaced).")
    return True


def main():
    parser = argparse.ArgumentParser(description="Inject Apple Books stats into README.md")
    parser.add_argument("--readme", default="README.md",   help="Path to README.md")
    parser.add_argument("--input",  default="books_output.md", help="Path to books_output.md")
    args = parser.parse_args()

    readme_path = Path(args.readme)
    input_path  = Path(args.input)

    if not readme_path.exists():
        print(f"❌  README not found: {readme_path}")
        sys.exit(1)

    if not input_path.exists():
        print(f"❌  Input file not found: {input_path}\n   Run fetch_books.py first.")
        sys.exit(1)

    inject(readme_path, input_path)


if __name__ == "__main__":
    main()
