import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px

# --- 页面设置 (可爱风配色) ---
st.set_page_config(page_title="宝宝喂养日记", page_icon="🍼")
st.markdown("""
    <style>
    .main { background-color: #FFF9E3; } /* 奶黄色背景 */
    .stButton>button { border-radius: 20px; background-color: #FFD1DC; border: none; }
    h1 { color: #FF8E99; font-family: 'Comic Sans MS'; }
    </style>
    """, unsafe_allow_html=True)

st.title("🍼 宝宝成长日记")

# --- 模拟数据库 (实际建议存入 SQLite 或 CSV) ---
if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["时间", "类型", "奶量(ml)"])

# --- 记录模块 ---
with st.container():
    st.subheader("✨ 新增记录")
    col1, col2, col3 = st.columns(3)
    with col1:
        feed_type = st.selectbox("类型", ["配方奶", "母乳", "辅食"])
    with col2:
        amount = st.number_input("奶量 (ml)", min_value=0, step=10)
    with col3:
        time_now = st.time_input("时间", datetime.now().time())

    if st.button("记录一下"):
        new_data = pd.DataFrame({"时间": [datetime.now().strftime("%m-%d %H:%M")],
                                 "类型": [feed_type], "奶量(ml)": [amount]})
        st.session_state.data = pd.concat([st.session_state.data, new_data], ignore_index=True)
        st.balloons()  # 成功后撒花


# --- 统计模块 ---
st.subheader("📊 喂养统计")
if not st.session_state.data.empty:
    # 绘制可爱的柱状图
    fig = px.bar(st.session_state.data, x="时间", y="奶量(ml)",
                 color_discrete_sequence=['#FFB7C5'], title="奶量趋势")
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(st.session_state.data.tail(5))  # 显示最近5条记录
else:
    st.info("目前还没有记录哦，快去喂宝宝吧~")