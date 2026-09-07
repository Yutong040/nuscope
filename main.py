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

question = input("请输入你的课程问题：")

task = Task(
    description=f"""
    请根据下面的课程资料回答用户问题：

    用户问题：
    {question}

    课程资料：
    {course_data}

    要求：
1. 只能使用提供的课程资料。
    2. 不得编造课程信息。
    3. 资料中没有答案时，请明确说“提供的资料中没有相关信息”。
    4. 给出清晰、简洁的中文回答。
    """,
    expected_output="一份基于课程资料的中文回答。",
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