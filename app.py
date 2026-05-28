import streamlit as st
import pandas as pd
from datetime import datetime
import random
import io
import os
import base64

# 1. 页面基础配置
st.set_page_config(page_title="昊天观财务管理系统", layout="wide", page_icon="☯️")

# --- 2. 持久化配置文件路径 ---
CONFIG_FILE = "haotian_config.txt"
DEFAULT_BG = "https://raw.githubusercontent.com/ai-temple/financial-system-demo/main/login_bg_clean.png"
DEFAULT_THEME = "#FAF9F0" 

def load_visual_config():
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
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write(f"{bg_data}\n{theme_data}")
    except Exception:
        pass

# 初始化视觉配置
saved_bg, saved_theme = load_visual_config()
if 'bg_img_url' not in st.session_state:
    st.session_state.bg_img_url = saved_bg
if 'op_theme_color' not in st.session_state:
    st.session_state.op_theme_color = saved_theme

# --- 3. 动态 CSS 视觉控制 ---
if not st.session_state.get('logged_in', False):
    # 登录大厅：无太极图，干净清爽
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
    # 操作后台：纯色极简，保护视力，防重叠
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

def to_excel_stream(dataframe):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        dataframe.to_excel(writer, index=False, sheet_name="昊天观账目数据")
    return output.getvalue()

# --- 5. 统一安全验证登录大厅 ---
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
                st.session_state.current_user = target_user.copy()
                st.session_state.current_user["username"] = input_user
                
                # 如果是义工，记录实名输入的姓名和电话
                if input_user == "volunteer":
                    st.session_state.current_user["name"] = f_name_l if f_name_l else "未登记义工"
                    st.session_state.current_user["phone"] = f_phone_l if f_phone_l else "未登记手机"
                
                log_action(input_user, st.session_state.current_user["name"], "实名账密登录", f"核验成功，进入操作台")
                st.rerun()
            else:
                st.error("❌ 凭证不匹配，请重新核验。")
    st.stop()

# --- 6. 成功登录，载入系统内部控制后台 ---
current_user = st.session_state.current_user
current_role = current_user["role"]

# ==========================================
# 权限大类 1：超级控制台修改空间 (admin)
# ==========================================
if current_role == "admin":
    st.markdown("## 🛠️ 超级控制台修改空间")
    t1, t2, t3 = st.tabs(["📊 全局流水修正", "🎨 网页视觉资产配置", "👥 岗位核验密令重置"])
    
    with t2:
        st.markdown("### 🖼️ 登录界面背景图像自主设置")
        uploaded_bg = st.file_uploader("📥 导入本地图片重新设置登录背景", type=["png", "jpg", "jpeg"])
        if uploaded_bg is not None:
            st.image(uploaded_bg, caption="当前导入的原始图像预览", use_container_width=True)
            if st.button("💾 确认裁剪涂鸦并永久保存背景", type="primary"):
                bytes_data = uploaded_bg.read()
                b64_str = base64.b64encode(bytes_data).decode()
                final_bg_url = f"data:image/png;base64,{b64_str}"
                st.session_state.bg_img_url = final_bg_url
                save_visual_config(final_bg_url, st.session_state.op_theme_color)
                st.success("✨ 图像设置成功！")
                st.rerun()
        
        if st.button("🔄 恢复系统默认无框纯净神明背景"):
            st.session_state.bg_img_url = DEFAULT_BG
            save_visual_config(DEFAULT_BG, st.session_state.op_theme_color)
            st.success("已重置。")
            st.rerun()
            
        st.markdown("---")
        st.markdown("### 🎨 登录后各操作界面主题颜色设置")
        theme_choice = st.selectbox("选择账务操作台的纯色主题", ["淡雅米白 (比侧栏浅，护眼推荐)", "清净素白 (纯净极简)", "玄门淡青 (道家静心)"])
        color_map = {"淡雅米白 (比侧栏浅，护眼推荐)": "#FAF9F0", "清净素白 (纯净极简)": "#FFFFFF", "玄门淡青 (道家静心)": "#F0F7F4"}
        if st.button("💾 确认更改并保存操作台主题颜色"):
            selected_color = color_map[theme_choice]
            st.session_state.op_theme_color = selected_color
            save_visual_config(st.session_state.bg_img_url, selected_color)
            st.success("🎨 主题配置已持久化保存！")
            st.rerun()
            
    with t1:
        st.session_state.ledger = st.data_editor(st.session_state.ledger, num_rows="dynamic", use_container_width=True)
        st.success("管理员具有底层数据强更权限。")
    with t3:
        st.dataframe(st.session_state.audit_logs, use_container_width=True)
        
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 退出超级管理员空间", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()
    st.stop()


# ==========================================
# 权限大类 2：普通业务账户区域（财务、义工、当家）
# ==========================================
st.sidebar.markdown(f"### 🕯️ 当前操作人员：\n**{current_user['name']}**")
st.sidebar.markdown(f"**岗位角色**：`{current_user['title']}`")
st.sidebar.markdown(f"**联系电话**：`{current_user['phone']}`")

if st.sidebar.button("🚪 安全交班/退出系统", use_container_width=True):
    st.session_state.logged_in = False
    st.rerun()

st.markdown(f"# ⛩️ 昊天观财务管理控制后台")

# 核心业务三大操作看盘
tabs = st.tabs(["📝 凭证分类账登记中心", "🔍 历史凭证解译与检索", "📊 观内资产统计与债务台账"])

# 1. 凭证记账大厅
with tabs[0]:
    if current_role in ["volunteer", "finance", "temple_head"]:
        st.markdown("### 📝 昊天观凭证分类账登记中心")
        with st.form("ledger_input_form", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                f_date = st.date_input("1. 选择变动日期", datetime.now())
                f_type = st.radio("2. 资金性质", ["收入", "支出"])
                f_cate1 = st.selectbox("3. 一级科目", ["捐赠性收入(非经营)", "宗教活动收入", "功德箱收入", "场所日常维护", "场所建设与修缮", "教职人员单费与劳务"])
                f_cate2 = st.selectbox("4. 二级明细明细", ["信众随喜功德款", "专项法会功德款", "修缮专项捐款", "水电开支", "法器香烛采购", "日常维修与施工支出", "其他"])
            with col_b:
                f_tax = st.selectbox("5. 税收属性", ["免税资产", "应税收入项目", "不涉及税项"])
                f_amount = st.number_input("6. 变动金额 (元)", min_value=0.0, step=100.0)
                f_person = st.text_input("7. 功德主/经手人姓名", placeholder="请输入相关缘主或负责人")
                f_file = st.file_uploader("8. 上传凭证/收据/借条协议残卷", type=["jpg", "png", "pdf"])
            f_memo = st.text_area("9. 详细用途明细与债务备注", placeholder="如为借款，请写明债权人、利率及偿还限期...")
            
            if st.form_submit_button("🔥 确认提交并生成凭证"):
                file_name = f_file.name if f_file else "未上传凭证"
                new_row = {
                    '日期': f_date.strftime('%Y-%m-%d'), '类型': f_type, '一级科目': f_cate1, '二级科目': f_cate2,
                    '税收属性': f_tax, '金额': f_amount, '经手人/功德主': f_person, '票据凭证': file_name,
                    '操作人姓名': current_user['name'], '操作人手机': current_user['phone'], '备注': f_memo
                }
                st.session_state.ledger = pd.concat([st.session_state.ledger, pd.DataFrame([new_row])], ignore_index=True)
                log_action(current_user['username'], current_user['name'], "账目登记", f"记账完成：金额 {f_amount} 元")
                st.success("🎉 账目登记录入成功！已纳入系统内控审计。")
    else:
        st.warning("⚠️ 权限未就绪，请联系超级管理员。")

# 2. 查询与检索大厅
with tabs[1]:
    st.markdown("### 🔍 历史凭证解译与多维度检索中心")
    if st.session_state.ledger.empty:
        st.info("🍃 账目流水空空如也，请先在‘登记中心’录入数据。")
    else:
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            search_type = st.selectbox("筛选资金性质", ["全部", "收入", "支出"])
        with col_s2:
            search_kw = st.text_input("关键字检索 (支持科目/备注/经手人)")
            
        df_filtered = st.session_state.ledger.copy()
        if search_type != "全部":
            df_filtered = df_filtered[df_filtered['类型'] == search_type]
        if search_kw:
            df_filtered = df_filtered[
                df_filtered['一级科目'].str.contains(search_kw) | 
                df_filtered['备注'].str.contains(search_kw) | 
                df_filtered['经手人/功德主'].str.contains(search_kw)
            ]
            
        st.dataframe(df_filtered, use_container_width=True)
        
        # 导出 Excel 报表（只有财务人员和当家有权下载）
        if current_role in ["finance", "temple_head"]:
            excel_data = to_excel_stream(df_filtered)
            st.download_button(
                label="📥 导出当前筛选账目为标准 Excel 报表",
                data=excel_data,
                file_name=f"haotianguan_ledger_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.info("🔒 账目 Excel 报表导出功能仅对【财务工作人员】与【当家/监院】账号开放，值班义工仅供看盘。")

# 3. 资产与债务大厅（只有财务人员和当家可见）
with tabs[2]:
    st.markdown("### 📊 观内结余资产与借贷债务监控台账")
    if current_role in ["finance", "temple_head"]:
        # 计算结余
        inc_total = st.session_state.ledger[st.session_state.ledger['类型'] == "收入"]['金额'].sum()
        exp_total = st.session_state.ledger[st.session_state.ledger['类型'] == "支出"]['金额'].sum()
        net_total = inc_total - exp_total
        
        cm1, cm2, cm3 = st.columns(3)
        with cm1: st.metric("🪙 累计收入净额", f"￥ {inc_total:,.2f}")
        with cm2: st.metric("💸 累计支出开支", f"￥ {exp_total:,.2f}")
        with cm3: st.metric("⚖️ 昊天观账面法财结余", f"￥ {net_total:,.2f}")
        
        st.markdown("---")
        st.markdown("#### 🪵 观内大额借入/债务负债追踪台账")
        st.dataframe(st.session_state.borrow_ledger, use_container_width=True)
    else:
        st.warning("🔒 核心法财统筹资产看盘属本观高度机密，非财务或当家法眼不可查阅。")
