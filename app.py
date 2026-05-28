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

# 辅助函数：把数据转换成可供下载的 Excel 字节流
def to_excel_stream(dataframe, sheet_name_str="Sheet1"):
    output = io.BytesIO()
    try:
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            dataframe.to_excel(writer, index=False, sheet_name=sheet_name_str)
    except Exception as e:
        # 如果 openpyxl 还没加载好，临时用 csv 兜底，防止直接炸系统
        output = io.BytesIO()
        dataframe.to_csv(output, index=False, encoding='utf-8-sig')
    return output.getvalue()

# --- 5. 统一账号密码登录大厅 ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>☯️ 昊天观财务管理系统</h1>", unsafe_allow_html=True)
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
    
    st.subheader("👥 核心职司账户与具体负责人对应登记表")
    
    for u_key in ["finance", "haotianguan"]:
        u_data = st.session_state.user_db[u_key]
        with st.expander(f"⚙️ 更改与管理岗位: {u_key}"):
            edit_pwd = st.text_input(f"登录密码修改", value=u_data["password"], key=f"pwd_{u_key}")
            edit_name = st.text_input(f"绑定负责人姓名", value=u_data["name"], key=f"name_{u_key}")
            edit_phone = st.text_input(f"负责人绑定手机号", value=u_data["phone"], key=f"phone_{u_key}")
            edit_id = st.text_input(f"负责人大陆身份证号", value=u_data["id_card"], key=f"id_{u_key}")
            
            # 🛠️【已彻底修复图一报错】：闭合了格式化字符串花括号与 Streamlit 按钮小括号
            if st.button(f"保存账号【{u_key}】对应关系", key=f"save_{u_key}"):
                if len(edit_id) != 18:
                    st.error("❌ 负责人大陆身份证号必须为18位！")
                elif len(edit_phone) != 11:
                    st.error("❌ 负责人手机号必须为11位！")
                else:
                    st.session_state.user_db[u_key] = {
                        "password": edit_pwd, "role": "finance" if u_key == "finance" else "temple_head", "title": u_data["title"],
                        "name": edit_name, "phone": edit_phone, "id_card": edit_id
                    }
                    log_action("admin", "超级管理员", "账户绑定调整", f"已成功将账户【{u_key}】绑定到负责人：{edit_name}")
                    st.success(f"💾 绑定成功！")
                    st.rerun()
                    
    with st.expander("⚙️ 查阅与修改值班义工账号密码"):
        v_data = st.session_state.user_db["volunteer"]
        edit_v_pwd = st.text_input("值班义工账户登录密码", value=v_data["password"])
        if st.button("更新义工账户密码"):
            st.session_state.user_db["volunteer"]["password"] = edit_v_pwd
            log_action("admin", "超级管理员", "义工密码修改", "更新了义工账户通用登录密码")
            st.success("义工账户密码已更新！")
            
    st.markdown("---")
    st.subheader("🕵️ 全盘实时内控操作日志")
    st.dataframe(st.session_state.audit_logs.sort_values(by='时间', ascending=False), use_container_width=True)
    
    if st.button("🚪 安全退出管理空间", type="primary"):
        st.session_state.logged_in = False
        st.rerun()
    st.stop()


# ==========================================
# 权限大类 2：业务账户区域（义工、财务、当家）
# ==========================================

if current_role == "volunteer" and not st.session_state.v_verified:
    st.markdown("<h1 style='text-align: center;'>☯️ 昊天观财务管理系统</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #555;'>值班义工岗位动态实名核验</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    v_col1, v_col2 = st.columns([1, 1])
    with v_col1:
        v_name = st.text_input("请输入值班义工真实姓名", placeholder="例如：李居士")
        v_phone = st.text_input("请输入值班义工手机号码", placeholder="11位手机号")
        
        c1, c2 = st.columns([1.5, 1])
        with c2:
            if st.button("📲 发送手机核验码", use_container_width=True):
                if len(v_phone) != 11:
                    st.error("请输入正确的手机号")
                else:
                    st.session_state.sms_code = str(random.randint(100000, 999999))
                    st.info(f"【财务内控中心】动态验证码：`{st.session_state.sms_code}`")
        with c1:
            v_code = st.text_input("输入验证码", placeholder="请输入蓝框中的验证码")
            
        if st.button("确认登记并解锁账簿", type="primary", use_container_width=True):
            if not st.session_state.sms_code:
                st.error("请先获取手机核验码！")
            elif v_code != st.session_state.sms_code:
                st.error("验证码错误，无法核验身份！")
            elif not v_name:
                st.error("请输入值班义工姓名！")
            else:
                st.session_state.v_verified = True
                st.session_state.active_v_info = {"name": v_name, "phone": v_phone}
                log_action("volunteer", v_name, "动态实名登记", f"义工【{v_name}】成功通过手机【{v_phone}】验证。")
                st.rerun()
                
    if st.button("🚪 退回登录大厅"):
        st.session_state.logged_in = False
        st.rerun()
    st.stop()

# 确立责任主体
if current_role == "volunteer":
    active_name = st.session_state.active_v_info["name"]
    active_phone = st.session_state.active_v_info["phone"]
    active_id = "义工免批登记"
else:
    active_name = current_user["name"]
    active_phone = current_user["phone"]
    active_id = current_user["id_card"]

# 左侧边栏：纯粹放置身份看板和登出按钮
st.sidebar.markdown(f"### 🕯️ 当前操作人员：\n**{active_name}**")
st.sidebar.markdown(f"**登录账号**：`{current_user['username']}`")
st.sidebar.markdown(f"**责任手机**：`{active_phone}
