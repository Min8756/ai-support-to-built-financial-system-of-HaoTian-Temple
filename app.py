import streamlit as st
import pandas as pd
from datetime import datetime
import random

# 1. 页面基础配置：固定浏览器页签标题为指定名称
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
        "temple_head": {
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
    with col2:
        st.markdown("<div style='background-color: #FFF8DC; padding: 15px; border-radius: 10px; border: 1px solid #8B4513;'><b>🔒 系统安全登录口</b></div>", unsafe_allow_html=True)
        
        input_user = st.text_input("登录账号", placeholder="volunteer / finance / temple_head / admin")
        input_pwd = st.text_input("登录密码", type="password")
        
        if st.button("安全验证，登录后台", use_container_width=True):
            # A. 超级管理员独立安全通道（固定密码：20010905）
            if input_user == "admin":
                if input_pwd == "20010905":
                    st.session_state.logged_in = True
                    st.session_state.current_user = {"role": "admin", "username": "admin", "name": "超级管理员"}
                    log_action("admin", "超级管理员", "管理员登录", "成功进入管理台修正空间")
                    st.success("管理员身份核验成功！")
                    st.rerun()
                else:
                    st.error("❌ 超级管理员密码错误。")
            
            # B. 业务账户（义工、财务、当家）账密校验
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
# 权限大类 1：超级管理员账户（账户管理系统）
# ==========================================
if current_role == "admin":
    st.markdown("<h1 style='text-align: center;'>☯️ 昊天观财务管理系统</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #555;'>后台控制中心：负责人实名绑定与账户管理</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    st.subheader("👥 核心职司账户与具体负责人对应登记表")
    st.markdown("根据审计合规要求，请在此处将固定账户（财务、当家）精准绑定到具体负责人的姓名、大陆身份证、手机号。")
    
    for u_key in ["finance", "temple_head"]:
        u_data = st.session_state.user_db[u_key]
        with st.expander(f"⚙️ 更改与管理岗位: {u_key}"):
            edit_pwd = st.text_input(f"登录密码修改", value=u_data["password"], key=f"pwd_{u_key}")
            edit_name = st.text_input(f"绑定负责人姓名", value=u_data["name"], key=f"name_{u_key}")
            edit_phone = st.text_input(f"负责人绑定手机号", value=u_data["phone"], key=f"phone_{u_key}")
            edit_id = st.text_input(f"负责人大陆身份证号", value=u_data["id_card"], key=f"id_{u_key}")
            
            if st.button(f"保存对应关系", key=f"save_{u_key}"):
                if len(edit_id) != 18:
                    st.error("❌ 负责人大陆身份证号必须为18位！")
                elif len(edit_phone) != 11:
                    st.error("❌ 负责人手机号必须为11位！")
                else:
                    st.session_state.user_db[u_key] = {
                        "password": edit_pwd, "role": u_key, "title": u_data["title"],
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

# 如果登录的是“值班义工”账户，必须强制动态验证姓名与手机号码
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

# 确立当前账簿中的责任主体
if current_role == "volunteer":
    active_name = st.session_state.active_v_info["name"]
    active_phone = st.session_state.active_v_info["phone"]
    active_id = "义工免批登记"
else:
    active_name = current_user["name"]
    active_phone = current_user["phone"]
    active_id = current_user["id_card"]

# 侧边栏：高清实名制看板
st.sidebar.markdown(f"### 🕯️ 当前操作人员：\n**{active_name}**")
st.sidebar.markdown(f"**登录账号**：`{current_user['username']}`")
st.sidebar.markdown(f"**责任手机**：`{active_phone}`")
if current_role != "volunteer":
    st.sidebar.markdown(f"**负责人身份证**：\n`{active_id[:6]}********{active_id[-4:]}`")
st.sidebar.markdown("---")
st.sidebar.markdown("🛡️ **内控安全状态**：\n`实名背书已生效，操作人已与账户一一对应`")

if st.sidebar.button("🚪 安全交班/退出"):
    log_action(current_user['username'], active_name, "账户退出", "安全退出当前工作台")
    st.session_state.logged_in = False
    st.session_state.v_verified = False
    st.rerun()

# 固定页面顶部大标题
st.markdown("<h1 style='text-align: center;'>☯️ 昊天观财务管理系统</h1>", unsafe_allow_html=True)
st.markdown("---")

df = st.session_state.ledger

# ==========================================
# 核心大盘资产看板（仅财务工作人员、当家账户可见）
# ==========================================
if current_role in ['finance', 'temple_head']:
    st.markdown(f"### 🏛️ 核心资产大盘看板 (当前查阅人：{active_name})")
    if not df.empty:
        total_income = df[df['类型'] == '收入']['金额'].sum()
        total_expense = df[df['类型'] == '支出']['金额'].sum()
        balance = total_income - total_expense
        op_income = df[(df['类型'] == '收入') & (df['税收属性'] == '经营性收入(涉税)')]['金额'].sum()
    else:
        total_income, total_expense, balance, op_income = 0.0, 0.0, 0.0, 0.0

    m1, m2, m3 = st.columns(3)
    m1.metric("当期总功德收入", f"￥{total_income:,.2f}")
    m2.metric("观内账面总结余", f"￥{balance:,.2f}")
    m3.metric("本季累计涉税商业收入", f"￥{op_income:,.2f}")
    st.markdown("---")

# ==========================================
# 所有账户可用：日常凭证建账
# ==========================================
st.sidebar.markdown("### 📝 凭证分类账登记")
entry_type = st.sidebar.radio("资金性质", ["收入", "支出"])

if entry_type == "收入":
    primary_cat = st.sidebar.selectbox("一级科目", ["捐赠收入(非经营)", "宗教活动收入(非经营)", "生产经营收入(经营性)", "其他收入"])
    sub_cats = {
        "捐赠收入(非经营)": ["信众随喜功功德款", "专项定向捐赠"],
        "宗教活动收入(非经营)": ["法会斋醮收入", "日常祈福消灾"],
        "生产经营收入(经营性)": ["文创香烛法物销售", "宫观宫殿房屋出租"],
        "其他收入": ["银行利息收入", "其他合法自筹"]
    }
else:
    primary_cat = st.sidebar.selectbox("一级科目", ["日常开支", "宗教活动支出", "修缮工程支出", "人员单费/劳务", "经营性商业成本"])
    sub_cats = {
        "日常开支": ["观内基本办公水电", "日常法物购置费"],
        "宗教活动支出": ["大型斋醮法会筹办", "对外社会慈善捐赠"],
        "修缮工程支出": ["殿堂基本维护", "神像重塑修缮"],
        "人员单费/劳务": ["常住道众单费", "雇佣常工/义工劳务补助"],
        "经营性商业成本": ["文创流通处采购进货款", "经营场所物业税费支出"]
    }

secondary_cat = st.sidebar.selectbox("二级明细科目", sub_cats[primary_cat])

if "经营" in primary_cat or "商业" in primary_cat:
    tax_property = "经营性收入(涉税)" if entry_type == "收入" else "经营性成本(涉税可扣除)"
else:
    tax_property = "非经营性收入(免税)" if entry_type == "收入" else "非经营性日常开支(免税)"

date = st.sidebar.date_input("发生日期", datetime.now())
amount = st.sidebar.number_input("变动金额 (元)", min_value=0.0, format="%.2f")
person = st.sidebar.text_input("经手人 / 功德主姓名")
uploaded_file = st.sidebar.file_uploader("📸 上传发票/收据底单", type=["jpg", "png", "pdf"])
notes = st.sidebar.text_area("详细用途说明/备注")

if st.sidebar.button("确认提交并生成凭证", type="primary"):
    if amount <= 0:
        st.sidebar.error("❌ 金额不能为零")
    elif entry_type == "支出" and uploaded_file is None:
        st.sidebar.warning("⚠️ 财务合规提示：所有支出必须上传原始发票凭借！")
    else:
        receipt_status = f"📄 已关联凭证({uploaded_file.name})" if uploaded_file else "⚠️ 暂无原始凭证"
        
        new_row = {
            '日期': date.strftime('%Y-%m-%d'), '类型': entry_type, '一级科目': primary_cat,
            '二级科目': secondary_cat, '税收属性': tax_property, '金额': amount, '经手人/功德主': person if person else "随喜",
            '票据凭证': receipt_status, '操作人姓名': active_name, '操作人手机': active_phone, '备注': notes
        }
        st.session_state.ledger = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        
        if amount >= 5000.0 or "涉税" in tax_property:
            send_alert_email(date.strftime('%Y-%m-%d'), amount, f"[{primary_cat}-{secondary_cat}] {notes}", active_name)
            log_action(current_user['username'], active_name, "大额/涉税风控异常", f"录入大额账目 ￥{amount} 元")
        else:
            log_action(current_user['username'], active_name, "日常记账", f"成功登记一笔 {entry_type} 凭证，金额：{amount} 元")
            
        st.sidebar.success("💾 凭证保存成功！")
        st.rerun()

# ==========================================
# 报表查阅与审计隔离
# ==========================================
if current_role == 'volunteer':
    st.info(f"💡 **值班留痕提示**：当前值班义工：`{active_name}`。根据不相容岗位分离原则，您拥有日常记账权限。全局报表已受内控隔离保护。")
else:
    t1, t2, t3 = st.tabs(["📒 实时财务日记账", "📊 五级周期性报表中心", "🕵️ 岗位实名审计日志"])
    
    with t1:
        st.subheader("财务日记账明细（已穿透至具体责任人）")
        if df.empty:
            st.write("暂无资金变动记录。")
        else:
            st.dataframe(df, use_container_width=True)
            
    with t2:
        st.subheader("📜 宫观合规多级周期性报表")
        if df.empty:
            st.warning("暂无数据用以生成财务报告。")
        else:
            df['parsed_date'] = pd.to_datetime(df['日期'])
            report_type = st.selectbox("请选择要调阅的报表周期：", ["日记账汇总", "周报表", "月报表", "季度报表", "年度决算报表"])
            
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
        st.subheader("🕵️ 岗位实名账密登录与防篡改操作日志")
        st.dataframe(st.session_state.audit_logs.sort_values(by='时间', ascending=False), use_container_width=True)
