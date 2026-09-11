from crew_pipeline import validate_plan_output


def test_validate_plan_output_blocks_unknown_course_codes():
    result = validate_plan_output(
        "推荐 CS3244 和 CS5227。",
        [{"code": "CS3244"}],
    )

    assert "CS5227" in result
    assert "未通过课程数据校验" in result


def test_validate_plan_output_accepts_known_course_codes():
    result = validate_plan_output(
        "推荐 CS3244。",
        [{"code": "CS3244"}],
    )

    assert result == "推荐 CS3244。"
