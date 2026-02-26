import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import requests
import base64

# --- 1. 页面基本配置 ---
st.set_page_config(page_title="宝宝喂养日记", page_icon="🍼", layout="wide")

# 注入 CSS 样式
st.markdown("""
    <style>
    .main { background-color: #FFF9E3; }
    .stMetric { background-color: #FFFFFF; padding: 15px; border-radius: 15px; border: 1px solid #FFD1DC; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    .stCheckbox { background-color: #FFFFFF; padding: 10px; border-radius: 10px; border: 1px solid #FFD1DC; }
    h1, h2, h3 { color: #FF8E99; font-family: 'Microsoft YaHei'; }
    .stButton>button { border-radius: 20px; width: 100%; background-color: #FFD1DC; color: white; border: none; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 获取 Secrets 钥匙 ---
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["REPO_NAME"]
except:
    st.error("⚠️ 请确保在 .streamlit/secrets.toml 中配置了 GITHUB_TOKEN 和 REPO_NAME")
    st.stop()

DATA_FILE = "baby_data.csv"
CHECK_FILE = "daily_check.csv"

# --- 3. 核心函数 ---
def sync_to_github(file_path, msg):
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{file_path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    res = requests.get(url, headers=headers)
    sha = res.json().get("sha") if res.status_code == 200 else None
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            content = base64.b64encode(f.read()).decode("utf-8")
        data = {"message": msg, "content": content}
        if sha: data["sha"] = sha
        requests.put(url, headers=headers, json=data)

def load_data(file, columns):
    if os.path.exists(file):
        df = pd.read_csv(file)
        if not df.empty and '时间' in df.columns:
            curr_year = datetime.now().year
            # 增加 errors='coerce' 防止脏数据导致崩溃
            df['dt_obj'] = pd.to_datetime(df['时间'].apply(lambda x: f"{curr_year}-{x}"), errors='coerce')
        return df
    return pd.DataFrame(columns=columns)

# 初始化 session_state
if 'data' not in st.session_state:
    st.session_state.data = load_data(DATA_FILE, ["时间", "类型", "数值", "单位"])
if 'checks' not in st.session_state:
    st.session_state.checks = load_data(CHECK_FILE, ["日期", "项目"])

# --- 4. 界面展示 ---
st.title("🍼 伊姐成长日记")
st.write(f"📅 今天是：**{datetime.now().strftime('%Y年%m月%d日')}**")

# --- A. 新增记录区 ---
st.subheader("📝 新增记录")
with st.container():
    c1, c2, c3 = st.columns(3)
    f_type = c1.selectbox("喂养方式", ["配方奶", "母乳-奶瓶喂", "母乳-亲喂"])
    if f_type == "母乳-亲喂":
        val = c2.number_input("亲喂时长 (分钟)", min_value=0, step=1, value=20)
        unit = "分钟"
    else:
        val = c2.number_input("喂养奶量 (ml)", min_value=0, step=10, value=100)
        unit = "ml"
    f_time = c3.time_input("记录时间", datetime.now().time())

    if st.button("🚀 提交并同步记录"):
        md = datetime.now().strftime("%m-%d")
        t_str = f"{md} {f_time.strftime('%H:%M')}"
        new_row = pd.DataFrame([{"时间": t_str, "类型": f_type, "数值": val, "单位": unit}])
        st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
        # 存本地
        st.session_state.data[["时间", "类型", "数值", "单位"]].to_csv(DATA_FILE, index=False)
        with st.spinner('正在同步至 GitHub...'):
            sync_to_github(DATA_FILE, f"Add {f_type}")
        st.balloons()
        st.rerun()

st.divider()

# --- B. 历史查阅与打卡区 ---
st.subheader("📊 历史查阅与补剂打卡")
pick_date = st.date_input("查看指定日期", datetime.now())
p_date_str = pick_date.strftime("%Y-%m-%d")
p_md = pick_date.strftime("%m-%d")

# 💊 补剂打卡
st.markdown("##### ✨ 今日补剂打卡")
today_checks = st.session_state.checks[st.session_state.checks['日期'] == p_date_str]['项目'].tolist()
ck1, ck2, ck3 = st.columns([1, 1, 1])
ad_val = ck1.checkbox("维生素 AD", value=("AD" in today_checks), key=f"ad_{p_date_str}")
d3_val = ck2.checkbox("维生素 D3", value=("D3" in today_checks), key=f"d3_{p_date_str}")

if ck3.button("保存打卡状态"):
    others = st.session_state.checks[st.session_state.checks['日期'] != p_date_str]
    new_c = others.copy()
    if ad_val: new_c = pd.concat([new_c, pd.DataFrame([{"日期": p_date_str, "项目": "AD"}])])
    if d3_val: new_c = pd.concat([new_c, pd.DataFrame([{"日期": p_date_str, "项目": "D3"}])])
    st.session_state.checks = new_c
    st.session_state.checks[["日期", "项目"]].to_csv(CHECK_FILE, index=False)
    sync_to_github(CHECK_FILE, f"Check: {p_date_str}")
    st.success(f"{p_date_str} 打卡成功同步！")

# 汇总统计
day_df = st.session_state.data[st.session_state.data['时间'].str.startswith(p_md)]
if not day_df.empty:
    m1, m2, m3 = st.columns(3)
    total_ml = day_df[day_df['单位'] == 'ml']['数值'].sum()
    total_min = day_df[day_df['单位'] == '分钟']['数值'].sum()
    m1.metric("🥤 今日总奶量", f"{int(total_ml)} ml")
    m2.metric("🤱 总亲喂时长", f"{int(total_min)} 分")
    m3.metric("🔢 记录次数", f"{len(day_df)} 次")
    st.dataframe(day_df.iloc[::-1][["时间", "类型", "数值", "单位"]], use_container_width=True)
else:
    st.info(f"{p_md} 暂无记录。")

# --- C. 侧边栏周趋势 ---
with st.sidebar:
    st.header("📈 周趋势 (ml)")
    if not st.session_state.data.empty and 'dt_obj' in st.session_state.data.columns:
        last_7 = datetime.now() - timedelta(days=7)
        # 过滤近7天且是 ml 的数据
        ml_df = st.session_state.data[
            (st.session_state.data['dt_obj'] >= last_7) & (st.session_state.data['单位'] == 'ml')
        ].copy()
        if not ml_df.empty:
            chart_data = ml_df.groupby(ml_df['dt_obj'].dt.date)['数值'].sum()
            st.line_chart(chart_data)
        else:
            st.write("近7天暂无奶量数据")
    else:
        st.write("暂无趋势数据")