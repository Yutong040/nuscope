from scripts.sync_courses import parse_courses, validate_courses


def test_parse_courses_extracts_units_and_preserves_existing_fields():
    html = """
    <table>
      <tr><th>Module Code</th><th>Module Title</th><th>Units</th></tr>
      <tr><td>CS3244</td><td>Machine Learning</td><td>Units = 4</td></tr>
    </table>
    """
    courses = parse_courses(
        html,
        {"CS3244"},
        "https://example.com/courses",
        {
            "CS3244": {
                "code": "CS3244",
                "description": "Existing description",
                "directions": ["Artificial Intelligence"],
                "prerequisites": ["Programming"],
            }
        },
    )

    assert courses == [
        {
            "code": "CS3244",
            "name": "Machine Learning",
            "description": "Existing description",
            "directions": ["Artificial Intelligence"],
            "prerequisites": ["Programming"],
            "credits": 4,
            "source_url": "https://example.com/courses",
            "updated_at": courses[0]["updated_at"],
        }
    ]


def test_validate_courses_rejects_missing_name():
    try:
        validate_courses([{"code": "CS3244", "name": ""}], {"CS3244"})
    except RuntimeError as exc:
        assert "缺少课程名称" in str(exc)
    else:
        raise AssertionError("Expected validation to fail")
