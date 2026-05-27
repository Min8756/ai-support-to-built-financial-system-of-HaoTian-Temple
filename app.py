import streamlit as st
import pandas as pd
from datetime import datetime

# 页面基础配置
st.set_page_config(page_title="昊天庙云端财务管理系统", layout="wide", page_icon="🕌")
st.title("🕌 昊天庙·云端财务管理系统")
st.markdown("---")

# 初始化本地测试数据（如果初次运行）
if 'ledger' not in st.session_state:
    st.session_state.ledger = pd.DataFrame(columns=['日期', '类型', '科目分类', '金额', '功德主/经手人', '备注'])

# 1. 核心看板数据计算
df = st.session_state.ledger
if not df.empty:
    total_income = df[df['类型'] == '收入']['金额'].sum()
    total_expense = df[df['类型'] == '支出']['金额'].sum()
else:
    total_income = 0.0
    total_expense = 0.0
balance = total_income - total_expense

# 顶部看板展示
col1, col2, col3 = st.columns(3)
col1.metric("📊 总收入 (元)", f"{total_income:,.2f}")
col2.metric("🔻 总支出 (元)", f"{total_expense:,.2f}")
col3.metric("💰 账面当前结余 (元)", f"{balance:,.2f}")
st.markdown("---")

# 2. 侧边栏录入功能
st.sidebar.header("📥 新增收支登记")
entry_type = st.sidebar.radio("请选择账目类型：", ["收入", "支出"])

# 固定科目定义
income_cats = ["捐赠性收入", "宗教活动收入", "功德箱收入"]
expense_cats = ["场所日常维护", "场所建设与修缮", "教职人员单费与劳务报酬", "工作人员工资性收入"]
categories = income_cats if entry_type == "收入" else expense_cats

# 录入表单
date = st.sidebar.date_input("日期", datetime.now())
category = st.sidebar.selectbox("科目分类", categories)
amount = st.sidebar.number_input("金额 (元)", min_value=0.0, step=100.0, format="%.2f")
person = st.sidebar.text_input("功德主 / 经手人")
notes = st.sidebar.text_area("备注信息")

if st.sidebar.button("确认记账并保存", type="primary"):
    if amount <= 0:
        st.sidebar.error("请输入有效的金额！")
    else:
        new_data = {
            '日期': date.strftime('%Y-%m-%d'),
            '类型': entry_type,
            '科目分类': category,
            '金额': amount,
            '功德主/经手人': person if person else "随喜",
            '备注': notes
        }
        st.session_state.ledger = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
        st.sidebar.success("记账成功！")
        st.rerun()

# 3. 主界面图表与历史明细表格
st.subheader("📋 财务流水明细与分析")

if st.session_state.ledger.empty:
    st.info("💡 当前暂无财务数据，请在左侧边栏登记第一笔收支。")
else:
    # 展示明细表格
    st.dataframe(st.session_state.ledger, use_container_width=True)
    
    # 导出功能
    csv = st.session_state.ledger.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 导出财务流水为 Excel/CSV 文件",
        data=csv,
        file_name=f"昊天庙财务流水_{datetime.now().strftime('%Y%m%d')}.csv",
        mime='text/csv'
    )
    
    # 简单的图表分析
    st.markdown("---")
    st.subheader("📊 收支结构比例分析")
    chart_data = st.session_state.ledger.groupby(['科目分类'])['金额'].sum().reset_index()
    st.bar_chart(data=chart_data, x='科目分类', y='金额', use_container_width=True)
