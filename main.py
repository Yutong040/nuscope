from pathlib import Path
from dotenv import load_dotenv
from crewai import Agent, Crew, Process, Task
from crewai.llm import LLM
import os 
import json
from tools.course_search import search_courses

load_dotenv()

llm = LLM(
    model=f"openai/{os.getenv('SOCLAAS_MODEL')}",
    api_key=os.getenv("SOCLAAS_API_KEY"),
    base_url=os.getenv("SOCLAAS_BASE_URL"),
)

course_data = json.loads(
    Path("data/courses.json").read_text(encoding="utf-8")
)
course_text = json.dumps(course_data, ensure_ascii=False, indent=2)

course_advisor = Agent(
    role="NUS Course Advisor",
    goal="Help students find suitable courses based on reliable course data",
    backstory=(
        "You are an NUS academic advisor. "
        "You must only use the courses returned by the search tool."
    ),
    llm=llm,
    tools=[search_courses],
    verbose=True,
)
question = input("请输入你的课程问题：")

task = Task(
    description=f"""
    用户问题：{question}

    请先使用 course_search 工具检索相关课程，再回答用户。

    要求：
    1. 必须先检索课程。
    2. 只能使用工具返回的数据。
    3. 不得编造课程信息。
    4. 返回课程编号、名称、相关方向和先修要求。
    5. 如果没有匹配结果，明确说明没有找到相关课程。
    6. 使用中文回答。
    """,
    expected_output="一份基于检索结果的中文课程建议。",
    agent=course_advisor,
)

crew = Crew(
    agents=[course_advisor],
    tasks=[task],
    process=Process.sequential,
    verbose=True,
)

result = crew.kickoff()
print("\n===== 最终答案 =====\n")
print(result)