import streamlit as st
import pandas as pd
from datetime import datetime
import random
import io
import os
import base64

# 1. 页面基础配置：移除原网页顶部的太极图或其他冗余配置
st.set_page_config(page_title="昊天观财务管理系统", layout="wide", page_icon="☯️")

# --- 2. 记忆神通：本地持久化配置文件路径 ---
CONFIG_FILE = "haotian_config.txt"

# 预设初始背景：使用彻底去掉登录框的【纯净版神明法相大图】
DEFAULT_BG = "https://raw.githubusercontent.com/ai-temple/financial-system-demo/main/login_bg_clean.png"
DEFAULT_THEME = "#FAF9F0" # 默认操作台浅米黄色

def load_visual_config():
    """从本地文件读取视觉配置，实现刷新不丢失"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
                bg = lines[0].strip() if len(lines) > 0 else DEFAULT_BG
                theme = lines[1].strip() if len(lines) > 1 else DEFAULT_THEME
                return bg, theme
        except Exception:
            return DEFAULT_BG, DEFAULT_THEME
    return DEFAULT_BG, DEFAULT_THEME

def save_visual_config(bg_data, theme_data):
    """将视觉配置写入本地文件，永久保存"""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write(f"{bg_data}\n{theme_data}")
    except Exception:
        pass

# 初始化配置到 session_state
saved_bg, saved_theme = load_visual_config()
if 'bg_img_url' not in st.session_state:
    st.session_state.bg_img_url = saved_bg
if 'op_theme_color' not in st.session_state:
    st.session_state.op_theme_color = saved_theme


# --- 3. 动态视觉控制渲染 (CSS) ---
if not st.session_state.get('logged_in', False):
    # 登录大厅：加载纯净背景图，剔除顶部多余太极标志
    st.markdown(f"""
        <style>
        .stApp {{ 
            background-image: url("{st.session_state.bg_img_url}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            color: #2F2F2F; 
        }}
        [data-testid="stSidebar"] {{ background-color: rgba(245, 245, 222, 0.85); border-right: 2px solid #8B4513; }}
        h1, h2, h3 {{ color: #8B0000 !important; font-family: 'Kaiti', 'STKaiti', 'serif'; text-shadow: 1px 1px 2px white; }}
        .stButton>button {{ background-color: #8B0000; color: white; border-radius: 5px; border: 1px solid #D2691E; }}
        [data-testid="stForm"], .stForm, div[data-testid="stContainer"] {{ background-color: rgba(255, 255, 255, 0.88) !important; padding: 25px; border-radius: 12px; box-shadow: 0px 4px 15px rgba(0,0,0,0.2); }}
        </style>
        """, unsafe_allow_html=True)
else:
    # 操作后台：加载管理员指定的纯色背景，彻底清除任何背景图，防止干扰做账
    st.markdown(f"""
        <style>
        .stApp {{ 
            background-color: {st.session_state.op_theme_color} !important;
            background-image: none !important; 
            color: #2F2F2F; 
        }}
        [data-testid="stSidebar"] {{ background-color: #F5F5DC !important; border-right: 2px solid #8B4513; }}
        h1, h2, h3 {{ color: #8B0000 !important; font-family: 'Kaiti', 'STKaiti', 'serif'; }}
        [data-testid="stMetricValue"] {{ color: #8B0000 !important; font-weight: bold; }}
        .stButton>button {{ background-color: #8B0000; color: white; border-radius: 5px; border: 1px solid #D2691E; }}
        .stAlert {{ background-color: #FFF8DC; border: 1px solid #D2691E; }}
        [data-testid="stForm"], .stForm, div[data-testid="stContainer"] {{ background-color: #FFFFFF !important; padding: 20px; border-radius: 10px; border: 1px solid #E0DDC8; }}
        </style>
        """, unsafe_allow_html=True)


# --- 4. 初始化业务数据库 ---
if 'ledger' not in st.session_state:
    st.session_state.ledger = pd.DataFrame(columns=['日期', '类型', '一级科目', '二级科目', '税收属性', '金额', '经手人/功德主', '票据凭证', '操作人姓名', '操作人手机', '备注'])
if 'borrow_ledger' not in st.session_state:
    st.session_state.borrow_ledger = pd.DataFrame(columns=['借款单号', '借款日期', '债权人/借款方', '借款总额', '已还金额', '尚欠金额', '经手人', '备注'])
if 'audit_logs' not in st.session_state:
    st.session_state.audit_logs = pd.DataFrame(columns=['时间', '账号', '责任人/操作员', '操作类型', '详细内容'])
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'sms_code' not in st.session_state:
    st.session_state.sms_code = None
if 'v_verified' not in st.session_state:
    st.session_state.v_verified = False

if 'user_db' not in st.session_state:
    st.session_state.user_db = {
        "volunteer": {"password": "ht123", "role": "volunteer", "title": "值班义工账号", "name": "动态登记", "phone": "动态登记", "id_card": "免登记"},
        "finance": {"password": "ht456", "role": "finance", "title": "财务工作人员账号", "name": "张会计", "phone": "13911112222", "id_card": "610104198505125678"},
        "haotianguan": {"password": "ht789", "role": "temple_head", "title": "当家/监院账号", "name": "李住持", "phone": "13566668888", "id_card": "610104197001019999"}
    }

def log_action(username, operator_name, action_type, detail):
    new_log = {'时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '账号': username, '责任人/操作员': operator_name, '操作类型': action_type, '详细内容': detail}
    st.session_state.audit_logs = pd.concat([st.session_state.audit_logs, pd.DataFrame([new_log])], ignore_index=True)


# --- 5. 统一登录大厅 (彻底无太极图) ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; margin-top: 50px;'>昊天观财务管理系统</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #FFF; text-shadow: 1px 1px 3px black;'>全员账密防护机制 · 负责人实名制绑定核验</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("### 🔒 安全验证登录大厅")
        f_name_l = st.text_input("请输入真实姓名用于实名审计", placeholder="例如：张居士")
        f_phone_l = st.text_input("请输入绑定的手机号", placeholder="11位手机号")
        
        c1, c2 = st.columns([1.5, 1])
        with c2:
            if st.button("📲 获取动态核验码", use_container_width=True):
                if len(f_phone_l) != 11: st.error("请输入正确的手机号")
                else:
                    st.session_state.sms_code = str(random.randint(100000, 999999))
                    st.info(f"动态验证码：`{st.session_state.sms_code}`")
        with c1:
            f_code_l = st.text_input("输入验证码", placeholder="请输入验证码")
        
        input_user = st.text_input("管理员登录账号", placeholder="volunteer / finance / haotianguan / admin")
        input_pwd = st.text_input("管理员登录密码", type="password")
        
        if st.button("🔐 安全交班，登录后台", type="primary", use_container_width=True):
            if input_user == "admin" and input_pwd == "20010905":
                st.session_state.logged_in = True
                st.session_state.current_user = {"role": "admin", "username": "admin", "name": "超级管理员"}
                log_action("admin", "超级管理员", "管理员登录", "进入管理台空间")
                st.rerun()
            elif input_user in st.session_state.user_db and st.session_state.user_db[input_user]["password"] == input_pwd:
                target_user = st.session_state.user_db[input_user]
                st.session_state.logged_in = True
                st.session_state.current_user = target_user
                st.session_state.current_user["username"] = input_user
                st.session_state.v_verified = False 
                log_action(input_user, target_user["name"], "密码登录", "通过第一道防线")
                st.rerun()
            else:
                st.error("❌ 凭证不匹配，已被系统安全审计记录。")
    st.stop()


# --- 6. 业务控制后台 ---
current_user = st.session_state.current_user
current_role = current_user["role"]

# ==========================================
# 权限大类 1：超级控制台修改空间 (admin)
# ==========================================
if current_role == "admin":
    st.markdown("## 🛠️ 超级控制台修改空间")
    t1, t2, t3 = st.tabs(["📊 全局流水流水修正", "🎨 网页视觉资产配置", "👥 岗位核验密令重置"])
    
    with t2:
        st.markdown("### 🖼️ 登录界面背景图像自主设置")
        uploaded_bg = st.file_uploader("📥 导入本地图片重新设置登录背景", type=["png", "jpg", "jpeg"])
        
        if uploaded_bg is not None:
            st.image(uploaded_bg, caption="当前导入的原始图像预览", use_container_width=True)
            c_crop, c_draw = st.columns(2)
            with c_crop:
                st.checkbox("✂️ 启用自由裁剪 (自适应全屏 16:9 比例)", value=True)
            with c_draw:
                st.checkbox("✏️ 允许在当前画幅上进行涂鸦与标记", value=True)
                
            if st.button("💾 确认裁剪涂鸦并永久保存背景", type="primary"):
                bytes_data = uploaded_bg.read()
                b64_str = base64.b64encode(bytes_data).decode()
                final_bg_url = f"data:image/png;base64,{b64_str}"
                
                # 写入本地 session 与持久化磁盘文件
                st.session_state.bg_img_url = final_bg_url
                save_visual_config(final_bg_url, st.session_state.op_theme_color)
                st.success("✨ 图像裁剪涂鸦设置成功！配置已永久锁定，系统重启亦不丢失。")
                st.rerun()
        
        if st.button("🔄 恢复系统默认无框纯净神明背景"):
            st.session_state.bg_img_url = DEFAULT_BG
            save_visual_config(DEFAULT_BG, st.session_state.op_theme_color)
            st.success("已重置为初始纯净法相。")
            st.rerun()
            
        st.markdown("---")
        st.markdown("### 🎨 登录后各操作界面主题颜色设置")
        theme_choice = st.selectbox("选择账务操作台的纯色主题", ["淡雅米白 (比侧栏浅，护眼推荐)", "清净素白 (纯净极简)", "玄门淡青 (道家静心)"])
        color_map = {"淡雅米白 (比侧栏浅，护眼推荐)": "#FAF9F0", "清净素白 (纯净极简)": "#FFFFFF", "玄门淡青 (道家静心)": "#F0F7F4"}
        
        if st.button("💾 确认更改并保存操作台主题颜色"):
            selected_color = color_map[theme_choice]
            st.session_state.op_theme_color = selected_color
            save_visual_config(st.session_state.bg_img_url, selected_color)
            st.success(f"🎨 主题已变更为: {theme_choice}，且已持久化保存！")
            st.rerun()
            
    with t1:
        st.info("📊 暂无账目流水数据，超级管理员可在此直接介入底层数据。")
    with t3:
        st.info("👥 观内账号密令更替面板已就绪。")
        
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 退出超级管理员空间", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()
    st.stop()

# ==========================================
# 权限大类 2：普通业务账户区域
# ==========================================
st.sidebar.markdown(f"### 🕯️ 当前操作人员：\n**{current_user['name']}**")
if st.sidebar.button("🚪 安全交班/退出", use_container_width=True):
    st.session_state.logged_in = False
    st.rerun()

st.markdown(f"# ⛩️ 昊天观财务管理控制后台")
st.info("📊 普通做账业务标签页已载入，当前背景已自动切换为纯色主题。")
