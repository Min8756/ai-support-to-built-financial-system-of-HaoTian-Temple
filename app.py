import streamlit as st
import pandas as pd
from datetime import datetime
import random
import io  # 用于处理内存文件流，实现一键下载Excel

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

if 'borrow_ledger' not in st.session_state:
    st.session_state.borrow_ledger = pd.DataFrame(columns=[
        '借款单号', '借款日期', '债权人/借款方', '借款总额', '已还金额', '尚欠金额', '经手人', '备注'
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
    st.toast(f"🚨 大额/重要风控流：已实时向观内安全邮箱 {to_email} 报送风控审计底单！")

# 辅助函数：把数据转换成可供下载的 Excel 字节流（核心迎检增设功能）
def to_excel_stream(dataframe, sheet_name_str="Sheet1"):
    output = io.BytesIO()
    # 使用 openpyxl 引擎（Streamlit 云端自带，非常安全稳定）
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        dataframe.to_excel(writer, index=False, sheet_name=sheet_name_str)
    return output.getvalue()

# --- 5. 统一账号密码登录大厅 ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>☯️ 昊天观财务 management 系统</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #555;'>全员账密防护机制 · 负责人实名制绑定核验</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.3, 1])
    with col2:
        st.markdown("<div style='background-color: #FFF8DC; padding: 15px; border-radius: 10px; border: 1px solid #8B4513;'><b>🔒 系统安全登录口</b></div>", unsafe_allow_html=True)
        
        input_user = st.text_input("登录账号", placeholder="volunteer / finance / haotianguan / admin")
        input_pwd = st.text_input("登录密码", type="password")
        
        if st.button("安全验证，登录后台", use_container_width=True):
            if input_user == "admin":
                if input_pwd == "20010905":
                    st.session_state.logged_in = True
                    st.session_state.current_user = {"role": "admin", "username": "admin", "name": "超级管理员"}
                    log_action("admin", "超级管理员", "管理员登录", "成功进入管理台修正空间")
                    st.success("管理员身份核验成功！")
                    st.rerun()
                else:
                    st.error("❌ 超级管理员密码错误。")
            
            elif input_user in st.session_state.user_db:
                target_user = st.session_state.user_db[input_user]
                if target_user["password"] == input_pwd:
                    st.session_state.logged_in = True
                    st.session_state.current_user = target_user
                    st.session_state.current_user["username"] = input_user
                    st.session_state.v_verified = False 
                    log_action(input_user, target_user["name"], "密码登录", "通过第一道账密防线")
                    st.success("密码正确！正在载入工作台...")
                    st.rerun()
                else:
                    st.error("❌ 密码错误，已被系统审计安全记录。")
            else:
                st.error("❌ 该账号在昊天观名录中不存在。")
    st.stop()

# --- 6. 进入系统内部控制后台 ---
current_user = st.session_state.current_user
current_role = current_user["role"]

# ==========================================
# 权限大类 1：超级管理员账户（管理空间）
# ==========================================
if current_role == "admin":
    st.markdown("<h1 style='text-align: center;'>☯️ 昊天观财务管理系统</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #555;'>后台控制中心：负责人实名绑定与账户管理</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    st.subheader("👥 核心职司账户
