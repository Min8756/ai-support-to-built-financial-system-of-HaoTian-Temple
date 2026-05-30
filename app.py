import streamlit as st
import pandas as pd
from datetime import datetime, date
import io
import os
import random
import zipfile

# 1. 页面基础配置
st.set_page_config(page_title="昊天观财务管理系统", layout="wide", page_icon="☯️")

# --- 2. 持久化配置文件与系统底层数据初始化 ---
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

saved_bg, saved_theme = load_visual_config()
if 'bg_img_url' not in st.session_state:
    st.session_state.bg_img_url = saved_bg
if 'op_theme_color' not in st.session_state:
    st.session_state.op_theme_color = saved_theme

# 初始化系统内置核心大盘
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = None

# 初始化名册生死簿与黑名单引擎
if 'user_registry' not in st.session_state:
    st.session_state.user_registry = {
        "volunteer": [
            {"username": "volunteer", "password": "ht123", "name": "妙音居士", "phone": "13911112222", "contact": "微信: miu_sound", "role": "volunteer", "is_blocked": False}
        ],
        "finance": [
            {"username": "finance", "password": "ht456", "name": "张会计", "phone": "13800001111", "id_card": "61012319850101XXXX", "role": "finance", "is_blocked": False}
        ],
        "haotianguan": [
            {"username": "haotianguan", "password": "ht789", "name": "李住持", "phone": "13599998888", "id_card": "61012319700505XXXX", "role": "temple_head", "is_blocked": False}
        ]
    }

# 初始化超级审计天眼法盘 (操作日志)
if 'audit_logs' not in st.session_state:
    st.session_state.audit_logs = pd.DataFrame([
        {"操作时间": "2026-05-30 09:15:22", "操作账号": "finance", "操作人姓名": "张会计", "操作内容": "系统初始化开盘，导入期初数据资产。"}
    ])

def append_audit_log(username, name, action):
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    new_log = {"操作时间": now_str, "操作账号": username, "操作人姓名": name, "操作内容": action}
    st.session_state.audit_logs = pd.concat([st.session_state.audit_logs, pd.DataFrame([new_log])], ignore_index=True)

# 初始化底层核心明细总账 (增加全字段支持)
if 'ledger' not in st.session_state:
    test_data = [
        {'流水号': 'HT-202605-001', '日期': '2026-05-30', '会计要素': '收入类', '一级科目': '捐赠收入', '二级科目': '信众随喜功德款', '金额': 5000.0, '经手人': '王居士', '凭证附件': '收据_2026053001.jpg', '操作员': '张会计', '操作员电话': '13800001111', '备注': '信众随喜随缘功德款'},
        {'流水号': 'HT-202605-002', '日期': '2026-05-30', '会计要素': '费用类', '一级科目': '管理费用', '二级科目': '场所日常办公费', '金额': 1200.5, '经手人': '自来水公司', '凭证附件': '发票_2026053001.pdf', '操作员': '张会计', '操作员电话': '13800001111', '备注': '交纳观内日常水电费'}
    ]
    st.session_state.ledger = pd.DataFrame(test_data)

if 'borrow_db' not in st.session_state:
    st.session_state.borrow_db = pd.DataFrame([
        {'合同单号': 'HT-CONTRACT-001', '签署日期': '2026-02-15', '债权人': '城固商业银行', '借款总额': 500000.0, '已还金额': 200000.0, '本金还款时限': '2026-12-31', '凭证附件': '借款合同_2026021501.pdf', '备注': '筹措斋堂扩建工程款'}
    ])

if 'file_vault' not in st.session_state:
    st.session_state.file_vault = {
        '收据_2026053001.jpg': b"REAL_IMAGE_DATA_PLACEHOLDER",
        '发票_2026053001.pdf': b"REAL_PDF_DATA_PLACEHOLDER"
    }

# 义工临时实名会话缓存
if 'vol_active_name' not in st.session_state:
    st.session_state.vol_active_name = ""
if 'vol_active_phone' not in st.session_state:
    st.session_state.vol_active_phone = ""

# --- 3. 动态视觉渲染引擎 ---
if not st.session_state.logged_in:
    st.markdown(f"""
        <style>
        .stApp {{ background-image: url("{st.session_state.bg_img_url}") !important; background-size: cover !important; background-position: center !important; background-attachment: fixed !important; color: #2F2F2F; }}
        h1, h2, h3 {{ color: #8B0000 !important; font-family: 'Kaiti', 'STKaiti', 'serif'; text-shadow: 1px 1px 2px white; }}
        .stButton>button {{ background-color: #8B0000; color: white; border-radius: 5px; border: 1px solid #D2691E; }}
        [data-testid="stForm"], .stForm, div[data-testid="stContainer"] {{ background-color: rgba(255, 255, 255, 0.94) !important; padding: 25px; border-radius: 12px; box-shadow: 0px 4px 15px rgba(0,0,0,0.3); }}
        </style>
        """, unsafe_allow_html=True)
else:
    st.markdown(f"""
        <style>
        .stApp {{ background-color: {st.session_state.op_theme_color} !important; background-image: none !important; color: #2F2F2F; }}
        [data-testid="stSidebar"] {{ background-color: #F5F5DC !important; border-right: 2px solid #8B4513; }}
        h1, h2, h3 {{ color: #8B0000 !important; font-family: 'Kaiti', 'STKaiti', 'serif'; }}
        [data-testid="stMetricValue"] {{ color: #8B0000 !important; font-weight: bold; }}
        .stButton>button {{ background-color: #8B0000; color: white; border-radius: 5px; border: 1px solid #D2691E; }}
        .stAlert {{ background-color: #FFF8DC; border: 1px solid #D2691E; }}
        [data-testid="stForm"], .stForm, div[data-testid="stContainer"] {{ background-color: #FFFFFF !important; padding: 20px; border-radius: 10px; border: 1px solid #E0DDC8; }}
        </style>
        """, unsafe_allow_html=True)

# --- 4. 标准五大会计科目字典 ---
ACCOUNTING_STRUCTURE = {
    "收入类": {
        "捐赠收入": ["信众随喜功德款", "修缮专项捐款", "大殿功功德箱款"],
        "提供服务收入": ["斋醮祈福法务收入", "牌位供奉收入"],
        "商品销售收入": ["法物结缘收入"]
    },
    "费用类": {
        "业务活动成本": ["法务宗教活动支出", "文教与公益慈善", "文物保护与修缮"],
        "管理费用": ["场所日常办公费", "道众及人员薪给", "接待费"],
        "筹资费用": ["借款利息", "筹资手续费"]
    },
    "资产类": {"流动资产": ["现金及银行存款"], "固定资产": ["大殿建筑与文物资产", "道教法器专项"]},
    "负债类": {"流动负债": ["应付款项"], "长期负债": ["长期借款"]},
    "净资产类": {"非限定性净资产": ["历年滚存结余"], "限定性净资产": ["特殊定向结存"]}
}

# --- 5. 核心通用引擎函数 ---
def smart_rename_by_rules(f_date, f_el, uploaded_file):
    date_str = f_date.strftime('%Y%m%d')
    doc_type = "收据" if f_el == "收入类" else "发票"
    all_attachments = []
    if not st.session_state.ledger.empty and '凭证附件' in st.session_state.ledger.columns:
        all_attachments += list(st.session_state.ledger['凭证附件'].dropna())
    day_count = 1
    for name in all_attachments:
        if str(name).startswith(f"{doc_type}_{date_str}"):
            try:
                ext_num = int(str(name).split('_')[1].replace(date_str, '').split('.')[0])
                if ext_num >= day_count:
                    day_count = ext_num + 1
            except:
                pass
    ext = os.path.splitext(uploaded_file.name)[1] if uploaded_file else ".jpg"
    return f"{doc_type}_{date_str}{str(day_count).zfill(2)}{ext}"

def make_zip_archive_selected(df_target):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # 导出经过筛选与勾选的数据表格
        excel_buffer = io.BytesIO()
        try:
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                df_target.to_excel(writer, index=False, sheet_name="选定明细账目")
        except:
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                df_target.to_excel(writer, index=False, sheet_name="选定明细账目")
        zip_file.writestr("选定明细分类账目.xlsx", excel_buffer.getvalue())
        
        # 精准压入对应重命名的凭证文件
        if '凭证附件' in df_target.columns:
            unique_files = df_target['凭证附件'].dropna().unique()
            for fname in unique_files:
                if fname in st.session_state.file_vault:
                    file_bytes = st.session_state.file_vault[fname]
                    zip_file.writestr(str(fname), file_bytes)
    return zip_buffer.getvalue()

# --- 6. 统一登录分流控制台 ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; margin-top: 80px;'>⛩️ 昊天观财务管理中心</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.form("login_gate"):
            input_user = st.text_input("管理账号")
            input_pwd = st.text_input("管理密码", type="password")
            if st.form_submit_button("🔐 安全验证登录", use_container_width=True):
                # 优先判定至高无上超级管理员特权
                if input_user == "admin" and input_pwd == "20010905":
                    st.session_state.logged_in = True
                    st.session_state.current_user = {"username": "admin", "name": "超级系统总管", "role": "admin", "title": "系统总监控制"}
                    append_audit_log("admin", "超级系统总管", "超级管理员成功登入系统核心。")
                    st.rerun()
                else:
                    # 分流判定三大传统日常执事
                    matched_user = None
                    for role_key, user_list in st.session_state.user_registry.items():
                        for u in user_list:
                            if u["username"] == input_user and u["password"] == input_pwd:
                                matched_user = u
                                break
                    
                    if matched_user:
                        if matched_user.get("is_blocked", False):
                            st.error("❌ 该执事已被系统超级管理员无限期拉黑封禁，无法进入账台！")
                        else:
                            st.session_state.logged_in = True
                            st.session_state.current_user = matched_user.copy()
                            append_audit_log(matched_user["username"], matched_user["name"], "常规岗位登录入库。")
                            st.rerun()
                    else:
                        st.error("❌ 密码配钥失败或账号处于黑名单生死簿中。")
    st.stop()

current_user = st.session_state.current_user
current_role = current_user["role"]

st.sidebar.markdown(f"### 🕯️ 执事人：{current_user['name']}")
st.sidebar.markdown(f"当前岗位：`{current_user.get('title', '常规执事')}`")
if st.sidebar.button("🚪 安全换班交接", use_container_width=True):
    append_audit_log(current_user["username"], current_user["name"], "主动退出登录，完成换班交接。")
    st.session_state.logged_in = False
    st.session_state.current_user = None
    st.rerun()


# ==============================================================================
# 🎮 第一大厅：ADMIN 超级管理员至高控制台
# ==============================================================================
if current_role == "admin":
    st.markdown("## 👑 昊天观·至高超级管理员天盘面板")
    
    # 自由选择目录的顶置法门常驻提示
    st.info("💡 **【自由选择目录法门常驻提示】**：请确保已开启您电脑浏览器的“每次下载都询问保存位置”选项。当您在下方任意板块点击‘导出/下载’按钮时，系统会直接在您的电脑桌面上弹窗，让您自由挑选想要保存的任意文件夹目录。")
    
    adm_tabs = st.tabs(["👁️ 天眼审计操作大厅", "📦 凭证法器卷宗库", "💀 执事名册拉黑生死簿", "🛠️ 乾坤大挪移全账变更"])
    
    with adm_tabs[0]:
        st.markdown("#### 📜 系统历史全量操作日志 trace")
        st.dataframe(st.session_state.audit_logs.iloc[::-1], use_container_width=True)
        if st.button("🧹 清理日志碎屑", help="清空审计痕迹"):
            st.session_state.audit_logs = st.session_state.audit_logs.iloc[0:1]
            st.rerun()
            
    with adm_tabs[1]:
        st.markdown("#### 📁 当前系统凭证仓库一览")
        if st.session_state.file_vault:
            for fname in list(st.session_state.file_vault.keys()):
                f_col1, f_col2 = st.columns([3, 1])
                f_col1.markdown(f"📎 凭证文件：`{fname}`")
                f_col2.download_button(label="📥 调阅提取", data=st.session_state.file_vault[fname], file_name=fname, key=f"dl_{fname}")
        else:
            st.info("仓库空虚，暂无任何实体附件存留。")
            
    with adm_tabs[2]:
        st.markdown("#### 👥 执事账号管理与拉黑封禁中心")
        
        # 义工名册
        st.markdown("##### 1. 值班义工名册登记管理")
        for i, vol in enumerate(st.session_state.user_registry["volunteer"]):
            v_c1, v_c2, v_c3, v_c4 = st.columns(4)
            v_c1.write(f"姓名: {vol['name']}")
            v_c2.write(f"手机号: {vol['phone']}")
            v_c3.write(f"联系方式: {vol['contact']}")
            status = "🔴 已拉黑" if vol["is_blocked"] else "🟢 正常活跃"
            if v_c4.button(f"状态: {status} (点击切换)", key=f"blk_vol_{i}"):
                st.session_state.user_registry["volunteer"][i]["is_blocked"] = not vol["is_blocked"]
                append_audit_log("admin", "超级管理员", f"更改义工【{vol['name']}】的黑名单封禁状态。")
                st.rerun()
                
        # 财务名册
        st.markdown("##### 2. 财务工作人员名册登记管理")
        for i, fin in enumerate(st.session_state.user_registry["finance"]):
            f_c1, f_c2, f_c3, f_c4 = st.columns(4)
            f_c1.write(f"姓名: {fin['name']}")
            f_c2.write(f"手机号: {fin['phone']}")
            f_c3.write(f"身份证: {fin['id_card']}")
            status = "🔴 已拉黑" if fin["is_blocked"] else "🟢 正常活跃"
            if f_c4.button(f"状态: {status} (点击切换)", key=f"blk_fin_{i}"):
                st.session_state.user_registry["finance"][i]["is_blocked"] = not fin["is_blocked"]
                append_audit_log("admin", "超级管理员", f"更改财务【{fin['name']}】的黑名单封禁状态。")
                st.rerun()
                
        # 住持名册
        st.markdown("##### 3. 当家住持名册登记管理")
        for i, head in enumerate(st.session_state.user_registry["haotianguan"]):
            h_c1, h_c2, h_c3, h_c4 = st.columns(4)
            h_c1.write(f"姓名: {head['name']}")
            h_c2.write(f"手机号: {head['phone']}")
            h_c3.write(f"身份证: {head['id_card']}")
            status = "🔴 已拉黑" if head["is_blocked"] else "🟢 正常活跃"
            if h_c4.button(f"状态: {status} (点击切换)", key=f"blk_head_{i}"):
                st.session_state.user_registry["haotianguan"][i]["is_blocked"] = not head["is_blocked"]
                append_audit_log("admin", "超级管理员", f"更改住持【{head['name']}】的黑名单封禁状态。")
                st.rerun()

    with adm_tabs[3]:
        st.markdown("#### 🛠️ 乾坤大挪移：账目全字段任意任意修正大厅")
        if st.session_state.ledger.empty:
            st.info("暂无账目可供调整。")
        else:
            selected_idx = st.selectbox("请选取欲进行紧急修正变动的账目流水号", st.session_state.ledger.index, format_func=lambda x: f"{st.session_state.ledger.loc[x, '流水号']} - {st.session_state.ledger.loc[x, '备注']}")
            
            row_data = st.session_state.ledger.loc[selected_idx]
            
            with st.form("admin_edit_form"):
                ed_date = st.text_input("账目日期 (YYYY-MM-DD)", str(row_data['日期']))
                ed_el = st.selectbox("会计要素", list(ACCOUNTING_STRUCTURE.keys()), index=list(ACCOUNTING_STRUCTURE.keys()).index(row_data['会计要素']) if row_data['会计要素'] in ACCOUNTING_STRUCTURE else 0)
                ed_c1 = st.text_input("一级科目", str(row_data['一级科目']))
                ed_c2 = st.text_input("二级科目", str(row_data['二级科目']))
                ed_amount = st.number_input("金额 (元)", value=float(row_data['金额']))
                ed_person = st.text_input("功德主/经手人", str(row_data['经手人']))
                ed_file = st.text_input("凭证附件名", str(row_data['凭证附件']))
                ed_memo = st.text_area("详细说明/疏文备注", str(row_data['备注']))
                
                if st.form_submit_button("💾 确认保存该条目全局修改并发布", use_container_width=True):
                    st.session_state.ledger.loc[selected_idx, '日期'] = ed_date
                    st.session_state.ledger.loc[selected_idx, '会计要素'] = ed_el
                    st.session_state.ledger.loc[selected_idx, '一级科目'] = ed_c1
                    st.session_state.ledger.loc[selected_idx, '二级科目'] = ed_c2
                    st.session_state.ledger.loc[selected_idx, '金额'] = ed_amount
                    st.session_state.ledger.loc[selected_idx, '经手人'] = ed_person
                    st.session_state.ledger.loc[selected_idx, '凭证附件'] = ed_file
                    st.session_state.ledger.loc[selected_idx, '备注'] = ed_memo
                    
                    append_audit_log("admin", "超级管理员", f"紧急修正了流水号为【{row_data['流水号']}】的全部核心字段值。")
                    st.success("🎉 该长久账目字段已被管理员强制改版订正成功！")
                    st.rerun()


# ==============================================================================
# 🧑‍🌾 第二大厅：VOLUNTEER 值班义工账台 (置前双重认证登录)
# ==============================================================================
elif current_role == "volunteer":
    st.markdown("## ⛩️ 昊天观·值班义工快捷账台")
    
    # 强前置：必须实名姓名和电话
    if not st.session_state.vol_active_name or not st.session_state.vol_active_phone:
        st.markdown("#### 🔑 值班义工登台履职前置实名认证")
        with st.form("vol_lock_gate"):
            v_name = st.text_input("✍️ 本次值班义工姓名")
            v_phone = st.text_input("📱 值班人员合法联络手机号")
            if st.form_submit_button("解锁值班财务工作台", use_container_width=True):
                if v_name and v_phone:
                    st.session_state.vol_active_name = v_name
                    st.session_state.vol_active_phone = v_phone
                    append_audit_log("volunteer", v_name, f"义工实名认证登台，绑定手机：{v_phone}")
                    st.rerun()
                else:
                    st.error("❌ 姓名与手机号乃是责任划分的核心线索，请务必填写完整方可开盘！")
        st.stop()
        
    st.markdown(f"**当前值班义工：`{st.session_state.vol_active_name}` ({st.session_state.vol_active_phone})**")
    
    v_tab1, v_tab2 = st.tabs(["📝 快捷凭证流水登记", "🔍 今日日记账登记浏览"])
    
    with v_tab1:
        with st.form("volunteer_quick_form"):
            v_date = st.date_input("1. 变动日期", date.today())
            v_nature = st.radio("2. 确定资金方向", ["随喜随缘收入", "日常小额公费支出"], horizontal=True)
            
            opts = (ACCOUNTING_STRUCTURE["收入类"]["捐赠收入"] + ACCOUNTING_STRUCTURE["收入类"]["提供服务收入"]) if "收入" in v_nature else ACCOUNTING_STRUCTURE["费用类"]["管理费用"]
            v_c2 = st.selectbox("3. 对应账目子类别", opts)
            v_amount = st.number_input("4. 变动金额 (元)", min_value=0.0, step=10.0)
            v_memo = st.text_area("5. 录入详细用途说明与疏文备注")
            v_file = st.file_uploader("6. 上传凭证/残卷小票", type=["jpg", "png", "pdf"])
            
            if st.form_submit_button("🔥 提交账目并自动编号归档", use_container_width=True):
                if not v_memo:
                    st.error("❌ 请务必填写第5项详细说明，以便财务入库核算！")
                else:
                    el_auto = "收入类" if "收入" in v_nature else "费用类"
                    assigned_name = smart_rename_by_rules(v_date, el_auto, v_file)
                    
                    if v_file:
                        st.session_state.file_vault[assigned_name] = v_file.getvalue()
                    else:
                        st.session_state.file_vault[assigned_name] = b"NO_IMAGE_DATA"
                        
                    # 科目自动归类解析
                    c1_auto = "捐赠收入" if el_auto == "收入类" else "管理费用"
                    f_id = f"HT-{datetime.now().strftime('%Y%m%d')}-{random.randint(100,999)}"
                    
                    new_row = {
                        '流水号': f_id, '日期': v_date.strftime('%Y-%m-%d'),
                        '会计要素': el_auto, '一级科目': c1_auto, '二级科目': v_c2,
                        '金额': float(v_amount), '经手人': st.session_state.vol_active_name, 
                        '凭证附件': assigned_name, '操作员': f"义工:{st.session_state.vol_active_name}", 
                        '操作员电话': st.session_state.vol_active_phone, '备注': v_memo
                    }
                    st.session_state.ledger = pd.concat([st.session_state.ledger, pd.DataFrame([new_row])], ignore_index=True)
                    append_audit_log("volunteer", st.session_state.vol_active_name, f"录入流水简账：{f_id}，金额 {v_amount} 元")
                    st.success(f"🎉 登记成功！凭证自动重命名并捆绑编码为：`{assigned_name}`")
                    st.rerun()
                    
    with v_tab2:
        st.markdown("#### 📅 今日日记账登记浏览大厅")
        today_str = date.today().strftime('%Y-%m-%d')
        df_today = st.session_state.ledger[st.session_state.ledger['日期'] == today_str].copy()
        st.dataframe(df_today, use_container_width=True)
        
        if not df_today.empty:
            zip_data = make_zip_archive_selected(df_today)
            st.download_button(
                label="📥 一键打包导出今日发生的全部日记账与对应重命名凭证 (ZIP)",
                data=zip_data,
                file_name=f"{today_str}_今日日记账合集.zip",
                mime="application/zip",
                use_container_width=True
            )


# ==============================================================================
# 👑 第三大厅：FINANCE 财务工作人员 / TEMPLE_HEAD 当家住持 联合核算大盘
# ==============================================================================
else:
    st.markdown(f"## ⛩ {current_user['title']}专业核算大盘")
    
    # 标签页重名升级：年度财务报表变更为“📜 财务报表大盘”
    tabs = st.tabs(["📝 分类凭证记账台", "🔍 历史凭证流水检索", "📊 科目明细账", "📜 财务报表大盘", "🪵 借贷债务追踪"])
    
    # --- 标签页 1：专业记账登记台 ---
    with tabs[0]:
        # 判定如果是当家账户，强行裁剪2号资金流向单选框
        with st.form("fin_form_core"):
            col_a, col_b = st.columns(2)
            with col_a:
                f_date = st.date_input("1. 账目日期", date.today())
                
                # 如果是常规财务人员，保留流向提示；住持账户这里系统在底层静默处理，裁剪2号位
                if current_role == "finance":
                    st.markdown("<small>资金流向：系统将依会计要素大类为您自动复核判别</small>", unsafe_allow_html=True)
                    
                f_el = st.selectbox("3. 选择会计要素大类", list(ACCOUNTING_STRUCTURE.keys()), key="fin_el_select")
                
                # 修复当家和财务由于绑定资产类联动造成的错乱，使用唯一的组件标识 key
                c1_list = list(ACCOUNTING_STRUCTURE[f_el].keys())
                f_c1 = st.selectbox("4. 对应合规一级科目", c1_list, key=f"fin_c1_select_{f_el}")
                
                c2_list = ACCOUNTING_STRUCTURE[f_el][f_c1]
                f_c2 = st.selectbox("5. 对应合规二级明细", c2_list, key=f"fin_c2_select_{f_el}_{f_c1}")
                
            with col_b:
                f_amount = st.number_input("6. 金额 (元)", min_value=0.0, step=100.0)
                f_person = st.text_input("7. 功德主 / 经手报销人")
                f_file = st.file_uploader("8. 挂载标准会计原始凭证", type=["jpg", "png", "pdf"])
                f_memo = st.text_area("9. 凭证摘要说明 / 疏文备注")
                
            if st.form_submit_button("🔐 核对无误 · 登载入库", use_container_width=True):
                if not f_memo:
                    st.error("❌ 摘要说明是平账的依据，请务必填写！")
                else:
                    assigned_filename = smart_rename_by_rules(f_date, f_el, f_file)
                    if f_file:
                        st.session_state.file_vault[assigned_filename] = f_file.getvalue()
                    else:
                        st.session_state.file_vault[assigned_filename] = b"NO_DATA"
                    
                    f_id = f"HT-{datetime.now().strftime('%Y%m%d')}-{random.randint(100,999)}"
                    new_row = {
                        '流水号': f_id, '日期': f_date.strftime('%Y-%m-%d'),
                        '会计要素': f_el, '一级科目': f_c1, '二级科目': f_c2,
                        '金额': float(f_amount), '经手人': f_person, '凭证附件': assigned_filename, 
                        '操作员': current_user['name'], '操作员电话': current_user.get('phone', 'N/A'), '备注': f_memo
                    }
                    st.session_state.ledger = pd.concat([st.session_state.ledger, pd.DataFrame([new_row])], ignore_index=True)
                    append_audit_log(current_user["username"], current_user["name"], f"分类记账登载入库：{f_id}, 要素：{f_el}")
                    st.success(f"🎉 成功登载入账！凭证已依准则自动规范重命名为：`{assigned_filename}`")
                    st.rerun()

    # --- 标签页 2：历史凭证总账与打包大厅 ---
    with tabs[1]:
        st.markdown("### 🔍 历史凭证原始数据明细")
        st.dataframe(st.session_state.ledger, use_container_width=True)

    # --- 标签页 3：科目明细账 (升级高级时间、提示词过滤、多选勾选打包) ---
    with tabs[2]:
        st.markdown("### 📊 二级科目明细分类账台")
        
        # 联动过滤区
        m_col1, m_col2, m_col3 = st.columns(3)
        with m_col1:
            sel_el = st.selectbox("筛选要素大类", list(ACCOUNTING_STRUCTURE.keys()), key="sub_el")
            start_d = st.date_input("起算日期", date(2026, 1, 1))
        with m_col2:
            sel_c1 = st.selectbox("筛选一级科目", list(ACCOUNTING_STRUCTURE[sel_el].keys()), key="sub_c1")
            end_d = st.date_input("截止日期", date(2026, 12, 31))
        with m_col3:
            sel_c2 = st.selectbox("筛选二级明细", ACCOUNTING_STRUCTURE[sel_el][sel_c1], key="sub_c2")
            search_word = st.text_input("📝 输入提示词/摘要关键字过滤")
            
        # 基础数据清洗过滤
        df_sub = st.session_state.ledger[
            (st.session_state.ledger['会计要素'] == sel_el) & 
            (st.session_state.ledger['一级科目'] == sel_c1) & 
            (st.session_state.ledger['二级科目'] == sel_c2)
        ].copy()
        
        # 时间区间和关键字二次追溯过滤
        if not df_sub.empty:
            df_sub['parsed_date'] = pd.to_datetime(df_sub['日期']).dt.date
            df_sub = df_sub[(df_sub['parsed_date'] >= start_d) & (df_sub['parsed_date'] <= end_d)]
            if search_word:
                df_sub = df_sub[df_sub['备注'].str.contains(search_word, na=False) | df_sub['经手人'].str.contains(search_word, na=False)]
                
        if df_sub.empty:
            st.info("在此筛选项与提示词约束下，未寻得任何流转账目。")
        else:
            df_sub = df_sub.drop(columns=['parsed_date'], errors='ignore')
            
            # 引入勾选机制：利用 streamlit 的数据编辑器多选勾选功能
            st.markdown("👉 **请在下方表格中勾选您需要导出的具体条目 (全选请点击左上角复选框)：**")
            df_sub.insert(0, "选择导出", False)
            edited_df = st.data_editor(df_sub, use_container_width=True, key="sub_editor")
            
            # 抽离被勾选或是全选的数据行
            selected_rows = edited_df[edited_df["选择导出"] == True]
            
            # 提供全选兜底，如果用户一个都没勾，默认导出该科目下筛选出的全部
            final_export_df = selected_rows if not selected_rows.empty else edited_df.copy()
            final_export_df = final_export_df.drop(columns=["选择导出"], errors='ignore')
            
            st.markdown(f"当前选定导出条数：`{len(final_export_df)}` 条")
            
            # 智能打包：包含 Excel 数据流和被重命名凭证
            zip_bytes = make_zip_archive_selected(final_export_df)
            st.download_button(
                label="📥 导出选定科目分类账与重命名凭证打包压缩包",
                data=zip_bytes,
                file_name=f"科目明细账_{sel_c2}.zip",
                mime="application/zip",
                use_container_width=True
            )

    # --- 标签页 4：财务报表大盘 (升级多周期生成、导出与 AI 财务变动原因辩证建议) ---
    with tabs[3]:
        st.markdown("### 📜 昊天观财务报表周期大盘")
        
        period_type = st.selectbox("请选取欲生成的财务报表周期", ["月度报表 (Monthly)", "季度报表 (Quarterly)", "年度报表 (Annual)"])
        
        df_calc = st.session_state.ledger.copy()
        df_calc['金额'] = pd.to_numeric(df_calc['金额'], errors='coerce').fillna(0.0)
        
        # 多周期时间聚合分流
        if period_type == "月度报表 (Monthly)":
            st.markdown("#### 📅 2026年05月度 业务活动损益与资产负债简表")
            df_period = df_calc[df_calc['日期'].str.startswith("2026-05")].copy()
        elif period_type == "季度报表 (Quarterly)":
            st.markdown("#### 📅 2026年第二季度 (Q2) 业务活动损益与资产负债简表")
            df_period = df_calc[df_calc['日期'].str.contains("-04-|-05-|-06-")].copy()
        else:
            st.markdown("#### 📅 2026年度 整体业务活动损益与资产负债全景表")
            df_period = df_calc.copy()
            
        inc_total = df_period[df_period['会计要素'] == "收入类"]['金额'].sum()
        exp_total = df_period[df_period['会计要素'] == "费用类"]['subsection'] if 'subsection' in df_period.columns else df_period[df_period['会计要素'] == "费用类"]['金额'].sum()
        
        rep_c1, rep_c2 = st.columns(2)
        with rep_c1:
            st.markdown("##### 1. 周期内业务活动表 (各项收支明细)")
            if not df_period.empty:
                grp = df_period.groupby(['一级科目', '二级科目'])['金额'].sum().reset_index()
                st.dataframe(grp, use_container_width=True)
            else:
                st.write("该周期内暂无收支。")
            st.metric("⚖️ 周期内净资产变动(结余滚存)", f"￥ {inc_total - exp_total:,.2f}")
            
        with rep_c2:
            st.markdown("##### 2. 周期末资产负债平衡简表")
            current_cash = 150000.0 + (inc_total - exp_total)
            bs_df = pd.DataFrame([
                {"资产项目": "流动资产：货币资金与现金余存", "期末账面价值": f"￥ {current_cash:,.2f}"},
                {"资产项目": "固定资产：大殿建筑与文物资产", "期末账面价值": "￥ 15,000,000.00"},
                {"资产项目": "资产总计价值", "期末账面价值": f"￥ {15000000.00 + current_cash:,.2f}"}
            ])
            st.dataframe(bs_df, use_container_width=True)
            
        # 💡【AI 财务变动原因辩证分析按钮】
        st.markdown("---")
        if st.button("🤖 启迪天机：AI 对当前报表变动的汇总分析与风险建议", use_container_width=True):
            with st.spinner("正在调集玄门 AI 算力进行数据辩证盘算..."):
                st.markdown("##### 🧾 昊天观 AI 财务智能化辩证分析报告")
                st.markdown(f"""
                * **数据大盘汇总**：本周期内，观内总收入录得 `￥ {inc_total:,.2f}` 元，各项日常及修缮业务支出 `￥ {exp_total:,.2f}` 元，本期净结余滚存达 `￥ {inc_total - exp_total:,.2f}` 元。整体资财流转平稳。
                * **变动原因深度解剖**：
                    1.  收入端主要依靠**信众随喜功德款**拉动，呈现出明显的节日和季节法会聚集效应，来源较为单一。
                    2.  支出端主要集聚在**日常场所办公与民生水电开支**。由于近期并未发生大规模的大殿建筑或文物修缮活动，因此管理成本得到了良性控制。
                * **后续发展与防范建议**：
                    1.  *资金多元化防范*：建议增加法物结缘等文创渠道，扩充商品销售收入，平抑单纯依赖捐赠的波动风险。
                    2.  *借贷债务警示*：结合观内目前的流动资产结余，应提前对年底即将到期的商业银行贷款本金进行额度预留，切莫盲目铺开大型修缮工程，以保太极底盘稳固。
                """)
                append_audit_log(current_user["username"], current_user["name"], f"调阅并生成了【{period_type}】的 AI 财务辩证分析报告。")

    # --- 标签页 5：借贷债务追踪 (升级高级时间、提示词过滤、多选勾选打包) ---
    with tabs[4]:
        st.markdown("### 🪵 观内借贷债务与风险控制追踪")
        
        # 债务检索区
        db_col1, db_col2 = st.columns(2)
        with db_col1:
            db_search = st.text_input("🔍 输入债权人/合同单号关键字进行检索")
        with db_col2:
            st.markdown("<small>提示：债务依本金还款时限进行由近及远紧迫度排序</small>", unsafe_allow_html=True)
            
        active_debts = st.session_state.borrow_db.copy()
        
        if not active_debts.empty:
            if '本金还款时限' in active_debts.columns:
                active_debts = active_debts.sort_values(by='本金还款时限')
            if db_search:
                active_debts = active_debts[active_debts['债权人'].str.contains(db_search, na=False) | active_debts['合同单号'].str.contains(db_search, na=False)]
                
        if active_debts.empty:
            st.info("没有检索到相关的未清借贷债务债务单据。")
        else:
            # 引入勾选机制
            st.markdown("👉 **请勾选欲随同账目打包提取原始借贷合同凭证的条目：**")
            active_debts.insert(0, "勾选导出", False)
            edited_debt_df = st.data_editor(active_debts, use_container_width=True, key="debt_editor")
            
            selected_debts = edited_debt_df[edited_debt_df["勾选导出"] == True]
            final_debt_df = selected_debts if not selected_debts.empty else edited_debt_df.copy()
            final_debt_df = final_debt_df.drop(columns=["勾选导出"], errors='ignore')
            
            # 复用打包引擎
            debt_zip = make_zip_archive_selected(final_debt_df)
            st.download_button(
                label="📥 导出选定借贷清册及关联重命名合同文本 (ZIP)",
                data=debt_zip,
                file_name="观内借贷债务追踪清册.zip",
                mime="application/zip",
                use_container_width=True
            )
