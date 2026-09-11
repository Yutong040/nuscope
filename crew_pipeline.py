"""Multi-agent course consultation pipeline."""

from __future__ import annotations

import json
import os

from crewai import Agent, Crew, Process, Task
from crewai.llm import LLM

from tools.course_search import search_courses


def build_llm() -> LLM:
    return LLM(
        model=f"openai/{os.getenv('SOCLAAS_MODEL')}",
        api_key=os.getenv("SOCLAAS_API_KEY"),
        base_url=os.getenv("SOCLAAS_BASE_URL"),
    )


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
