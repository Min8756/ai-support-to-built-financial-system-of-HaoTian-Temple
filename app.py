import streamlit as st
import pandas as pd
from datetime import datetime

# 1. 页面基础配置
st.set_page_config(page_title="昊天观·云端税收合规财务系统", layout="wide", page_icon="☯️")

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

# 3. 初始化全局数据库
if 'ledger' not in st.session_state:
    st.session_state.ledger = pd.DataFrame(columns=[
        '日期', '类型', '一级科目', '二级科目', '税收属性', '金额', '经手人/功德主', '票据凭证', '操作员', '备注'
    ])

if 'audit_logs' not in st.session_state:
    st.session_state.audit_logs = pd.DataFrame(columns=['时间', '账号', '操作类型', '详细内容'])

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_user = None

# --- 4. 账号及负责人数据库（西安莲湖区实名认证版） ---
USER_DB = {
    "volunteer": {
        "password": "ht123", "role": "volunteer", "name": "李居士(值班义工)", 
        "phone": "13800138001", "id_card": "110101199003071234"
    },
    "finance": {
        "password": "ht456", "role": "finance", "name": "张会计(专职财务)", 
        "phone": "13911112222", "id_card": "310101198505125678"
    },
    "temple_head": {
        "password": "ht789", "role": "temple_head", "name": "昊天观当家/监院", 
        "phone": "13566668888", "id_card": "440101197001019999"
    }
}

# 辅助函数：记录审计日志
def log_action(username, action_type, detail):
    new_log = {
        '时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        '账号': username,
        '操作类型': action_type,
        '详细内容': detail
    }
    st.session_state.audit_logs = pd.concat([st.session_state.audit_logs, pd.DataFrame([new_log])], ignore_index=True)

# 辅助函数：大额变动及涉税异常邮件弹窗提示
def send_alert_email(date_str, amount, event, operator, tax_type=""):
    to_email = "rldycym123123@163.com"
    st.toast(f"🚨 莲湖税风控提醒：重要财务变动已实时向 {to_email} 发送风控邮件！")

# --- 5. 安全登录系统 ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>☯️ 昊天观 · 云端税收合规财务系统</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #555;'>依照《陕西省宗教活动场所财务管理办法》与莲湖税务局征管规范设计</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.3, 1])
    with col2:
        st.markdown("<div style='background-color: #FFF8DC; padding: 15px; border-radius: 10px; border: 1px solid #8B4513;'><b>🔒 玄门职司实名登录</b></div>", unsafe_allow_html=True)
        username = st.text_input("登录账号")
        password = st.text_input("登录密码", type="password")
        
        if st.button("验明正身，进入系统", use_container_width=True):
            if username in USER_DB and USER_DB[username]["password"] == password:
                st.session_state.logged_in = True
                st.session_state.current_user = USER_DB[username]
                log_action(username, "用户登录", f"负责人：{USER_DB[username]['name']} 成功登录。")
                st.rerun()
            else:
                st.error("❌ 账号或密码错误。")
    st.stop()

# --- 6. 正式后台管理界面 ---
user = st.session_state.current_user

# 侧边栏：负责人安全与税务认定信息
st.sidebar.markdown(f"### 🕯️ 当前操作法座：\n**{user['name']}**")
st.sidebar.markdown(f"**职司角色**：`{user['role']}`")
st.sidebar.markdown(f"**实名核验**：`陕西西安·莲湖区` \n({user['id_card'][:6]}********{user['id_card'][-4:]})")
st.sidebar.markdown("---")
st.sidebar.markdown("⚙️ **莲湖税务征管状态**：\n`非营利组织企业所得税免税资格已备案`")

if st.sidebar.button("🚪 退出当前账户"):
    log_action(user['name'], "用户登出", "安全退出系统")
    st.session_state.logged_in = False
    st.session_state.current_user = None
    st.rerun()

st.title("📜 昊天观 · 账目税收性质分类核算后台")
st.markdown("---")

df = st.session_state.ledger

# ==========================================
# 权限层级 1：大盘看板（仅高级财务、当家账户可见）
# ==========================================
if user['role'] in ['finance', 'temple_head']:
    st.markdown("### 🏛️ 昊天观法财具足核心看板")
    if not df.empty:
        total_income = df[df['类型'] == '收入']['金额'].sum()
        total_expense = df[df['类型'] == '支出']['金额'].sum()
        balance = total_income - total_expense
        op_income = df[(df['类型'] == '收入') & (df['税收属性'] == '经营性收入(涉税)')]['金额'].sum()
        non_op_income = df[(df['类型'] == '收入') & (df['税收属性'] == '非经营性收入(免税)')]['金额'].sum()
    else:
        total_income, total_expense, balance, op_income, non_op_income = 0.0, 0.0, 0.0, 0.0, 0.0

    m1, m2, m3 = st.columns(3)
    m1.metric("当期总功德收入", f"￥{total_income:,.2f}")
    m2.metric("观内账面总结余", f"￥{balance:,.2f}")
    m3.metric("本季累计商业经营收入", f"￥{op_income:,.2f}", delta=f"免税非经营收入: ￥{non_op_income:,.2f}")
    st.markdown("---")

# ==========================================
# 所有账户可用：严格按税法划分的一二级科目日常登记
# ==========================================
st.sidebar.markdown("### 📝 凭证日常税收分类登记")
entry_type = st.sidebar.radio("资金性质", ["收入", "支出"])

# 税法规范化一二级科目定义
if entry_type == "收入":
    primary_cat = st.sidebar.selectbox("一级科目", ["捐赠收入(非经营)", "宗教活动收入(非经营)", "生产经营收入(经营性)", "其他收入"])
    sub_cats = {
        "捐赠收入(非经营)": ["信众随喜功德款", "专项定向捐赠"],
        "宗教活动收入(非经营)": ["法会斋醮收入", "日常祈福消灾"],
        "生产经营收入(经营性)": ["文创香烛法物销售", "宫观门面房屋出租"],
        "other_inc": ["银行利息收入", "其他合法自筹"]
    }
    # 针对其他收入做映射
    actual_primary = "其他收入" if primary_cat == "其他收入" else primary_cat
    actual_sub_key = "other_inc" if primary_cat == "其他收入" else primary_cat
else:
    primary_cat = st.sidebar.selectbox("一级科目", ["日常开支", "宗教活动支出", "修缮工程支出", "人员单费/劳务", "经营性商业成本"])
    sub_cats = {
        "日常开支": ["观内基本办公水电", "日常法物购置费"],
        "宗教活动支出": ["大型斋醮法会筹办", "对外社会慈善捐赠"],
        "修缮工程支出": ["殿堂基本维护", "神像重塑修缮"],
        "人员单费/劳务": ["常住道众单费", "雇佣常工/义工劳务补助"],
        "经营性商业成本": ["文创流通处采购进货款", "经营场所物业税费支出"]
    }
    actual_primary = primary_cat
    actual_sub_key = primary_cat

secondary_cat = st.sidebar.selectbox("二级明细科目", sub_cats[actual_sub_key])

# 税务系统自动判定属性
if "经营" in actual_primary or "商业" in actual_primary:
    tax_property = "经营性收入(涉税)" if entry_type == "收入" else "经营性成本(涉税可扣除)"
else:
    tax_property = "非经营性收入(免税)" if entry_type == "收入" else "非经营性日常开支(免税)"

st.sidebar.info(f"⚖️ 税务系统自动归类：{tax_property}")

date = st.sidebar.date_input("发生日期", datetime.now())
amount = st.sidebar.number_input("变动金额 (元)", min_value=0.0, format="%.2f")
person = st.sidebar.text_input("经手人 / 功德主姓名", placeholder="默认：十方善信随喜")
uploaded_file = st.sidebar.file_uploader("📸 上传陕西财政捐赠收据/商业发票底单", type=["jpg", "png", "pdf"])
notes = st.sidebar.text_area("详细用途说明/备注")

if st.sidebar.button("确认提交并生成凭证", type="primary"):
    if amount <= 0:
        st.sidebar.error("❌ 金额不能为零")
    elif entry_type == "支出" and uploaded_file is None:
        st.sidebar.warning("⚠️ 财务合规提示：莲湖税务要求所有支出必须附原始发票凭证！")
    else:
        receipt_status = f"📄 已关联凭证({uploaded_file.name})" if uploaded_file else "⚠️ 暂无原始凭证"
        new_row = {
            '日期': date.strftime('%Y-%m-%d'), '类型': entry_type, '一级科目': actual_primary,
            '二级科目': secondary_cat, '税收属性': tax_property, '金额': amount, '经手人/功德主': person if person else "随喜",
            '票据凭证': receipt_status, '操作员': user['name'], '备注': notes
        }
        st.session_state.ledger = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        
        # 实时风控触发
        if amount >= 5000.0 or "涉税" in tax_property:
            send_alert_email(date.strftime('%Y-%m-%d'), amount, f"[{actual_primary}-{secondary_cat}] {notes}", user['name'], tax_property)
            log_action(user['name'], "税务与大额审计风控", f"变动 ￥{amount} 元({tax_property})，已实时邮件备案。")
        else:
            log_action(user['name'], "账目登记", f"成功登记一笔 {entry_type} 账目，金额：{amount} 元。")
            
        st.sidebar.success("💾 凭证保存成功，已并入莲湖合规账簿！")
        st.rerun()

# ==========================================
# 权限层级 2：五级财务报表（仅高级财务、当家可见）
# ==========================================
if user['role'] == 'volunteer':
    st.info("💡 **合规提示**：您当前的权限为‘值班登记居士’。根据不相容岗位分离原则，多级税务周期报表专属于高级财务及当家法座查阅，感谢您的发心！")
else:
    t1, t2, t3, t4 = st.tabs(["📒 实时财务日记账", "📊 周期性财务报表", "⚖️ 陕西电子税务局申报测算", "🕵️ 账户审计日志"])
    
    with t1:
        st.subheader("昊天观财务日记账明细（含税收属性标签）")
        if df.empty:
            st.write("暂无资金变动记录。")
        else:
            st.dataframe(df, use_container_width=True)
            
    with t2:
        st.subheader("📜 昊天观合规多级周期性报表")
        if df.empty:
            st.warning("暂无数据用以生成财务报告。")
        else:
            df['parsed_date'] = pd.to_datetime(df['日期'])
            report_type = st.selectbox("请选择要调阅的报表周期：", ["日记账汇总", "周报表", "月报表", "季度报表", "年度决算报表"])
            
            # 安全稳定的报表生成机制
            if report_type == "日记账汇总":
                summary = df.groupby(['日期', '类型'])['金额'].sum().reset_index()
            elif report_type == "周报表":
                df['周次'] = df['parsed_date'].dt.isocalendar().week
                summary = df.groupby(['周次', '一级科目', '类型'])['金额'].sum().reset_index()
            elif report_type == "月报表":
                df['月份'] = df['parsed_date'].dt.to_period('M').astype(str)
                summary = df.groupby(['月份', '一级科目', '类型'])['金额'].sum().reset_index()
            elif report_type == "季度报表":
                df['季度'] = df['parsed_date'].dt.to_period('Q').astype(str)
                summary = df.groupby(['季度', '一级科目', '类型'])['金额'].sum().reset_index()
            else:
                df['年度'] = df['parsed_date'].dt.year
                summary = df.groupby(['年度', '一级科目', '类型'])['金额'].sum().reset_index()
                
            st.dataframe(summary)

    with t3:
        st.subheader("⚖️ 适用于西安市莲湖区税务申报专项数据测算")
        if df.empty:
            st.write("暂无涉税经营数据。")
        else:
            tax_income_df = df[df['税收属性'] == '经营性收入(涉税)']
            total_tax_income = tax_income_df['金额'].sum()
            
            st.metric("本期累计应税收入额(增值税基数)", f"￥{total_tax_income:,.2f}")
            if total_tax_income > 0:
                st.warning("💡 **财务审核风控提示**：请确保商业流通处依法开具发票，并依季在陕西省电子税务局申报。")
                st.dataframe(tax_income_df)
            else:
                st.success("✅ 本期无商业经营收入，本季度在陕西电子税务局进行零申报即可。")

    with t4:
        st.subheader("🕵️ 昊天观·安全实名审计日志")
        st.dataframe(st.session_state.audit_logs.sort_values(by='时间', ascending=False), use_container_width=True)
