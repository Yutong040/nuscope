"""Multi-agent course consultation pipeline."""

from __future__ import annotations

import json
import os
import re

from crewai import Agent, Crew, Process, Task
from crewai.llm import LLM

from tools.course_search import search_courses


COURSE_CODE_PATTERN = re.compile(r"\b([A-Z]{2,4}\s*\d{4}[A-Z]?)\b", re.I)


def build_llm() -> LLM:
    return LLM(
        model=f"openai/{os.getenv('SOCLAAS_MODEL')}",
        api_key=os.getenv("SOCLAAS_API_KEY"),
        base_url=os.getenv("SOCLAAS_BASE_URL"),
    )


def validate_plan_output(output: str, courses: list[dict]) -> str:
    """Prevent the UI from displaying course codes absent from the catalog."""
    known_codes = {course["code"].upper() for course in courses}
    mentioned_codes = {
        match.replace(" ", "").upper()
        for match in COURSE_CODE_PATTERN.findall(output)
    }
    unknown_codes = sorted(mentioned_codes - known_codes)
    if unknown_codes:
        return (
            "规划结果未通过课程数据校验，已拦截输出。\n\n"
            f"模型提到了目录中不存在的课程：{', '.join(unknown_codes)}。\n"
            "请减少推荐数量或重新生成。"
        )
    return output


def answer_question(question: str, courses: list[dict]) -> str:
    llm = build_llm()
    researcher = Agent(
        role="NUS Course Researcher",
        goal="Find relevant courses using the course search tool",
        backstory="You retrieve only courses supported by the course database.",
        llm=llm,
        tools=[search_courses],
        verbose=False,
    )
    planner = Agent(
        role="NUS Course Planner",
        goal="Turn retrieved course information into a useful recommendation",
        backstory="You create cautious recommendations and never invent missing fields.",
        llm=llm,
        verbose=False,
    )
    verifier = Agent(
        role="Course Answer Reviewer",
        goal="Check that the final answer is supported by the available course data",
        backstory="You remove unsupported claims and clearly label missing information.",
        llm=llm,
        verbose=False,
    )

    research_task = Task(
        description=f"""使用 course_search 工具检索与以下问题相关的课程：{question}
        只返回检索到的课程编号、名称和匹配依据。""",
        expected_output="相关课程的结构化检索结果。",
        agent=researcher,
    )
    planning_task = Task(
        description=f"""用户问题：{question}
        根据前一步检索结果制定中文课程建议。
        当前课程数据：{json.dumps(courses, ensure_ascii=False)}
        不要编造方向、先修课、课程描述或其他数据中不存在的信息。""",
        expected_output="一份中文课程建议。",
        agent=planner,
        context=[research_task],
    )
    review_task = Task(
        description="""审核前一步回答：删除没有数据依据的断言；保留课程编号、名称、学分和已有字段；
        对缺失的课程描述、方向或先修要求明确写出“暂无数据”。只输出最终中文答案。""",
        expected_output="经过事实审核的最终中文课程回答。",
        agent=verifier,
        context=[planning_task],
    )

    crew = Crew(
        agents=[researcher, planner, verifier],
        tasks=[research_task, planning_task, review_task],
        process=Process.sequential,
        verbose=False,
    )
    return str(crew.kickoff())


def plan_courses(
    goal: str,
    completed: str,
    course_count: int,
    courses: list[dict],
) -> str:
    """Create a cautious course plan from the locally synced course catalog."""
    llm = build_llm()
    planner = Agent(
        role="NUS Academic Planner",
        goal="Create a practical course plan from the available course catalog",
        backstory="You recommend courses conservatively and never invent prerequisites.",
        llm=llm,
        verbose=False,
    )
    reviewer = Agent(
        role="Academic Plan Reviewer",
        goal="Verify that a course plan is supported by the catalog",
        backstory="You flag missing prerequisites and distinguish facts from suggestions.",
        llm=llm,
        verbose=False,
    )

    planning_task = Task(
        description=f"""
        学生目标方向：{goal}
        已修课程：{completed or '未提供'}
        希望推荐课程数量：{course_count}
        可用课程目录：{json.dumps(courses, ensure_ascii=False)}

        请从目录中选择最多 {course_count} 门相关课程，给出课程编号、名称和推荐理由。
        只能使用目录中的信息；没有先修课数据时必须明确说明，不能推测。
        """,
        expected_output="一份中文课程学习计划。",
        agent=planner,
    )
    review_task = Task(
        description="""
        审核课程计划：确认每门课程都存在于目录中；删除未经数据支持的先修课断言；
        明确区分课程事实与推荐建议；最后给出简洁的中文学习计划。""",
        expected_output="经过审核的中文课程学习计划。",
        agent=reviewer,
        context=[planning_task],
    )
    crew = Crew(
        agents=[planner, reviewer],
        tasks=[planning_task, review_task],
        process=Process.sequential,
        verbose=False,
    )
    return validate_plan_output(str(crew.kickoff()), courses)
