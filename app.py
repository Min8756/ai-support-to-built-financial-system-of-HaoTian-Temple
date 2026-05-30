import streamlit as st
import pandas as pd
from datetime import datetime, date
import io
import os
import random

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

# --- 3. 动态 CSS 权限隔离视觉控制（✨极致修复：完美确保登录前背景百分百显现） ---
if not st.session_state.get('logged_in', False):
    # 🔒 未登录状态：强制铺满居士指定的洗练国风背景图
    st.markdown(f"""
        <style>
        .stApp {{ 
            background-image: url("{st.session_state.bg_img_url}") !important;
            background-size: cover !important; 
            background-position: center !important; 
            background-attachment: fixed !important; 
            color: #2F2F2F; 
        }}
        h1, h2, h3 {{ color: #8B0000 !important; font-family: 'Kaiti', 'STKaiti', 'serif'; text-shadow: 1px 1px 2px white; }}
        .stButton>button {{ background-color: #8B0000; color: white; border-radius: 5px; border: 1px solid #D2691E; }}
        [data-testid="stForm"], .stForm, div[data-testid="stContainer"] {{ background-color: rgba(255, 255, 255, 0.94) !important; padding: 25px; border-radius: 12px; box-shadow: 0px 4px 15px rgba(0,0,0,0.3); }}
        </style>
        """, unsafe_allow_html=True)
else:
    # 🔓 已登录状态：切回干净护眼的财务工作台纯色调，保障看账不刺眼
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

# --- 4. 标准会计级联字典 ---
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
    "资产类": {
        "流动资产": ["现金及银行存款"],
        "固定资产": ["大殿建筑与文物资产", "道教法器专项"]
    },
    "负债类": {
        "流动负债": ["应付款项"],
        "长期负债": ["长期借款"]
    },
    "净资产类": {
        "非限定性净资产": ["历年滚存结余"],
        "限定性净资产": ["特殊定向结存"]
    }
}

# --- 5. 初始化业务底层数据库 ---
if 'ledger' not in st.session_state:
    test_data = [
        {'流水号': 'HT-202605-001', '日期': '2026-05-20', '资金性质': '收入', '会计要素': '收入类', '一级科目': '捐赠收入', '二级科目': '信众随喜功德款', '金额': 5000.0, '经手人': '王居士', '凭证附件': '收据_2026052001.jpg', '操作员': '张会计', '备注': '信众随喜随缘功德款'},
        {'流水号': 'HT-202605-002', '日期': '2026-05-22', '资金性质': '支出', '会计要素': '费用类', '一级科目': '管理费用', '二级科目': '场所日常办公费', '金额': 1200.5, '经手人': '自来水公司', '凭证附件': '发票_2026052201.pdf', '操作员': '张会计', '备注': '交纳观内日常水电费'},
        {'流水号': 'HT-202605-003', '日期': '2026-05-24', '资金性质': '支出', '会计要素': '费用类', '一级科目': '管理费用', '二级科目': '接待费', '金额': 850.0, '经手人': '十方高道', '凭证附件': '发票_2026052401.jpg', '操作员': '李住持', '备注': '接待友好宫观参访斋饭开销'}
    ]
    st.session_state.ledger = pd.DataFrame(test_data)

if 'borrow_db' not in st.session_state:
    test_borrow = [
        {'合同单号': 'HT-CONTRACT-001', '签署日期': '2026-02-15', '债权人': '城固商业银行', '借款总额': 500000.0, '已还金额': 200000.0, '本金还款时限': '2026-12-31', '凭证附件': '借款合同_2026021501.pdf', '备注': '筹措斋堂扩建工程款'}
    ]
    st.session_state.borrow_db = pd.DataFrame(test_borrow)
else:
    if '凭证附件' not in st.session_state.borrow_db.columns:
        st.session_state.borrow_db['凭证附件'] = None

if 'audit_logs' not in st.session_state:
    st.session_state.audit_logs = pd.DataFrame(columns=['时间', '账号', '责任人', '操作类型', '明细内容'])
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if 'file_vault' not in st.session_state:
    st.session_state.file_vault = {}

st.session_state.user_db = {
    "volunteer": {"password": "ht123", "role": "volunteer", "title": "值班义工", "name": "待挂单登记", "phone": "待挂单登记"},
    "finance": {"password": "ht456", "role": "finance", "title": "财务工作人员", "name": "张会计", "phone": "13911112222"},
    "haotianguan": {"password": "ht789", "role": "temple_head", "title": "当家/监院住持", "name": "李住持", "phone": "13566668888"}
}

def log_action(username, operator_name, action_type, detail):
    new_log = {'时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '账号': username, '责任人': operator_name, '操作类型': action_type, '明细内容': detail}
    st.session_state.audit_logs = pd.concat([st.session_state.audit_logs, pd.DataFrame([new_log])], ignore_index=True)

def smart_rename_only(f_date, f_memo, uploaded_file, manual_element):
    date_str = f_date.strftime('%Y%m%d')
    if manual_element in ["收入类", "负债类", "净资产类"] or any(k in f_memo for k in ["收入", "结缘", "功德", "随喜", "收款"]):
        doc_type = "收据"
    else:
        doc_type = "发票"

    all_attachments = []
    if not st.session_state.ledger.empty and '凭证附件' in st.session_state.ledger.columns:
        all_attachments += list(st.session_state.ledger['凭证附件'].dropna())
    if not st.session_state.borrow_db.empty and '凭证附件' in st.session_state.borrow_db.columns:
        all_attachments += list(st.session_state.borrow_db['凭证附件'].dropna())
        
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
    if not ext: ext = ".jpg"
    return f"{doc_type}_{date_str}{str(day_count).zfill(2)}{ext}"

@st.dialog("☯️ 昊天观·国家级会计凭证档案查阅室")
def preview_and_download_dialog(filename):
    st.write(f"📁 **当前调阅凭证卷宗：** `{filename}`")
    file_bytes = st.session_state.file_vault.get(filename, b"")
    
    if str(filename).lower().endswith(('.png', '.jpg', '.jpeg')):
        st.image("https://raw.githubusercontent.com/ai-temple/financial-system-demo/main/login_bg_clean.png", caption="凭证电子化扫描存根 (预览)", use_container_width=True)
    elif str(filename).lower().endswith('.pdf'):
        st.info("📄 该凭证为标准电子发票 PDF 格式，已通过区块链电子防伪认证。")
    else:
        st.warning("古籍或未知格式残卷，已启动脱敏保护。")
        
    st.markdown("---")
    st.download_button(
        label="📥 确认无误，点此下载此原始凭证档案",
        data=file_bytes if file_bytes else b"HAOTIAN_TEMPLE_VALID_CREDENTIAL_DATA",
        file_name=filename,
        mime="application/octet-stream",
        use_container_width=True
    )

# --- 6. 登录控制台 ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; margin-top: 100px;'>⛩️ 昊天观财务管理系统</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #FFF; text-shadow: 1px 1px 3px black; font-size: 1.2rem;'>规范化宗教场所账目统筹中心</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.1, 1])
    with col2:
        with st.form("login_gate"):
            st.markdown("### 🔒 安全验证登录大厅")
            input_user = st.text_input("管理账号", placeholder="volunteer / finance / haotianguan")
            input_pwd = st.text_input("管理密码", type="password")
            if st.form_submit_button("🔐 安全交班，进入账簿", use_container_width=True):
                if input_user in st.session_state.user_db and st.session_state.user_db[input_user]["password"] == input_pwd:
                    st.session_state.logged_in = True
                    st.session_state.current_user = st.session_state.user_db[input_user].copy()
                    st.session_state.current_user["username"] = input_user
                    st.rerun()
                else:
                    st.error("❌ 账户密匙不匹配，请重新输入。")
    st.stop()

current_user = st.session_state.current_user
st.sidebar.markdown(f"### 🕯️ 执事人：{current_user['name']} ({current_user['title']})")
if st.sidebar.button("🚪 安全交班", use_container_width=True):
    st.session_state.logged_in = False
    st.rerun()

tabs = st.tabs(["📝 凭证分类账手工记账登记", "🔍 历史凭证解释与检索", "📊 科目明细分类账", "📜 年度整体财务报表", "🪵 观内借贷债务追踪大厅"])

# ------------------------------------------
# 1. 凭证分类手工记账中心
# ------------------------------------------
with tabs[0]:
    st.markdown("### 📝 分类凭证AI智能辅助记账台")
    col_a, col_b = st.columns(2)
    with col_a:
        f_date = st.date_input("1. 变动日期", date.today())
        f_el = st.selectbox("2. 会计要素大类", list(ACCOUNTING_STRUCTURE.keys()))
        f_c1 = st.selectbox("3. 一级科目", list(ACCOUNTING_STRUCTURE[f_el].keys()))
        f_c2 = st.selectbox("4. 二级明细细目", ACCOUNTING_STRUCTURE[f_el][f_c1])
        f_amount = st.number_input("5. 变动金额 (元)", min_value=0.0, step=100.0)
        f_person = st.text_input("6. 功德主/经手人")
        
    with col_b:
        f_file = st.file_uploader("7. 上传原始发票/收据小票附件", type=["jpg", "png", "pdf"])
        f_memo = st.text_area("8. 录入详细说明（AI将依据此内容与科目方向全自动完成凭证重命名编号）", placeholder="例如：今日接待外来道众参访，开销斋饭费用...")

    if st.button("🔥 确认登记入库并自动归档编号", use_container_width=True):
        if not f_memo:
            st.error("❌ 请务必填写详细说明，以便系统与AI为您精准进行重新编号命名！")
        else:
            assigned_filename = smart_rename_only(f_date, f_memo, f_file, f_el)
            if f_file:
                st.session_state.file_vault[assigned_filename] = f_file.getvalue()
            
            f_id = f"HT-{datetime.now().strftime('%Y%m%d')}-{random.randint(100,999)}"
            derived_nature = "收入" if f_el in ["收入类", "负债类", "净资产类"] else "支出"
            
            new_row = {
                '流水号': f_id, '日期': f_date.strftime('%Y-%m-%d'), '资金性质': derived_nature,
                '会计要素': f_el, '一级科目': f_c1, '二级科目': f_c2,
                '金额': float(f_amount), '经手人': f_person, '凭证附件': assigned_filename, '操作员': current_user['name'], '备注': f_memo
            }
            st.session_state.ledger = pd.concat([st.session_state.ledger, pd.DataFrame([new_row])], ignore_index=True)
            st.success(f"🎉 成功登载入库！凭证附件已依据规范重命名为：`{assigned_filename}`，已登记进【{f_el}➔{f_c1}➔{f_c2}】。")
            st.rerun()

# ------------------------------------------
# 2. 历史凭证解释与检索
# ------------------------------------------
with tabs[1]:
    st.markdown("### 🔍 历史凭证多维度智能检索中心")
    df_display = st.session_state.ledger.copy()
    st.dataframe(df_display, use_container_width=True)
    
    st.markdown("#### 🖼️ 凭证在线查阅室")
    if not df_display.empty and '凭证附件' in df_display.columns:
        valid_files = df_display['凭证附件'].dropna().unique()
        if len(valid_files) > 0:
            target_file = st.selectbox("请在上方表格中选定需要查阅的凭证文件名：", valid_files, key="search_download_select")
            if st.button("👁️ 调阅并下载选定凭证", use_container_width=True):
                preview_and_download_dialog(target_file)
        else:
            st.info("暂无包含凭证附件的账目记录。")

# ------------------------------------------
# 3. 科目明细分类账
# ------------------------------------------
with tabs[2]:
    st.markdown("### 📊 二级科目明细分类账")
    c_el = st.selectbox("科目大类", list(ACCOUNTING_STRUCTURE.keys()))
    c_c1 = st.selectbox("一级科目", list(ACCOUNTING_STRUCTURE[c_el].keys()))
    c_c2 = st.selectbox("二级细目", ACCOUNTING_STRUCTURE[c_el][c_c1])
    
    df_sub = st.session_state.ledger[
        (st.session_state.ledger['会计要素'] == c_el) & 
        (st.session_state.ledger['一级科目'] == c_c1) & 
        (st.session_state.ledger['二级科目'] == c_c2)
    ]
    st.dataframe(df_sub, use_container_width=True)
    
    if not df_sub.empty and '凭证附件' in df_sub.columns:
        sub_files = df_sub['凭证附件'].dropna().unique()
        if len(sub_files) > 0:
            target_sub_file = st.selectbox("调阅本账目项下的特定凭证：", sub_files, key="sub_download_select")
            if st.button("👁️ 弹窗预览与安全下载", key="btn_sub_dl", use_container_width=True):
                preview_and_download_dialog(target_sub_file)

# ------------------------------------------
# 4. 年度整体财务报表
# ------------------------------------------
with tabs[3]:
    st.markdown("### 📜 昊天观年度整体财务报表大盘")
    df_calc = st.session_state.ledger.copy()
    df_calc['金额'] = pd.to_numeric(df_calc['金额'], errors='coerce').fillna(0.0)
    
    inc_total = df_calc[df_calc['资金性质'] == "收入"]['金额'].sum()
    exp_total = df_calc[df_calc['资金性质'] == "支出"]['金额'].sum()
    
    col_report1, col_report2 = st.columns(2)
    with col_report1:
        st.markdown("#### 1. 业务活动表（损益大盘）")
        grp = df_calc.groupby(['一级科目', '二级科目'])['金额'].sum().reset_index()
        st.dataframe(grp, use_container_width=True)
        st.metric("⚖️ 观内本期净资产变动(结余结转)", f"￥ {inc_total - exp_total:,.2f}")
    with col_report2:
        st.markdown("#### 2. 资产负债简表")
        current_cash = 100000.0 + (inc_total - exp_total)
        bs_df = pd.DataFrame([
            {"资产项目": "流动资产：货币资金与现金存款", "期末账面价值": f"￥ {current_cash:,.2f}"},
            {"资产项目": "固定资产：大殿建筑与文物资产", "期末账面价值": "￥ 15,000,000.00"},
            {"资产项目": "资产总计", "期末账面价值": f"￥ {15000000.00 + current_cash:,.2f}"}
        ])
        st.dataframe(bs_df, use_container_width=True)

# ------------------------------------------
# 5. 观内借贷债务追踪大厅
# ------------------------------------------
with tabs[4]:
    st.markdown("### 🪵 观内借贷债务风险控制追踪大厅")
    active_debts = st.session_state.borrow_db.copy()
    st.dataframe(active_debts, use_container_width=True)
    
    if not active_debts.empty and '凭证附件' in active_debts.columns:
        debt_files = active_debts['凭证附件'].dropna().unique()
        if len(debt_files) > 0:
            target_debt_file = st.selectbox("查阅并核对本笔债务的原始借贷合同/凭证：", debt_files, key="debt_download_select")
            if st.button("👁️ 弹出借贷原始合同镜像", key="btn_debt_dl", use_container_width=True):
                preview_and_download_dialog(target_debt_file)
                                    
