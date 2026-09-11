import json
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from crew_pipeline import answer_question, plan_courses


load_dotenv()

st.set_page_config(
    page_title="NUScope Course Advisor",
    page_icon="🎓",
    layout="wide",
)


COURSE_FILE = Path(__file__).parent / "data" / "courses.json"


def load_courses() -> list[dict]:
    return json.loads(COURSE_FILE.read_text(encoding="utf-8"))


st.title("🎓 NUScope Course Advisor")
st.caption("基于 CrewAI 的 NUS 课程咨询原型")

courses = load_courses()
overview_tab, chat_tab, plan_tab = st.tabs(["📚 课程目录", "💬 AI 咨询", "🗺️ 学习规划"])

with overview_tab:
    st.subheader("NUS School of Computing 课程目录")
    st.write(f"当前数据包含 **{len(courses)}** 门课程。")

    prefixes = sorted({course["code"][:2] for course in courses})
    filter_col, search_col = st.columns([1, 2])
    with filter_col:
        selected_prefix = st.selectbox("学院方向", ["全部"] + prefixes)
    with search_col:
        catalog_query = st.text_input("搜索课程", placeholder="课程编号或名称，例如 CS3244")

    filtered_courses = courses
    if selected_prefix != "全部":
        filtered_courses = [
            course for course in filtered_courses
            if course["code"].startswith(selected_prefix)
        ]
    if catalog_query.strip():
        query = catalog_query.strip().lower()
        filtered_courses = [
            course for course in filtered_courses
            if query in f"{course['code']} {course['name']}".lower()
        ]

    st.write(f"找到 **{len(filtered_courses)}** 门课程")
    if filtered_courses:
        selected_code = st.selectbox(
            "选择课程查看详情",
            [course["code"] for course in filtered_courses],
        )
        selected_course = next(
            course for course in filtered_courses if course["code"] == selected_code
        )
        detail_col, source_col = st.columns([2, 1])
        with detail_col:
            st.markdown(f"### {selected_course['code']} · {selected_course['name']}")
            st.write(selected_course.get("description") or "暂无课程描述")
            st.write(f"**方向：** {', '.join(selected_course.get('directions', [])) or '暂无数据'}")
            st.write(f"**先修要求：** {', '.join(selected_course.get('prerequisites', [])) or '暂无数据'}")
            st.write(f"**学分：** {selected_course.get('credits') or '暂无数据'}")
        with source_col:
            st.markdown("#### 数据来源")
            st.write(f"更新时间：{selected_course.get('updated_at', '未知')}")
            if selected_course.get("source_url"):
                st.link_button("打开官方来源", selected_course["source_url"])
    else:
        st.info("没有找到匹配课程。")

with chat_tab:
    st.subheader("AI 课程咨询")
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
                    answer = answer_question(question, courses)
                except Exception as exc:
                    st.error(f"运行失败：{exc}")
                    st.stop()
            st.markdown(answer)
            st.session_state.messages.append(
                {"role": "assistant", "content": answer}
            )

with plan_tab:
    st.subheader("生成课程学习规划")
    st.caption("规划仅基于当前已同步的课程目录，最终选课请以 NUS 官方要求为准。")
    goal = st.text_input("目标方向", placeholder="例如：Artificial Intelligence")
    completed = st.text_input("已修课程", placeholder="例如：CS2030S, CS2040S")
    course_count = st.slider("希望推荐的课程数量", min_value=1, max_value=6, value=3)

    if st.button("生成学习规划", type="primary"):
        if not goal.strip():
            st.warning("请先填写目标方向。")
        else:
            with st.spinner("正在生成并审核学习规划..."):
                try:
                    plan = plan_courses(goal, completed, course_count, courses)
                    st.markdown(plan)
                except Exception as exc:
                    st.error(f"运行失败：{exc}")
