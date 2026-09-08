import json
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from crewai import Agent, Crew, Process, Task
from crewai.llm import LLM
from tools.course_search import search_courses


load_dotenv()

st.set_page_config(
    page_title="NUScope Course Advisor",
    page_icon="🎓",
    layout="centered",
)


@st.cache_resource
def build_advisor():
    required = ["SOCLAAS_MODEL", "SOCLAAS_API_KEY", "SOCLAAS_BASE_URL"]
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise RuntimeError(f"缺少环境变量：{', '.join(missing)}")

    llm = LLM(
        model=f"openai/{os.getenv('SOCLAAS_MODEL')}",
        api_key=os.getenv("SOCLAAS_API_KEY"),
        base_url=os.getenv("SOCLAAS_BASE_URL"),
    )

    return Agent(
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


def answer_question(question: str) -> str:
    course_data = json.loads(
        (Path(__file__).parent / "data" / "courses.json").read_text(
            encoding="utf-8"
        )
    )

    task = Task(
        description=f"""
        用户问题：{question}

        请先使用 course_search 工具检索相关课程，再回答用户。
        课程资料补充如下：{json.dumps(course_data, ensure_ascii=False)}

        要求：
        1. 必须先检索课程。
        2. 只能使用工具返回的数据。
        3. 不得编造课程信息。
        4. 返回课程编号、名称、相关方向和先修要求。
        5. 如果没有匹配结果，明确说明没有找到相关课程。
        6. 使用中文回答。
        """,
        expected_output="一份基于检索结果的中文课程建议。",
        agent=build_advisor(),
    )

    crew = Crew(
        agents=[build_advisor()],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
    )
    return str(crew.kickoff())


st.title("🎓 NUScope Course Advisor")
st.caption("基于 CrewAI 的 NUS 课程咨询原型")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

question = st.chat_input("例如：我想学习人工智能，应该关注哪些课程？")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("正在检索课程并生成建议..."):
            try:
                answer = answer_question(question)
            except Exception as exc:
                st.error(f"运行失败：{exc}")
                st.stop()
        st.markdown(answer)
        st.session_state.messages.append(
            {"role": "assistant", "content": answer}
        )
