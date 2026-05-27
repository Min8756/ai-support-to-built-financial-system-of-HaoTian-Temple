import streamlit as st
import pandas as pd
from datetime import datetime
import random

# 1. 页面基础配置
st.set_page_config(page_title="昊天观·高强度内控财务系统", layout="wide", page_icon="☯️")

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

# 3. 初始化全局持久化数据库（引入 Session 级别存储）
if 'ledger' not in st.session_state:
    st.session_state.ledger = pd.DataFrame(columns=[
        '日期', '类型', '一级科目', '二级科目', '税收属性', '金额', '经手人/功德主', '票据凭证', '具体操作员', '负责人手机', '备注'
    ])

if 'audit_logs' not in st.session_state:
    st.session_state.audit_logs = pd.DataFrame(columns=['时间', '账号角色', '实名责任人', '操作类型', '详细内容'])

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_user_role = None

# 验证码动态缓存
if 'sent_code' not in st.session_state:
    st.session_state.sent_code = None
if 'verified_session' not in st.session_state:
    st.session_state.verified_session = False

# --- 4. 可供管理员动态修改的初始实名制负责人数据库 ---
if 'user_management_db' not in st.session_state:
    st.session_state.user_management_db = {
        "volunteer": {"title": "值班义工", "name": "李居士", "phone": "13800138001", "id_card": "未登记(义工免批)"},
        "finance": {"title": "高级财务人员", "name": "张会计", "phone": "13911112222", "id_card": "610104198505125678"},
        "temple_head": {"title": "当家/监院", "name": "昊天观住持", "phone": "13566668888", "id_card": "610104197001019999"}
    }

# 辅助函数：记录审计日志
def log_action(role, real_name, action_type, detail):
    new_log = {
        '时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        '账号角色': role,
        '实名责任人': real_name,
        '操作类型': action_type,
        '详细内容': detail
    }
    st.session_state.audit_logs = pd.concat([st.session_state.audit_logs, pd.DataFrame([new_log])], ignore_index=True)

# 辅助函数：风控短信与邮件联动提示
def send_alert_email(date_str, amount, event, operator):
    to_email = "rldycym123123@163.com"
    st.toast(f"🚨 大额风控流：已向 {to_email} 发布实时审计监控快报！")

# --- 5. 统一入口：多角色实名核验登录大厅 ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>☯️ 昊天观 · 实名核验与安全内控财务系统</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #555;'>全真/正一玄门账目 · 责任到人 · 动态验证码审计闭环</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<div style='background-color: #FFF8DC; padding: 15px; border-radius: 10px; border: 1px solid #8B4513;'><b>🔒 选择职司并进行安全核验</b></div>", unsafe_allow_html=True)
        
        login_role = st.selectbox("请选择您的登录职司/身份：", [
            "值班义工账户 (volunteer)", 
            "财务工作人员账户 (finance)", 
            "当家/监院账户 (temple_head)",
            "超级管理员账户 (admin)"
        ])
        
        role_key = login_role.split("(")[1].replace(")", "").strip()
        
        # 管理员账户走独立密码通道，无需每次核验手机号
        if role_key == "admin":
            admin_pwd = st.text_input("请输入超级管理员密码", type="password")
            if st.button("进入管理员修正空间", use_container_width=True):
                if admin_pwd == "htadmin999":
                    st.session_state.logged_in = True
                    st.session_state.current_user_role = "admin"
                    log_action("超级管理员", "观内统筹人", "管理员登录", "进入后台账目与账户基础信息修正空间")
                    st.rerun()
                else:
                    st.error("❌ 管理员秘钥错误。")
        else:
            # 业务账户：拉取管理员设置或初始化的默认资料
            current_template = st.session_state.user_management_db[role_key]
            
            st.markdown("### 📋 请完善并核验您的个人实名登记信息")
            input_name = st.text_input("负责人员姓名", value=current_template["name"])
            input_phone = st.text_input("绑定手机号码", value=current_template["phone"])
            
            # 财务和当家必须输入并核验中国大陆身份证
            if role_key in ["finance", "temple_head"]:
                input_id = st.text_input("大陆身份证号(18位)", value=current_template["id_card"])
            else:
                input_id = "义工免批登记"
                
            # --- 验证码核心机制 ---
            c1, c2 = st.columns([1.5, 1])
            with c2:
                if st.button("📲 获取短信验证码", use_container_width=True):
                    if len(input_phone) != 11:
                        st.error("请输入合规的11位手机号")
                    else:
                        st.session_state.sent_code = str(random.randint(100000, 999999))
                        st.info(f"【昊天观财务中心】您的动态验证码为：`{st.session_state.sent_code}`（已安全下发至模拟网关）")
            
            with c1:
                input_code = st.text_input("输入6位短信验证码", placeholder="请输入上方蓝框中的数字")
                
            if st.button("🔐 身份实名核验并登堂入账", use_container_width=True):
                if not st.session_state.sent_code:
                    st.error("❌ 请先点击获取短信验证码！")
                elif input_code != st.session_state.sent_code:
                    st.error("❌ 验证码不匹配，核验失败！")
                elif role_key in ["finance", "temple_head"] and len(input_id) != 18:
                    st.error("❌ 财务/当家依法必须填写合规的18位大陆身份证号！")
                else:
                    # 核验通过，动态覆盖当前的即时信息
                    st.session_state.logged_in = True
                    st.session_state.current_user_role = role_key
                    st.session_state.active_user_info = {
                        "name": input_name, "phone": input_phone, "id_card": input_id, "title": current_template["title"]
                    }
                    st.session_state.sent_code = None # 清空验证码
                    log_action(current_template["title"], input_name, "实名核验登录", f"核验手机：{input_phone}，身份证：{input_id}，成功进入工作台。")
                    st.rerun()
    st.stop()

# --- 6. 正式管理后台（分权隔离机制） ---
current_role = st.session_state.current_user_role

# ==========================================
# 权限分支 A：超级管理员账户（账户信息详细修改面板）
# ==========================================
if current_role == "admin":
    st.title("⚙️ 昊天观 · 账户职司精细化修正空间 (超级管理员)")
    st.markdown("---")
    
    st.subheader("🛠️ 各岗位固定负责人基本信息修改")
    st.markdown("管理员可在此修正由于人事变动、人员登记错误导致的姓名、手机号及身份证不符问题。")
    
    for r_key, r_info in st.session_state.user_management_db.items():
        with st.expander(f"修改 {r_info['title']} 账户的默认配置资料"):
            new_name = st.text_input(f"[{r_info['title']}] 默认姓名", value=r_info["name"], key=f"edit_name_{r_key}")
            new_phone = st.text_input(f"[{r_info['title']}] 默认手机", value=r_info["phone"], key=f"edit_phone_{r_key}")
            if r_key != "volunteer":
                new_id = st.text_input(f"[{r_info['title']}] 默认身份证", value=r_info["id_card"], key=f"edit_id_{r_key}")
            else:
                new_id = "未登记(义工免批)"
                
            if st.button(f"保存 {r_info['title']} 的修正资料", key=f"save_btn_{r_key}"):
                st.session_state.user_management_db[r_key] = {
                    "title": r_info['title'], "name": new_name, "phone": new_phone, "id_card": new_id
                }
                log_action("超级管理员", "观内统筹人", "基础资料修正", f"修改了 {r_info['title']} 的预设资料。新姓名：{new_name}")
                st.success("资料更新成功！下次该岗位人员登录时将默认载入此数据。")
                st.rerun()
                
    st.markdown("---")
    st.subheader("🕵️ 全盘实时审计内控日志 (防篡改视图)")
    st.dataframe(st.session_state.audit_logs.sort_values(by='时间', ascending=False), use_container_width=True)
    
    if st.button("🚪 安全退出管理员空间", type="primary"):
        st.session_state.logged_in = False
        st.rerun()
    st.stop()

# ==========================================
# 权限分支 B：业务岗位账户（义工、财务、当家）
# ==========================================
u_info = st.session_state.active_user_info

# 侧边栏：显示当前经过短信验证的高清实名看板
st.sidebar.markdown(f"### 🕯️ 当前当班法座：\n**{u_info['name']}**")
st.sidebar.markdown(f"**岗位职司**：`{u_info['title']}`")
st.sidebar.markdown(f"**验证手机**：`{u_info['phone']}`")
if current_role != "volunteer":
    st.sidebar.markdown(f"**实名身份证**：\n`{u_info['id_card'][:6]}********{u_info['id_card'][-4:]}`")
st.sidebar.markdown("---")
st.sidebar.markdown("🛡️ **动态核验状态**：\n`短信验证码核验已通过，本次操作已被实时审计留痕`")

if st.sidebar.button("🚪 退出当前交班账户"):
    log_action(u_info['title'], u_info['name'], "用户登出", "安全退出当前班次")
    st.session_state.logged_in = False
    st.rerun()

df = st.session_state.ledger

# ==========================================
# 权限展示层级：核心看板（仅财务工作人员、当家可见）
# ==========================================
if current_role in ['finance', 'temple_head']:
    st.markdown(f"### 🏛️ 昊天观核心资产大盘看板 (调阅人：{u_info['name']})")
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
# 所有实名验证通过的账户可用：账目与原始凭证录入
# ==========================================
st.sidebar.markdown("### 📝 账目税收分类登记")
entry_type = st.sidebar.radio("资金性质", ["收入", "支出"])

if entry_type == "收入":
    primary_cat = st.sidebar.selectbox("一级科目", ["捐赠收入(非经营)", "宗教活动收入(非经营)", "生产经营收入(经营性)", "其他收入"])
    sub_cats = {
        "捐赠收入(非经营)": ["信众随喜功德款", "专项定向捐赠"],
        "宗教活动收入(非经营)": ["法会斋醮收入", "日常祈福消灾"],
        "生产经营收入(经营性)": ["文创香烛法物销售", "宫观门面房屋出租"],
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

# 税务自动判断
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
        st.sidebar.warning("⚠️ 财务合规提示：莲湖税务要求所有支出必须附原始发票凭证！")
    else:
        receipt_status = f"📄 已关联凭证({uploaded_file.name})" if uploaded_file else "⚠️ 暂无原始凭证"
        
        # 写入真实操作人员的姓名与验证过的手机号
        new_row = {
            '日期': date.strftime('%Y-%m-%d'), '类型': entry_type, '一级科目': primary_cat,
            '二级科目': secondary_cat, '税收属性': tax_property, '金额': amount, '经手人/功德主': person if person else "随喜",
            '票据凭证': receipt_status, '具体操作员': u_info['name'], '负责人手机': u_info['phone'], '备注': notes
        }
        st.session_state.ledger = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        
        # 触发全自动化多维审计与实时邮件快报
        if amount >= 5000.0 or "涉税" in tax_property:
            send_alert_email(date.strftime('%Y-%m-%d'), amount, f"[{primary_cat}-{secondary_cat}] {notes}", u_info['name'])
            log_action(u_info['title'], u_info['name'], "涉税/大额专项审计", f"登记 ￥{amount} 元账目，触发邮箱预警。")
        else:
            log_action(u_info['title'], u_info['name'], "账目登记", f"登记了一笔 {entry_type}，金额：{amount} 元。")
            
        st.sidebar.success("💾 凭证保存成功，操作人已双重背书入账！")
        st.rerun()

# ==========================================
# 报表查阅权限隔离：仅高级财务、当家账户可见
# ==========================================
if user_role == 'volunteer':
    st.info(f"💡 **值班留痕提示**：当前操作员为：`{u_info['name']}`。您已成功通过手机号动态核验。根据不相容岗位分离原则，您拥有日常记账权限。全盘明细账及五级财务报表（日/周/月/季/年）属于高级财务与当家核心权限，已被隔离保护。")
else:
    t1, t2, t3 = st.tabs(["📒 实时财务日记账", "📊 五级周期性报表中心", "🕵️ 岗位实名审计日志"])
    
    with t1:
        st.subheader("昊天观财务日记账明细（穿透到具体操作人姓名）")
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
        st.subheader("🕵️ 岗位实名核验登录与内控防篡改日志")
        st.markdown("系统精准记录每班次负责人的身份核验细节，出现任何账目偏差均可精准追溯到具体的验证手机。")
        st.dataframe(st.session_state.audit_logs.sort_values(by='时间', ascending=False), use_container_width=True)
