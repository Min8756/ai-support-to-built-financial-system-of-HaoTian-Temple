import streamlit as st
import pandas as pd
from datetime import datetime
import random

# 1. 页面基础配置：固定浏览器页签标题
st.set_page_config(page_title="昊天观财务管理系统", layout="wide", page_icon="☯️")

# --- 2. 玄门古风及规范化表单 CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #FDF5E6; color: #2F2F2F; }
    [data-testid="stSidebar"] { background-color: #F5F5DC; border-right: 2px solid #8B4513; }
    h1, h2, h3 { color: #8B0000 !important; font-family: 'Kaiti', 'STKaiti', 'serif'; }
    [data-testid="stMetricValue"] { color: #B8860B !important; }
    .stButton>button { background-color: #8B0000; color: white; border-radius: 5px; border: 1px solid #D2691E; }
    .stButton>button:hover { background-color: #A52A2A; border: 1px solid #FFD700; }
    .stAlert { background-color: #FFF8DC; border: 1px solid #D2691E; }
    </style>
    """, unsafe_allow_html=True)

# 3. 初始化全局持久化数据库
if 'ledger' not in st.session_state:
    st.session_state.ledger = pd.DataFrame(columns=[
        '日期', '类型', '一级科目', '二级科目', '税收属性', '金额', '经手人/功德主', '票据凭证', '操作人姓名', '操作人手机', '备注'
    ])

if 'audit_logs' not in st.session_state:
    st.session_state.audit_logs = pd.DataFrame(columns=['时间', '账号', '责任人/操作员', '操作类型', '详细内容'])

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_user = None

if 'sms_code' not in st.session_state:
    st.session_state.sms_code = None
if 'v_verified' not in st.session_state:
    st.session_state.v_verified = False

# --- 4. 账户管理系统（由管理员进行全局绑定和修改的数据库） ---
if 'user_db' not in st.session_state:
    st.session_state.user_db = {
        "volunteer": {
            "password": "ht123", "role": "volunteer", "title": "值班义工账号",
            "name": "动态登记", "phone": "动态登记", "id_card": "免登记"
        },
        "finance": {
            "password": "ht456", "role": "finance", "title": "财务工作人员账号",
            "name": "张会计", "phone": "13911112222", "id_card": "610104198505125678"
        },
        "haotianguan": {
            "password": "ht789", "role": "temple_head", "title": "当家/监院账号",
            "name": "李住持", "phone": "13566668888", "id_card": "610104197001019999"
        }
    }

# 辅助函数：记录审计日志
def log_action(username, operator_name, action_type, detail):
    new_log = {
        '时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        '账号': username,
        '责任人/操作员': operator_name,
        '操作类型': action_type,
        '详细内容': detail
    }
    st.session_state.audit_logs = pd.concat([st.session_state.audit_logs, pd.DataFrame([new_log])], ignore_index=True)

# 辅助函数：大额变动邮件监控提示
def send_alert_email(date_str, amount, event, operator):
    to_email = "rldycym123123@163.com"
    st.toast(f"🚨 大额风控流：已实时向观内安全邮箱 {to_email} 报送风控审计底单！")

# --- 5. 统一账号密码登录大厅 ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>☯️ 昊天观财务管理系统</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #555;'>全员账密防护机制 · 负责人实名制绑定核验</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.3, 1])
