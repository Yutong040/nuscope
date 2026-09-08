import json
from pathlib import Path

from crewai.tools import tool


COURSE_FILE = Path(__file__).parents[1] / "data" / "courses.json"


@tool("course_search")
def search_courses(query: str) -> str:
    """Search NUS courses by code, name, direction, or prerequisite."""
    courses = json.loads(COURSE_FILE.read_text(encoding="utf-8"))
    query = query.lower()

    matched = []

    for course in courses:
        searchable_text = " ".join(
            [
                course["code"],
                course["name"],
                course["description"],
                *course["directions"],
                *course["prerequisites"],
            ]
        ).lower()

        if query in searchable_text:
            matched.append(course)

    if not matched:
        return "没有找到匹配的课程。"

    return json.dumps(matched, ensure_ascii=False, indent=2)