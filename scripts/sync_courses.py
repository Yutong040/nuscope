"""Fetch a small, safe subset of NUS SoC course data."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup


DEFAULT_URL = "https://www.comp.nus.edu.sg/cug/soc-sched/"
DEFAULT_CODES = {"CS2030S", "CS3243", "CS3244"}
OUTPUT_FILE = Path(__file__).parents[1] / "data" / "courses.json"
CODE_PATTERN = re.compile(r"\b([A-Z]{2,4})\s*([0-9]{4}[A-Z]?)\b", re.I)


def clean(value: str) -> str:
    return " ".join(value.split())


def normalize_code(value: str) -> str | None:
    match = CODE_PATTERN.search(value)
    if not match:
        return None
    return f"{match.group(1).upper()}{match.group(2).upper()}"


def header_kind(value: str) -> str:
    value = clean(value).lower()
    if "code" in value or "module" in value:
        return "code"
    if "title" in value or "course name" in value or value == "name":
        return "name"
    if "description" in value or "brief" in value:
        return "description"
    if "prerequisite" in value or "pre-requisite" in value:
        return "prerequisites"
    return "other"


def parse_courses(html: str, wanted_codes: set[str], source_url: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    found: dict[str, dict] = {}
    updated_at = datetime.now(UTC).date().isoformat()

    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if not rows:
            continue

        headers = [clean(cell.get_text(" ", strip=True)) for cell in rows[0].find_all(["th", "td"])]
        kinds = [header_kind(header) for header in headers]

        for row in rows[1:]:
            cells = [clean(cell.get_text(" ", strip=True)) for cell in row.find_all(["th", "td"])]
            if not cells:
                continue

            code = next((normalize_code(cell) for cell in cells), None)
            if code not in wanted_codes:
                continue

            values = dict.fromkeys(("name", "description", "prerequisites"), "")
            for index, cell in enumerate(cells):
                kind = kinds[index] if index < len(kinds) else "other"
                if kind in values and not values[kind]:
                    values[kind] = cell

            # If the page has no recognizable headers, use the cells after code
            # as a conservative fallback instead of inventing course content.
            if not values["name"]:
                code_index = next(i for i, cell in enumerate(cells) if normalize_code(cell) == code)
                remaining = [cell for cell in cells[code_index + 1 :] if cell]
                values["name"] = remaining[0] if remaining else ""
                values["description"] = " ".join(remaining[1:])

            found[code] = {
                "code": code,
                "name": values["name"],
                "description": values["description"],
                "directions": [],
                "prerequisites": [values["prerequisites"]] if values["prerequisites"] else [],
                "source_url": source_url,
                "updated_at": updated_at,
            }

    missing = wanted_codes - found.keys()
    if missing:
        raise RuntimeError(
            "课程页面未找到：" + ", ".join(sorted(missing)) +
            "。页面结构可能已变化，请检查官方页面后再调整解析规则。"
        )

    return [found[code] for code in sorted(wanted_codes)]


def fetch(url: str, timeout: int = 20) -> str:
    response = requests.get(
        url,
        timeout=timeout,
        headers={"User-Agent": "NUScope-course-sync/0.1"},
    )
    response.raise_for_status()
    return response.text


def write_atomically(courses: list[dict]) -> None:
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary_file = OUTPUT_FILE.with_suffix(".json.tmp")
    temporary_file.write_text(
        json.dumps(courses, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary_file.replace(OUTPUT_FILE)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--codes", nargs="+", default=sorted(DEFAULT_CODES))
    args = parser.parse_args()

    wanted_codes = {code.upper().replace(" ", "") for code in args.codes}
    try:
        print(f"Fetching {args.url}")
        courses = parse_courses(fetch(args.url), wanted_codes, args.url)
        write_atomically(courses)
    except (requests.RequestException, OSError, RuntimeError) as exc:
        print(f"Sync failed: {exc}", file=sys.stderr)
        print("Existing data/courses.json was not changed.", file=sys.stderr)
        return 1

    print(f"Fetched {len(courses)} courses: {', '.join(course['code'] for course in courses)}")
    print(f"Updated {OUTPUT_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
