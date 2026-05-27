import streamlit as st
import pandas as pd
from datetime import datetime

# 1. 页面基础配置 (道教古风图标与标题 - 已更名为昊天观)
st.set_page_config(page_title="昊天观·云端财务管理系统", layout="wide", page_icon="☯️")

# --- 2. 注入道教玄门风格自定义 CSS ---
st.markdown("""
    <style>
    /* 全局背景色：宣纸古色 */
    .stApp {
        background-color: #FDF5E6;
        color: #2F2F2F;
    }
    /* 侧边栏样式 */
    [data-testid="stSidebar"] {
        background-color: #F5F5DC;
        border-right: 2px solid #8B4513;
    }
    /* 标题样式：朱砂红 */
    h1, h2, h3 {
        color: #8B0000 !important;
        font-family: 'Kaiti', 'STKaiti', 'serif';
    }
    /* 指标看板样式：古铜金 */
    [data-testid="stMetricValue"] {
        color: #B8860B !important;
    }
    /* 按钮样式：道袍深蓝/朱红 */
    .stButton>button {
        background-color: #8B0000;
        color: white;
        border-radius: 5px;
        border: 1px solid #D2691E;
    }
    .stButton>button:hover {
        background-color: #A52A2A;
        border: 1px solid #FFD700;
    }
    /* 警告与成功信息样式 */
    .stAlert {
        background-color: #FFF8DC;
        border: 1px solid #D2691E;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. 模拟内置账号数据库 (分级管理)
USER_DB = {
    "volunteer": {"password": "ht123", "role": "volunteer", "name": "值班居士"},
    "finance": {"password": "ht456", "role": "finance", "name": "财务会计/出纳"},
    "temple_head": {"password": "ht789", "role": "temple_head", "name": "监院/住持"}
}

# 4. 初始化 Session State
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_role = None
    st.session_state.user_name = None

if 'ledger' not in st.session_state:
    st.session_state.ledger = pd.DataFrame(columns=['日期', '类型', '科目分类', '金额', '经手人/功德主', '票据凭证', '操作员', '备注'])

# --- 5. 登录界面 (太极引导) ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>☯️ 昊天观 · 云端财务管理系统</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #555;'>清净财务 · 法财相须 · 合规管理</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("""
            <div style='background-color: #FFF8DC; padding: 20px; border-radius: 15px; border: 2px solid #8B4513;'>
                <h3 style='text-align: center;'>用户验明正身</h3>
            </div>
        """, unsafe_allow_html=True)
        username = st.text_input("账号", placeholder="volunteer / finance / temple_head")
        password = st.text_input("密码", type="password")
        
        if st.button("进入系统", use_container_width=True):
            if username in USER_DB and USER_DB[username]["password"] == password:
                st.session_state.logged_in = True
                st.session_state.user_role = USER_DB[username]["role"]
                st.session_state.user_name = USER_DB[username]["name"]
                st.rerun()
            else:
                st.error("❗ 账号或密码有误，请重新输入。")
    st.stop()

# --- 6. 进入正式系统 ---

# 侧边栏：用户信息与登出
st.sidebar.markdown(f"### 🕯️ 欢迎：{st.session_state.user_name}")
st.sidebar.markdown(f"当前职司：`{st.session_state.user_role}`")
if st.sidebar.button("登出系统"):
    st.session_state.logged_in = False
    st.rerun()

st.markdown(f"## 📜 昊天观 · 财务管理系统")
st.markdown("---")

# 数据提取
df = st.session_state.ledger

# ==========================================
# 权限层级 A：负责人视图 (负责人/住持/监院专属看板)
# ==========================================
if st.session_state.user_role == "temple_head":
    st.markdown("### 🏛️ 法财具足 · 宏观看板")
    if not df.empty:
        total_income = df[df['类型'] == '收入']['金额'].sum()
        total_expense = df[df['类型'] == '支出']['金额'].sum()
        balance = total_income - total_expense
    else:
        total_income, total_expense, balance = 0.0, 0.0, 0.0

    m1, m2, m3 = st.columns(3)
    m1.metric("累计功德(总收入)", f"￥{total_income:,.2f}")
    m2.metric("清净支用(总支出)", f"￥{total_expense:,.2f}")
    m3.metric("当前余利(结余)", f"￥{balance:,.2f}")
    st.markdown("---")

# ==========================================
# 权限层级 B：所有角色共用：登记录入区
# ==========================================
st.sidebar.markdown("### 📝 账目录入")
entry_type = st.sidebar.radio("账目性质", ["收入", "支出"])

# 符合法规的道教宫观场所标准科目
income_cats = ["捐赠收入(功德款)", "宗教活动收入(法会/斋醮)", "生产经营收入(香烛/文创)", "其他收入"]
expense_cats = ["日常开支(水电维修)", "宗教活动支出", "修缮工程支出", "人员单费/劳务", "其他支出"]
categories = income_cats if entry_type == "收入" else expense_cats

date = st.sidebar.date_input("日期", datetime.now())
category = st.sidebar.selectbox("科目", categories)
amount = st.sidebar.number_input("金额 (元)", min_value=0.0, format="%.2f")
person = st.sidebar.text_input("经手人/功德主", placeholder="默认随喜")

# 票据上传功能
st.sidebar.markdown("### 📸 票据凭证上传")
uploaded_file = st.sidebar.file_uploader("拍摄或上传收据/发票凭证", type=["jpg", "png", "pdf"])

notes = st.sidebar.text_area("备注/资金详细用途")

if st.sidebar.button("提交存档", type="primary"):
    if amount <= 0:
        st.sidebar.error("金额无效")
    elif entry_type == "支出" and uploaded_file is None:
        st.sidebar.warning("⚠️ 依规：宫观所有开支需附原始凭证/发票图片。")
    else:
        receipt_status = f"✅ 已存 ({uploaded_file.name})" if uploaded_file else "❌ 无票据"
        new_row = {
            '日期': date.strftime('%Y-%m-%d'),
            '类型': entry_type,
            '科目分类': category,
            '金额': amount,
            '经手人/功德主': person if person else "随喜",
            '票据凭证': receipt_status,
            '操作员': st.session_state.user_name,
            '备注': notes
        }
        st.session_state.ledger = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        st.sidebar.success("存档成功！")
        st.rerun()

# ==========================================
# 权限层级 C: 明细查看权限隔离
# ==========================================

if st.session_state.user_role == "volunteer":
    st.info("💡 **居士提示**：您目前的权限为‘值班登记’。为了观内财务清静与安全，录入明细由财务及负责人复核，您当前不可查看历史总表。")

else:
    st.markdown("### 📒 财务明细审计表 (复核视图)")
    if df.empty:
        st.write("暂无记录。")
    else:
        # 显示数据表
        st.dataframe(df, use_container_width=True)
        
        # 会计特有功能：导出
        if st.session_state.user_role == "finance":
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 导出财务月报 (CSV)", data=csv, file_name="昊天观财务明细.csv", mime="text/csv")

    # 负责人特有功能：图表分析
    if st.session_state.user_role == "temple_head" and not df.empty:
        st.markdown("---")
        st.markdown("### 📊 财务结构分析")
        chart_data = df.groupby('科目分类')['金额'].sum().reset_index()
        st.bar_chart(data=chart_data, x='科目分类', y='金额')
