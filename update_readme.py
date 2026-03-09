#!/usr/bin/env python3
"""
update_readme.py
Injects content between marker comments in README.md.

Default markers:  <!-- BOOKS:START --> / <!-- BOOKS:END -->
Custom markers:   --start / --end flags

Usage:
    python update_readme.py
    python update_readme.py --readme README.md --input reading_chart.svg \
        --start "<!-- CHART:START -->" --end "<!-- CHART:END -->"
"""

import argparse
import re
import sys
from pathlib import Path

DEFAULT_START = "<!-- BOOKS:START -->"
DEFAULT_END   = "<!-- BOOKS:END -->"


def inject(readme_path: Path, input_path: Path, start_marker: str, end_marker: str) -> bool:
    readme_text = readme_path.read_text(encoding="utf-8")
    new_content = input_path.read_text(encoding="utf-8").strip()

    pattern = re.compile(
        rf"({re.escape(start_marker)})(.*?)({re.escape(end_marker)})",
        re.DOTALL,
    )

    if not pattern.search(readme_text):
        print(
            f"❌  Markers not found in README.\n"
            f"   Add the following where you want the section:\n\n"
            f"   {start_marker}\n"
            f"   {end_marker}\n"
        )
        sys.exit(1)

    replacement = f"{start_marker}\n{new_content}\n{end_marker}"
    new_readme, count = pattern.subn(replacement, readme_text)

    if new_readme == readme_text:
        print("ℹ️   README already up-to-date.")
        return False

    readme_path.write_text(new_readme, encoding="utf-8")
    print(f"✅  README updated ({count} section(s) replaced).")
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--readme", default="README.md")
    parser.add_argument("--input",  default="books_output.md")
    parser.add_argument("--start",  default=DEFAULT_START)
    parser.add_argument("--end",    default=DEFAULT_END)
    args = parser.parse_args()

    readme_path = Path(args.readme)
    input_path  = Path(args.input)

    if not readme_path.exists():
        print(f"❌  README not found: {readme_path}")
        sys.exit(1)
    if not input_path.exists():
        print(f"❌  Input not found: {input_path}")
        sys.exit(1)

    inject(readme_path, input_path, args.start, args.end)


if __name__ == "__main__":
    main()
