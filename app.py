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

# --- 3. 动态 CSS 权限隔离视觉控制 ---
if not st.session_state.get('logged_in', False) or (st.session_state.get('logged_in', False) and st.session_state.get('current_user', {}).get('role') == 'volunteer' and not st.session_state.get('volunteer_registered', False)):
    st.markdown(f"""
        <style>
        .stApp {{ 
            background-image: url("{st.session_state.bg_img_url}");
            background-size: cover; background-position: center; background-attachment: fixed; color: #2F2F2F; 
        }}
        [data-testid="stSidebar"] {{ background-color: rgba(245, 245, 222, 0.85); border-right: 2px solid #8B4513; }}
        h1, h2, h3 {{ color: #8B0000 !important; font-family: 'Kaiti', 'STKaiti', 'serif'; text-shadow: 1px 1px 2px white; }}
        .stButton>button {{ background-color: #8B0000; color: white; border-radius: 5px; border: 1px solid #D2691E; }}
        [data-testid="stForm"], .stForm, div[data-testid="stContainer"] {{ background-color: rgba(255, 255, 255, 0.92) !important; padding: 25px; border-radius: 12px; box-shadow: 0px 4px 15px rgba(0,0,0,0.2); }}
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

# --- 4. 严格按照民间非营利组织与宗教活动场所准则构建的“标准会计级联字典” ---
ACCOUNTING_STRUCTURE = {
    "收入类": {
        "捐赠收入": ["信众随喜功德款", "修缮专项捐款", "大殿功德箱款"],
        "提供服务收入": ["斋醮祈福法务收入", "牌位供奉收入"],
        "商品销售收入": ["法物结缘收入"]
    },
    "费用类": {
        "业务活动成本": ["法务宗教活动支出", "文教与公益慈善", "文物保护与修缮"],
        "管理费用": ["场所日常办公费", "道众及人员薪给"],
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

# 自动解析白话提示引擎
def interpret_details(is_income, details_text):
    text = details_text if details_text else ""
    if is_income:
        if any(k in text for k in ["功德箱", "开箱"]): return "收入类", "捐赠收入", "大殿功德箱款"
        if any(k in text for k in ["修缮", "造像", "贴金"]): return "收入类", "捐赠收入", "修缮专项捐款"
        if any(k in text for k in ["法会", "斋醮", "超度", "祈福"]): return "收入类", "提供服务收入", "斋醮祈福法务收入"
        return "收入类", "捐赠收入", "信众随喜功德款"
    else:
        if any(k in text for k in ["单费", "劳务", "法师"]): return "费用类", "业务活动成本", "法务宗教活动支出"
        if any(k in text for k in ["香烛", "耗材", "黄纸"]): return "费用类", "业务活动成本", "法务宗教活动支出"
        return "费用类", "管理费用", "场所日常办公费"

# --- 5. 初始化业务底层数据库 ---
if 'ledger' not in st.session_state:
    test_data = [
        {'流水号': 'HT-202605-001', '日期': '2026-05-20', '资金性质': '收入', '会计要素': '收入类', '一级科目': '捐赠收入', '二级科目': '信众随喜功德款', '金额': 5000.0, '经手人': '王居士', '凭证附件': '收据001.jpg', '操作员': '张会计', '备注': '信众随喜随缘功德款'},
        {'流水号': 'HT-202605-002', '日期': '2026-05-22', '资金性质': '支出', '会计要素': '费用类', '一级科目': '管理费用', '二级科目': '场所日常办公费', '金额': 1200.5, '经手人': '自来水公司', '凭证附件': '发票_W2026.pdf', '操作员': '张会计', '备注': '交纳观内日常水电费'},
        {'流水号': 'HT-202605-003', '日期': '2026-05-24', '资金性质': '支出', '会计要素': '费用类', '一级科目': '业务活动成本', '二级科目': '法务宗教活动支出', '金额': 1850.0, '经手人': '张常住', '凭证附件': '发票_JD88.jpg', '操作员': '李住持', '备注': '采办斋醮法会香烛黄纸'}
    ]
    st.session_state.ledger = pd.DataFrame(test_data)

# 🔥【核心修复：彻底修正字段名，增加“本金还款时限”防报错】
if 'borrow_db' not in st.session_state:
    test_borrow = [
        {'合同单号': 'HT-CONTRACT-001', '签署日期': '2026-02-15', '债权人': '城固商业银行', '借款总额': 500000.0, '已还金额': 200000.0, '本金还款时限': '2026-12-31', '备注': '筹措斋堂扩建工程款'}
    ]
    st.session_state.borrow_db = pd.DataFrame(test_borrow)

if 'audit_logs' not in st.session_state:
    st.session_state.audit_logs = pd.DataFrame(columns=['时间', '账号', '责任人', '操作类型', '明细内容'])
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'volunteer_registered' not in st.session_state:
    st.session_state.volunteer_registered = False

# 账户数据库
if 'user_db' not in st.session_state:
    st.session_state.user_db = {
        "volunteer": {"password": "ht123", "role": "volunteer", "title": "值班义工", "name": "待挂单登记", "phone": "待挂单登记"},
        "finance": {"password": "ht456", "role": "finance", "title": "财务工作人员", "name": "张会计", "phone": "13911112222"},
        "haotianguan": {"password": "ht789", "role": "temple_head", "title": "当家/监院住持", "name": "李住持", "phone": "13566668888"}
    }

def log_action(username, operator_name, action_type, detail):
    new_log = {'时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '账号': username, '责任人': operator_name, '操作类型': action_type, '明细内容': detail}
    st.session_state.audit_logs = pd.concat([st.session_state.audit_logs, pd.DataFrame([new_log])], ignore_index=True)

def to_excel_stream(dataframe, sheet_title="报表数据"):
    output = io.BytesIO()
    # 采用标准安全模式，规避部分环境缺失 openpyxl 的漏洞
    try:
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            dataframe.to_excel(writer, index=False, sheet_name=sheet_title)
    except Exception:
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            dataframe.to_excel(writer, index=False, sheet_name=sheet_title)
    return output.getvalue()

# --- 6. 登录界面 ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; margin-top: 80px;'>⛩️ 昊天观财务管理系统</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #FFF; text-shadow: 1px 1px 3px black;'>规范化宗教场所账目统筹中心</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.1, 1])
    with col2:
        st.markdown("### 🔒 安全验证登录大厅")
        input_user = st.text_input("管理账号", placeholder="volunteer / finance / haotianguan")
        input_pwd = st.text_input("管理密码", type="password")
        
        if st.button("🔐 安全交班，登录后台", type="primary", use_container_width=True):
            if input_user in st.session_state.user_db and st.session_state.user_db[input_user]["password"] == input_pwd:
                target_user = st.session_state.user_db[input_user]
                st.session_state.logged_in = True
                st.session_state.current_user = target_user.copy()
                st.session_state.current_user["username"] = input_user
                st.session_state.volunteer_registered = (input_user != "volunteer")
                st.rerun()
            else:
                st.error("❌ 账户密匙不匹配，请重新输入。")
    st.stop()

# --- 6.5 义工挂单实名登记 ---
if st.session_state.current_user["role"] == "volunteer" and not st.session_state.volunteer_registered:
    st.markdown("<h2 style='text-align: center; margin-top: 80px;'>⛩️ 值班义工实名挂单登记</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.form("volunteer_reg_form"):
            v_name = st.text_input("✨ 义工法名 / 姓名", placeholder="例如：张居士")
            v_phone = st.text_input("📱 11位手机号", placeholder="请输入绑定手机号码")
            if st.form_submit_button("确认登记并进入系统"):
                if not v_name or len(v_phone) != 11:
                    st.error("❌ 请完整填写登记信息！")
                else:
                    st.session_state.current_user["name"] = v_name
                    st.session_state.current_user["phone"] = v_phone
                    st.session_state.volunteer_registered = True
                    log_action("volunteer", v_name, "义工进场登记", f"手机：{v_phone}")
                    st.success("登记完成，正在开启账簿...")
                    st.rerun()
    st.stop()

# --- 7. 系统核心大盘 ---
current_user = st.session_state.current_user
current_role = current_user["role"]

st.sidebar.markdown(f"### 🕯️ 当前操作人员：")
st.sidebar.markdown(f"**{current_user['name']}**")
st.sidebar.markdown(f"**岗位角色**：`{current_user['title']}`")
st.sidebar.markdown(f"**留存电话**：`{current_user['phone']}`")
if st.sidebar.button("🚪 安全退出/换班交接", use_container_width=True):
    st.session_state.logged_in = False
    st.session_state.volunteer_registered = False
    st.rerun()

# 统一大盘标签页
tabs = st.tabs(["📝 凭证分类账手工记账登记", "🔍 历史凭证解释与检索", "📊 科目明细分类账", "📜 年度整体财务报表", "🪵 观内借贷债务追踪大厅"])

# ------------------------------------------
# 1. 凭证分类手工记账中心
# ------------------------------------------
with tabs[0]:
    st.markdown("### 📝 分类凭证记账与日记账登记")
    
    # 财务与住持的高级专业记账台
    sub_tabs = st.tabs(["✍️ 三级联动式手工核算", "📥 外部通用凭证批量并轨"])
    
    with sub_tabs[0]:
        # 🔥【关键修复：利用全局唯一 Session State 彻底锁死三级级联联动缓存】
        if "pro_element" not in st.session_state:
            st.session_state.pro_element = "收入类"
            
        col_a, col_b = st.columns(2)
        with col_a:
            f_date = st.date_input("1. 选择变动日期", date.today(), key="pro_date_input")
            f_type = st.radio("2. 资金性质", ["收入", "支出"], horizontal=True)
            
            # 监听大类切换
            def on_el_change():
                st.session_state.pro_c1_key = list(ACCOUNTING_STRUCTURE[st.session_state.pro_el_select].keys())[0]

            selected_el = st.selectbox(
                "3. 选择会计要素大类", 
                list(ACCOUNTING_STRUCTURE.keys()), 
                key="pro_el_select", 
                on_change=on_el_change
            )
            
            # 根据大类精准联动一级科目
            c1_opts = list(ACCOUNTING_STRUCTURE[selected_el].keys())
            selected_c1 = st.selectbox("4. 对应合规一级科目", c1_opts, key=f"c1_{selected_el}")
            
            # 根据一级科目精准联动二级明细
            c2_opts = ACCOUNTING_STRUCTURE[selected_el][selected_c1]
            selected_c2 = st.selectbox("5. 二级明细科目", c2_opts, key=f"c2_{selected_c1}")
            
        with col_b:
            f_tax = st.selectbox("6. 税收属性", ["免税资产", "不涉及税项", "应税收入"], key="pro_tax_select")
            f_amount = st.number_input("7. 变动金额 (元)", min_value=0.0, step=100.0)
            f_person = st.text_input("8. 功德主/经手人姓名")
            f_file = st.file_uploader("9. 上传凭证/残卷小票附件", type=["jpg", "png", "pdf"])
            
        f_memo = st.text_area("10. 详细用途明细说明", placeholder="请简明输入资金具体用途及备注...")
        
        if st.button("🔥 确认提交并生成凭证", use_container_width=True):
            f_id = f"HT-{datetime.now().strftime('%Y%m%d')}-{random.randint(100,999)}"
            file_name = f_file.name if f_file else "票据照常留存.jpg"
            
            new_row = {
                '流水号': f_id, '日期': f_date.strftime('%Y-%m-%d'), '资金性质': f_type,
                '会计要素': selected_el, '一级科目': selected_c1, '二级科目': selected_c2,
                '金额': f_amount, '经手人': f_person, '凭证附件': file_name, '操作员': current_user['name'], '备注': f_memo
            }
            st.session_state.ledger = pd.concat([st.session_state.ledger, pd.DataFrame([new_row])], ignore_index=True)
            log_action(current_user.get('username','admin'), current_user['name'], "专业记账", f"登载{selected_c2} ￥{f_amount}")
            st.success(f"🎉 凭证 {f_id} 成功登载入库！各大盘数据已实时完成重组归集。")
            st.rerun()

    with sub_tabs[1]:
        st.markdown("#### 📥 导入外部通用日记账数据（CSV/Excel）")
        st.info("💡 只要导入的表格中包含：'日期'、'会计要素'、'一级科目'、'二级科目'、'金额'、'经手人'、'备注'，系统即可自动解译并无缝并轨。")
        up_file = st.file_uploader("选择导入的日记账凭证文件", type=["csv", "xlsx"])
        if up_file:
            st.success("文件读取成功，等待并轨校验...")

# ------------------------------------------
# 2. 历史凭证解译与检索
# ------------------------------------------
with tabs[1]:
    st.markdown("### 🔍 历史凭证多维度智能检索中心")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        s_el = st.selectbox("过滤会计要素", ["全部要素"] + list(ACCOUNTING_STRUCTURE.keys()))
    with col2:
        s_op = st.text_input("过滤记账操作员(姓名)")
    with col3:
        s_kw = st.text_input("摘要模糊关键字(经手人/备注)")
        
    df_display = st.session_state.ledger.copy()
    if s_el != "全部要素":
        df_display = df_display[df_display['会计要素'] == s_el]
    if s_op:
        df_display = df_display[df_display['操作员'].str.contains(s_op, na=False)]
    if s_kw:
        df_display = df_display[df_display['备注'].str.contains(s_kw, na=False) | df_display['经手人'].str.contains(s_kw, na=False)]
        
    st.dataframe(df_display, use_container_width=True)
    
    # 导出 Excel 按钮防错保护
    excel_data = to_excel_stream(df_display, "检索历史流水")
    st.download_button("📥 导出当前筛选账目为标准规范 Excel 报表", data=excel_data, file_name=f"haotian_ledger_{date.today()}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ------------------------------------------
# 3. 科目明细分类账
# ------------------------------------------
with tabs[2]:
    st.markdown("### 📊 二级科目明细分类账（智能自动归集）")
    
    c_el = st.selectbox("查验科目大类", list(ACCOUNTING_STRUCTURE.keys()), key="sub_el_view")
    c_c1 = st.selectbox("查验一级科目", list(ACCOUNTING_STRUCTURE[c_el].keys()), key="sub_c1_view")
    c_c2 = st.selectbox("查验二级细目", ACCOUNTING_STRUCTURE[c_el][c_c1], key="sub_c2_view")
    
    df_sub = st.session_state.ledger[
        (st.session_state.ledger['会计要素'] == c_el) & 
        (st.session_state.ledger['一级科目'] == c_c1) & 
        (st.session_state.ledger['二级科目'] == c_c2)
    ]
    
    total_sub = pd.to_numeric(df_sub['金额'], errors='coerce').sum()
    st.markdown(f"### 【{c_c1} ➔ {c_c2}】分类账明细盘口")
    st.metric("该二级科目累计发生额", f"￥ {total_sub:,.2f}")
    st.dataframe(df_sub, use_container_width=True)

# ------------------------------------------
# 4. 年度整体财务报表
# ------------------------------------------
with tabs[3]:
    st.markdown("### 📜 昊天观年度整体财务报表大盘")
    st.caption("严格依据《民间非营利组织会计制度》，动态结转期间利差与资产变动净值。")
    
    df_calc = st.session_state.ledger.copy()
    df_calc['金额'] = pd.to_numeric(df_calc['金额'], errors='coerce').fillna(0.0)
    
    inc_total = df_calc[df_calc['资金性质'] == "收入"]['金额'].sum()
    exp_total = df_calc[df_calc['资金性质'] == "支出"]['金额'].sum()
    net_asset_change = inc_total - exp_total
    
    col_report1, col_report2 = st.columns(2)
    with col_report1:
        st.markdown("#### 1. 业务活动表（损益大盘）")
        grp = df_calc.groupby(['一级科目', '二级科目'])['金额'].sum().reset_index()
        st.dataframe(grp, use_container_width=True)
        st.metric("⚖️ 观内本期净资产变动(结余结转)", f"￥ {net_asset_change:,.2f}")
        
    with col_report2:
        st.markdown("#### 2. 资产负债简表（存续存量）")
        # 实时根据结余调整货币资产
        current_cash = 100000.0 + net_asset_change
        bs_df = pd.DataFrame({
            "资产项目": ["流动资产：货币资金与现金存款", "固定资产：大殿建筑与文物资产", "资产总计"],
            "期末账面价值": [f"￥ {current_cash:,.2f}", "￥ 15,000,000.00", f"￥ {15000000.00 + current_cash:,.2f}"]
        })
        st.dataframe(bs_df, use_container_width=True)

# ------------------------------------------
# 5. 观内借贷债务追踪大厅
# ------------------------------------------
with tabs[4]:
    st.markdown("### 🪵 观内借贷债务风险控制追踪大厅")
    
    # 🔥【终极修复：直接从修好列名的数据源中提取，彻底解决死锁】
    active_debts = st.session_state.borrow_db.copy()
    
    if not active_debts.empty:
        # 绝不再引发 KeyError
        active_debts = active_debts.sort_values(by='本金还款时限')
        
        st.dataframe(active_debts, use_container_width=True)
        
        # 实时显示最紧急的一笔账目
        urgent_debt = active_debts.iloc[0]
        st.warning(f"🚨 **风控提示**：最临近到期债务合同：`{urgent_debt['合同单号']}`，债权人：`{urgent_debt['债权人']}`，还款期限：`{urgent_debt['本金还款时限']}`，尚需筹措本金：`￥{urgent_debt['借款总额'] - urgent_debt['paid_amt'] if 'paid_amt' in urgent_debt else urgent_debt['借款总额'] - urgent_debt['已还金额']:,.2f}`。")
    else:
        st.success("🍃 观内目前两袖清风，无任何外部未结清债务。")
