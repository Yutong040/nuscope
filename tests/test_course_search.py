import json

from tools import course_search


def test_search_matches_exact_code_and_reports_reason(tmp_path, monkeypatch):
    data_file = tmp_path / "courses.json"
    data_file.write_text(
        json.dumps(
            [
                {
                    "code": "CS3244",
                    "name": "Machine Learning",
                    "description": "Fundamental machine learning algorithms",
                    "directions": [],
                    "prerequisites": [],
                }
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(course_search, "COURSE_FILE", data_file)

    result = json.loads(course_search.search_courses.run("CS3244"))

    assert result[0]["code"] == "CS3244"
    assert "课程编号" in result[0]["match_reason"]


def test_search_supports_common_alias(tmp_path, monkeypatch):
    data_file = tmp_path / "courses.json"
    data_file.write_text(
        json.dumps(
            [
                {
                    "code": "CS3244",
                    "name": "Machine Learning",
                    "description": "",
                    "directions": [],
                    "prerequisites": [],
                }
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(course_search, "COURSE_FILE", data_file)

    result = json.loads(course_search.search_courses.run("机器学习"))

    assert result[0]["code"] == "CS3244"
