import streamlit as st
import pandas as pd
from datetime import datetime
import os
import plotly.express as px

# --- 页面设置 ---
st.set_page_config(page_title="宝宝喂养日记", page_icon="🍼", layout="wide")

# 可爱风 CSS 优化
st.markdown("""
    <style>
    .main { background-color: #FFF9E3; }
    .stMetric { background-color: #FFFFFF; padding: 15px; border-radius: 15px; border: 1px solid #FFD1DC; }
    .stCheckbox { background-color: #FFFFFF; padding: 10px; border-radius: 10px; border: 1px solid #FFD1DC; }
    h1 { color: #FF8E99; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 顶部日期显示 ---
today_date = datetime.now().strftime("%Y年%m月%d日")
st.title(f"🍼 伊姐成长日记")
st.subheader(f"📅 今天是：{today_date}")

# --- 2. 数据加载逻辑 ---
DATA_FILE = "baby_data.csv"
CHECK_FILE = "daily_check.csv"


def load_data(file, columns):
    if os.path.exists(file):
        df = pd.read_csv(file)
        # 确保时间列是字符串，方便过滤
        return df
    return pd.DataFrame(columns=columns)


if 'data' not in st.session_state:
    st.session_state.data = load_data(DATA_FILE, ["时间", "类型", "内容"])
if 'checks' not in st.session_state:
    st.session_state.checks = load_data(CHECK_FILE, ["日期", "项目"])

# --- 3. 每日补剂提醒 (AD/D3) ---
today_str = datetime.now().strftime("%Y-%m-%d")
st.markdown("### ✨ 今日补剂提醒")
today_checks = st.session_state.checks[st.session_state.checks['日期'] == today_str]['项目'].tolist()

col_ad, col_d3, col_btn = st.columns([1, 1, 1])
with col_ad:
    ad_checked = st.checkbox("💊 维生素 AD", value=("AD" in today_checks))
with col_d3:
    d3_checked = st.checkbox("🌞 维生素 D3", value=("D3" in today_checks))
with col_btn:
    if st.button("保存打卡状态"):
        new_checks = st.session_state.checks[st.session_state.checks['日期'] != today_str]
        if ad_checked: new_checks = pd.concat([new_checks, pd.DataFrame([{"日期": today_str, "项目": "AD"}])])
        if d3_checked: new_checks = pd.concat([new_checks, pd.DataFrame([{"日期": today_str, "项目": "D3"}])])
        st.session_state.checks = new_checks
        st.session_state.checks.to_csv(CHECK_FILE, index=False)
        st.success("打卡成功！")

st.divider()

# --- 4. 今日喂养统计 (当日汇总) ---
st.markdown("### 📊 今日喂养统计")

# 过滤出今天的记录 (假设时间格式为 "MM-DD HH:MM")
current_month_day = datetime.now().strftime("%m-%d")
today_df = st.session_state.data[st.session_state.data['时间'].str.startswith(current_month_day)]

if not today_df.empty:
    total_ml = today_df[today_df['类型'] != '辅食']['内容'].sum()
    total_count = len(today_df)

    m1, m2 = st.columns(2)
    m1.metric("🍼 今日总奶量", f"{total_ml} ml")
    m2.metric("🔢 喂养总次数", f"{total_count} 次")

    # 按类型汇总的简单图表
    fig = px.pie(today_df, values='内容', names='类型', color_discrete_sequence=px.colors.qualitative.Pastel)
    fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=200)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("今天还没有喂养记录哦~")

st.divider()

# --- 5. 新增记录区 ---
st.markdown("### 📝 新增记录")
with st.container():
    col1, col2, col3 = st.columns(3)
    with col1:
        feed_type = st.selectbox("类型", ["配方奶", "母乳", "辅食"])
    with col2:
        amount = st.number_input("奶量/内容 (ml/g)", min_value=0, step=10, value=100)
    with col3:
        # 提供一个默认当前时间，也可以手动选
        time_input = st.time_input("记录时间", datetime.now().time())

    if st.button("点我保存记录"):
        # 拼接日期和选择的时间
        final_time_str = f"{current_month_day} {time_input.strftime('%H:%M')}"
        new_entry = pd.DataFrame([{"时间": final_time_str, "类型": feed_type, "内容": amount}])

        st.session_state.data = pd.concat([st.session_state.data, new_entry], ignore_index=True)
        st.session_state.data.to_csv(DATA_FILE, index=False)
        st.balloons()
        st.rerun()  # 立即刷新看到统计变化

# --- 6. 最近记录明细 ---
with st.expander("📜 查看历史明细"):
    st.dataframe(st.session_state.data.sort_index(ascending=False), use_container_width=True)
