from pathlib import Path
from dotenv import load_dotenv
from crewai import Agent, Crew, Process, Task
from crewai.llm import LLM
import os 

load_dotenv()

llm = LLM(
    model=f"openai/{os.getenv('MODEL_NAME')}",
    api_key=os.getenv("MODEL_API_KEY"),
    base_url=os.getenv("MODEL_BASE_URL"),
)

course_data = Path("data/courses.txt").read_text(encoding="utf-8")

course_advisor = Agent(
    role="NUS Course Advisor",
    goal="Answer questions about NUS courses using only the provided course data",
    backstory="You are a careful academic advisor.",
    llm=llm,
    verbose=True,
)

question = "我想学习人工智能，应该关注哪些课程？请说明理由。"

task = Task(
    description=f"""
    请根据下面的课程资料回答用户问题：

    用户问题：
    {question}

    课程资料：
    {course_data}

    要求：
1. 只能使用提供的课程资料。
2. 不得声称“没有提供课程资料”。
3. 资料中没有答案时，明确说“提供的资料中没有相关信息”。
4. 列出相关课程编号和名称。
5. 解释课程为什么适合人工智能方向。
6. 列出课程的先修要求。
    """,
    expected_output="一份清晰的课程推荐说明。",
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