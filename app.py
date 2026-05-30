import streamlit as st
import pandas as pd
from datetime import datetime, date
import io
import os
import random
import zipfile

# 1. 页面基础配置
st.set_page_config(page_title="昊天观财务管理系统", layout="wide", page_icon="☯️")

# --- 2. 持久化配置文件与视觉配置 ---
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

# --- 3. 动态视觉控制 ---
if not st.session_state.get('logged_in', False):
    st.markdown(f"""
        <style>
        .stApp {{ 
            background-image: url("{st.session_state.bg_img_url}") !important;
            background-size: cover !important; background-position: center !important; background-attachment: fixed !important; color: #2F2F2F; 
        }}
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

# --- 4. 标准会计字典 ---
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

VOLUNTEER_INCOME_OPTS = ACCOUNTING_STRUCTURE["收入类"]["捐赠收入"] + ACCOUNTING_STRUCTURE["收入类"]["提供服务收入"] + ACCOUNTING_STRUCTURE["收入类"]["商品销售收入"]
VOLUNTEER_EXPENSE_OPTS = ACCOUNTING_STRUCTURE["费用类"]["业务活动成本"] + ACCOUNTING_STRUCTURE["费用类"]["管理费用"] + ACCOUNTING_STRUCTURE["费用类"]["筹资费用"]

# --- 5. 初始化系统底层数据库 ---
if 'ledger' not in st.session_state:
    test_data = [
        {'流水号': 'HT-202605-001', '日期': '2026-05-30', '资金性质': '收入', '会计要素': '收入类', '一级科目': '捐赠收入', '二级科目': '信众随喜功德款', '金额': 5000.0, '经手人': '王居士', '凭证附件': '收据_2026053001.jpg', '操作员': '张会计', '备注': '信众随喜随缘功德款'},
        {'流水号': 'HT-202605-002', '日期': '2026-05-30', '资金性质': '支出', '会计要素': '费用类', '一级科目': '管理费用', '二级科目': '场所日常办公费', '金额': 1200.5, '经手人': '自来水公司', '凭证附件': '发票_2026053001.pdf', '操作员': '张会计', '备注': '交纳观内日常水电费'}
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

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

st.session_state.user_db = {
    "volunteer": {"password": "ht123", "role": "volunteer", "title": "值班义工", "name": "值班义工"},
    "finance": {"password": "ht456", "role": "finance", "title": "财务工作人员", "name": "张会计"},
    "haotianguan": {"password": "ht789", "role": "temple_head", "title": "当家/监院住持", "name": "李住持"}
}

# ✨【智能重命名引擎】
def smart_rename_by_rules(f_date, f_nature, uploaded_file):
    date_str = f_date.strftime('%Y%m%d')
    doc_type = "收据" if f_nature == "收入" else "发票"
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

def reverse_map_subject(f_nature, sub_c2):
    if f_nature == "收入":
        el, c1 = "收入类", "捐赠收入"
        if sub_c2 in ACCOUNTING_STRUCTURE["收入类"]["提供服务收入"]: c1 = "提供服务收入"
        if sub_c2 in ACCOUNTING_STRUCTURE["收入类"]["商品销售收入"]: c1 = "商品销售收入"
    else:
        el, c1 = "费用类", "管理费用"
        if sub_c2 in ACCOUNTING_STRUCTURE["费用类"]["业务活动成本"]: c1 = "业务活动成本"
        if sub_c2 in ACCOUNTING_STRUCTURE["费用类"]["筹资费用"]: c1 = "筹资费用"
    return el, c1

# 🗜️【核心打包引擎：打包 Excel 与重命名后的凭证图片】
def make_zip_archive(df_target, filename_prefix):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # 1. 压入 Excel 账目明细
        excel_buffer = io.BytesIO()
        try:
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                df_target.to_excel(writer, index=False, sheet_name="明细账目")
        except:
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                df_target.to_excel(writer, index=False, sheet_name="明细账目")
        zip_file.writestr(f"{filename_prefix}.xlsx", excel_buffer.getvalue())
        
        # 2. 压入对应的重命名凭证文件
        if '凭证附件' in df_target.columns:
            unique_files = df_target['凭证附件'].dropna().unique()
            for fname in unique_files:
                file_bytes = st.session_state.file_vault.get(fname, b"HAOTIAN_DATA_PLACEHOLDER")
                zip_file.writestr(str(fname), file_bytes)
                
    return zip_buffer.getvalue()

# --- 6. 登录控制台 ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; margin-top: 100px;'>⛩️ 昊天观财务管理中心</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.1, 1])
    with col2:
        with st.form("login_gate"):
            input_user = st.text_input("管理账号")
            input_pwd = st.text_input("管理密码", type="password")
            if st.form_submit_button("🔐 安全登录", use_container_width=True):
                if input_user in st.session_state.user_db and st.session_state.user_db[input_user]["password"] == input_pwd:
                    st.session_state.logged_in = True
                    st.session_state.current_user = st.session_state.user_db[input_user].copy()
                    st.rerun()
                else:
                    st.error("❌ 账户配钥失败。")
    st.stop()

current_user = st.session_state.current_user
current_role = current_user["role"]

st.sidebar.markdown(f"### 🕯️ 执事人：{current_user['name']}")
st.sidebar.markdown(f"岗位：`{current_user['title']}`")
if st.sidebar.button("🚪 安全换班交接", use_container_width=True):
    st.session_state.logged_in = False
    st.rerun()

# ==============================================================================
# 🎛️ 权限隔离分流大厅
# ==============================================================================
if current_role == "volunteer":
    st.markdown("## ⛩️ 昊天观·值班义工快捷账台")
    v_tab1, v_tab2 = st.tabs(["📝 快捷凭证流水登记", "🔍 今日日记账登记浏览"])
    
    with v_tab1:
        with st.form("volunteer_quick_form"):
            v_date = st.date_input("1. 变动日期", date.today())
            v_nature = st.radio("2. 资金性质", ["收入", "支出"], horizontal=True)
            opts = VOLUNTEER_INCOME_OPTS if v_nature == "收入" else VOLUNTEER_EXPENSE_OPTS
            v_c2 = st.selectbox("3. 对应账目子类别", opts)
            v_amount = st.number_input("4. 变动金额 (元)", min_value=0.0, step=10.0)
            v_memo = st.text_area("5. 录入详细说明")
            v_file = st.file_uploader("6. 上传凭证/残卷小票", type=["jpg", "png", "pdf"])
            
            if st.form_submit_button("🔥 提交账目并自动编号归档", use_container_width=True):
                if not v_memo:
                    st.error("❌ 请务必填写第5项详细说明！")
                else:
                    assigned_name = smart_rename_by_rules(v_date, v_nature, v_file)
                    if v_file:
                        st.session_state.file_vault[assigned_name] = v_file.getvalue()
                    else:
                        st.session_state.file_vault[assigned_name] = b"NO_IMAGE_DATA"
                        
                    el_auto, c1_auto = reverse_map_subject(v_nature, v_c2)
                    f_id = f"HT-{datetime.now().strftime('%Y%m%d')}-{random.randint(100,999)}"
                    
                    new_row = {
                        '流水号': f_id, '日期': v_date.strftime('%Y-%m-%d'), '资金性质': v_nature,
                        '会计要素': el_auto, '一级科目': c1_auto, '二级科目': v_c2,
                        '金额': float(v_amount), '经手人': "值班义工", '凭证附件': assigned_name, '操作员': current_user['name'], '备注': v_memo
                    }
                    st.session_state.ledger = pd.concat([st.session_state.ledger, pd.DataFrame([new_row])], ignore_index=True)
                    st.success(f"🎉 登记成功！凭证自动重命名为：`{assigned_name}`")
                    st.rerun()
                    
    with v_tab2:
        st.markdown("#### 📅 今日日记账登记浏览大厅")
        today_str = date.today().strftime('%Y-%m-%d')
        df_today = st.session_state.ledger[st.session_state.ledger['日期'] == today_str].copy()
        st.dataframe(df_today, use_container_width=True)
        
        if not df_today.empty:
            zip_data = make_zip_archive(df_today, f"今日日记账_{today_str}")
            st.markdown("⬇️ **请点击下方按钮导出打包合集（会自动弹窗让您自由选择电脑上的保存位置）：**")
            st.download_button(
                label="📥 一键导出今日日记账与重命名凭证（ZIP 压缩包合集）",
                data=zip_data,
                file_name=f"{today_str}_今日日记账打包凭证.zip",
                mime="application/zip",
                use_container_width=True
            )
        else:
            st.info("📅 今日暂未发生任何凭证流转变动。")

else:
    # 👑 财务工作人员/当家住持 专属管理控制台
    st.markdown(f"## ⛩️ 昊天观财务总监核算台")
    tabs = st.tabs(["📝 凭证分类账登记", "🔍 历史凭证与今日打包", "📊 科目明细账", "📜 年度财务报表", "🪵 借贷债务追踪"])
    
    with tabs[0]:
        with st.form("fin_form"):
            col_a, col_b = st.columns(2)
            with col_a:
                f_date = st.date_input("1. 变动日期", date.today())
                f_nature = st.radio("2. 确定资金流向性质", ["收入", "支出"], horizontal=True)
                f_el = st.selectbox("3. 会计要素大类", list(ACCOUNTING_STRUCTURE.keys()))
                f_c1 = st.selectbox("4. 一级科目", list(ACCOUNTING_STRUCTURE[f_el].keys()))
                f_c2 = st.selectbox("5. 二级明细细目", ACCOUNTING_STRUCTURE[f_el][f_c1])
            with col_b:
                f_amount = st.number_input("6. 变动金额 (元)", min_value=0.0, step=100.0)
                f_person = st.text_input("7. 功德主/经手人")
                f_file = st.file_uploader("8. 上传原始单据", type=["jpg", "png", "pdf"])
                f_memo = st.text_area("9. 录入详细说明")
                
            if st.form_submit_button("🔥 确认核算登记入库", use_container_width=True):
                if not f_memo:
                    st.error("❌ 请输入详细说明！")
                else:
                    assigned_filename = smart_rename_by_rules(f_date, f_nature, f_file)
                    if f_file:
                        st.session_state.file_vault[assigned_filename] = f_file.getvalue()
                    else:
                        st.session_state.file_vault[assigned_filename] = b"NO_DATA"
                    
                    f_id = f"HT-{datetime.now().strftime('%Y%m%d')}-{random.randint(100,999)}"
                    new_row = {
                        '流水号': f_id, '日期': f_date.strftime('%Y-%m-%d'), '资金性质': f_nature,
                        '会计要素': f_el, '一级科目': f_c1, '二级科目': f_c2,
                        '金额': float(f_amount), '经手人': f_person, '凭证附件': assigned_filename, '操作员': current_user['name'], '备注': f_memo
                    }
                    st.session_state.ledger = pd.concat([st.session_state.ledger, pd.DataFrame([new_row])], ignore_index=True)
                    st.success(f"🎉 记账成功！凭证重命名为：`{assigned_filename}`")
                    st.rerun()

    with tabs[1]:
        st.markdown("### 🔍 历史凭证总账盘")
        st.dataframe(st.session_state.ledger, use_container_width=True)
        
        st.markdown("---")
        st.markdown("#### 📅 附：今日发生日记账一键打包")
        today_str = date.today().strftime('%Y-%m-%d')
        df_today = st.session_state.ledger[st.session_state.ledger['日期'] == today_str].copy()
        st.dataframe(df_today, use_container_width=True)
        
        if not df_today.empty:
            zip_data = make_zip_archive(df_today, f"今日日记账_{today_str}")
            st.download_button(
                label="📥 点击打包导出今日全部数据（ZIP压缩包，内含Excel及重命名凭证）",
                data=zip_data,
                file_name=f"{today_str}_今日日记账打包凭证.zip",
                mime="application/zip",
                use_container_width=True
            )
        else:
            st.info("📅 今日暂未发生任何凭证流转变动。")

    with tabs[2]:
        st.markdown("### 📊 二级科目明细分类账")
        c_el = st.selectbox("科目大类", list(ACCOUNTING_STRUCTURE.keys()))
        c_c1 = st.selectbox("一级科目", list(ACCOUNTING_STRUCTURE[c_el].keys()))
        c_c2 = st.selectbox("二级细目", ACCOUNTING_STRUCTURE[c_el][c_c1])
        df_sub = st.session_state.ledger[(st.session_state.ledger['会计要素'] == c_el) & (st.session_state.ledger['一级科目'] == c_c1) & (st.session_state.ledger['二级科目'] == c_c2)]
        st.dataframe(df_sub, use_container_width=True)

    with tabs[3]:
        st.markdown("### 📜 昊天观年度整体财务报表大盘")
        # 🛠️ 彻底隔离并修复底盘：将数据转换与字符串处理完全剥离，杜绝全局 TypeError 报错
        df_calc = st.session_state.ledger.copy()
        if not df_calc.empty:
            df_calc['金额'] = pd.to_numeric(df_calc['金额'], errors='coerce').fillna(0.0)
            inc_total = df_calc[df_calc['资金性质'] == "收入"]['金额'].sum()
            exp_total = df_calc[df_calc['资金性质'] == "支出"]['金额'].sum()
        else:
            inc_total, exp_total = 0.0, 0.0
            
        col_report1, col_report2 = st.columns(2)
        with col_report1:
            st.markdown("#### 1. 业务活动表（损益大盘）")
            if not df_calc.empty:
                grp = df_calc.groupby(['一级科目', '二级科目'])['金额'].sum().reset_index()
                st.dataframe(grp, use_container_width=True)
            st.metric("⚖️ 本期净资产变动(结余结转)", f"￥ {inc_total - exp_total:,.2f}")
            
        with col_report2:
            st.markdown("#### 2. 资产负债简表")
            current_cash = 100000.0 + (inc_total - exp_total)
            bs_df = pd.DataFrame([
                {"资产项目": "流动资产：货币资金与现金存款", "期末账面价值": f"￥ {current_cash:,.2f}"},
                {"资产项目": "固定资产：大殿建筑与文物资产", "期末账面价值": "￥ 15,000,000.00"},
                {"资产项目": "资产总计", "期末账面价值": f"￥ {15000000.00 + current_cash:,.2f}"}
            ])
            st.dataframe(bs_df, use_container_width=True)

    with tabs[4]:
        st.markdown("### 🪵 观内借贷债务风险控制追踪大厅")
        active_debts = st.session_state.borrow_db.copy()
        if not active_debts.empty and '本金还款时限' in active_debts.columns:
            active_debts = active_debts.sort_values(by='本金还款时限')
        st.dataframe(active_debts, use_container_width=True)
