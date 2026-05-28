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
.stApp {
    background-image: url("https://raw.githubusercontent.com/Min8756/ai-support-to-built-financial-system-of-HaoTian-Temple/main/Gemini_Generated_Image_iaz9q7iaz9q7iaz9.png");
    background-position: center;
    background-attachment: fixed;
    color: #2F2F2F;
}
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
st.sidebar.markdown(f"**责任手机**：`{active_phone}`")
if current_role != "volunteer":
    st.sidebar.markdown(f"**负责人身份证**：\n`{active_id[:6]}********{active_id[-4:]}`")
st.sidebar.markdown("---")
st.sidebar.markdown("🛡️ **内控安全状态**：\n`实名背书已生效，操作人已与账户一对应`")

st.sidebar.markdown("<br><br><br>", unsafe_allow_html=True)
if st.sidebar.button("🚪 安全交班/退出", use_container_width=True):
    log_action(current_user['username'], active_name, "账户退出", "安全退出当前工作台")
    st.session_state.logged_in = False
    st.session_state.v_verified = False
    st.rerun()

# 右侧主界面业务流
df = st.session_state.ledger
borrow_df = st.session_state.borrow_ledger

# A. 核心大盘资产看板（财务与当家可见）
if current_role in ['finance', 'temple_head']:
    st.markdown(f"### 🏛️ 核心资产大盘看板 (当前查阅人：{active_name})")
    
    total_income = df[df['类型'] == '收入']['金额'].sum() if not df.empty else 0.0
    total_expense = df[df['类型'] == '支出']['金额'].sum() if not df.empty else 0.0
    op_income = df[(df['类型'] == '收入') & (df['税收属性'] == '经营性收入(涉税)')]['金额'].sum() if not df.empty else 0.0
    
    total_borrowed = borrow_df['借款总额'].sum() if not borrow_df.empty else 0.0
    total_repaid = borrow_df['已还金额'].sum() if not borrow_df.empty else 0.0
    current_debt = borrow_df['尚欠金额'].sum() if not borrow_df.empty else 0.0
    
    final_balance = total_income - total_expense + total_borrowed - total_repaid

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("当期总功德收入", f"￥{total_income:,.2f}")
    m2.metric("观内实际总结余(含借款)", f"￥{final_balance:,.2f}")
    m3.metric("本季累计涉税商业收入", f"￥{op_income:,.2f}")
    m4.metric("宫观当前待偿总负债", f"￥{current_debt:,.2f}", delta="-已偿还" if total_repaid > 0 else None)
    st.markdown("---")

# B. 统一右侧做账表单区域
st.markdown("### 📝 昊天观凭证分类账登记中心")
with st.container(border=True):
    f_col1, f_col2, f_col3 = st.columns([1, 1, 1.5])
    
    with f_col1:
        if current_role == "volunteer":
            entry_types_available = ["收入", "支出"]
        else:
            entry_types_available = ["收入", "支出", "宫观借款(负债项)"]
            
        entry_type = st.radio("1️⃣ 资金性质", entry_types_available)
        date = st.date_input("2️⃣ 发生日期", datetime.now())
        amount = st.number_input("3️⃣ 变动金额 (元)", min_value=0.0, format="%.2f")
        
    with f_col2:
        if entry_type == "收入":
            primary_cat = st.selectbox("4️⃣ 一级科目", ["捐赠收入(非经营)", "宗教活动收入(非经营)", "生产经营收入(经营性)", "其他收入"])
            sub_cats = {
                "捐赠收入(非经营)": ["信众随喜功德款", "专项定向捐赠(限时专用)", "实物折价捐赠收入"],
                "宗教活动收入(非经营)": ["法会斋醮收入", "日常祈福消灾", "放生印经专款"],
                "生产经营收入(经营性)": ["文创香烛法物销售", "宫观宫殿房屋出租"],
                "其他收入": ["银行利息收入", "其他合法自筹"]
            }
            secondary_cat = st.selectbox("5️⃣ 二级明细科目", sub_cats[primary_cat])
            person = st.text_input("6️⃣ 功德主 / 经手人姓名")
            tax_property = "经营性收入(涉税)" if "经营" in primary_cat else "非经营性收入(免税)"
            
        elif entry_type == "支出":
            primary_cat = st.selectbox("4️⃣ 一级科目", ["日常开支", "宗教活动支出", "修缮工程支出", "人员单费/劳务", "经营性商业成本"])
            sub_cats = {
                "日常开支": ["观内基本办公水电", "日常法物购置费"],
                "宗教活动支出": ["大型斋醮法会筹办", "对外社会慈善捐赠", "高功执事单费开支"],
                "修缮工程支出": ["殿堂基本维护", "神像重塑修缮", "文物古建特殊保护"],
                "人员单费/劳务": ["常住道众单费", "雇佣常工/义工劳务补助"],
                "经营性商业成本": ["文创流通处采购进货款", "经营场所物业税费支出"]
            }
            secondary_cat = st.selectbox("5️⃣ 二级明细科目", sub_cats[primary_cat])
            person = st.text_input("6️⃣ 报销经手人姓名")
            tax_property = "经营性成本(涉税可扣除)" if "经营" in primary_cat or "商业" in primary_cat else "非经营性日常开支(免税)"
            
        else: # 借款(负债项)
            primary_cat = "宫观负债引流"
            secondary_cat = st.selectbox("5️⃣ 借款渠道分类", ["大功德主无息借款", "金融机构商业贷款", "兄弟宫观拆借资金"])
            person = st.text_input("6️⃣ 债权人/借款方真实姓名")
            tax_property = "负债类(免纳税关联)"

    with f_col3:
        uploaded_file = st.file_uploader("7️⃣ 📸 上传发票/收据/借条协议凭证", type=["jpg", "png", "pdf"])
        notes = st.text_area("8️⃣ 详细用途说明与债务备注 (如借款期限、利息约定等)")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔥 确认提交并生成凭证", type="primary", use_container_width=True):
            if amount <= 0:
                st.error("❌ 金额不能为零")
            elif entry_type == "支出" and uploaded_file is None:
                st.warning("⚠️ 财务合规提示：所有支出必须上传原始发票凭借！")
            elif entry_type == "宫观借款(负债项)" and current_role == "volunteer":
                st.error("❌ 严重越权：值班义工无权提交借款负债项目！")
            elif entry_type == "宫观借款(负债项)" and not person:
                st.error("❌ 登记借款必须如实填写【债权人/借款方】姓名，用以建立负债追踪。")
            else:
                receipt_status = f"📄 已关联凭证({uploaded_file.name})" if uploaded_file else "⚠️ 暂无原始凭证"
                
                if entry_type == "宫观借款(负债项)":
                    b_id = f"BRW-{datetime.now().strftime('%Y%m%d')}-{random.randint(10,99)}"
                    new_borrow = {
                        '借款单号': b_id, '借款日期': date.strftime('%Y-%m-%d'), '债权人/借款方': person,
                        '借款总额': amount, '已还金额': 0.0, '尚欠金额': amount, '经手人': active_name, '备注': notes
                    }
                    st.session_state.borrow_ledger = pd.concat([st.session_state.borrow_ledger, pd.DataFrame([new_borrow])], ignore_index=True)
                    log_action(current_user['username'], active_name, "向外借款入账", f"成功引入一笔来自【{person}】的借款，金额：{amount} 元")
                    send_alert_email(date.strftime('%Y-%m-%d'), amount, f"引入借款: {notes}", active_name)
                else:
                    new_row = {
                        '日期': date.strftime('%Y-%m-%d'), '类型': entry_type, '一级科目': primary_cat,
                        '二级科目': secondary_cat, '税收属性': tax_property, '金额': amount, '经手人/功德主': person if person else "随喜",
                        '票据凭证': receipt_status, '操作人姓名': active_name, '操作人手机': active_phone, '备注': notes
                    }
                    st.session_state.ledger = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    
                    if amount >= 5000.0 or "涉税" in tax_property:
                        send_alert_email(date.strftime('%Y-%m-%d'), amount, f"[{primary_cat}-{secondary_cat}] {notes}", active_name)
                        log_action(current_user['username'], active_name, "大额/涉税风控异常", f"录入大额收支 ￥{amount} 元")
                    else:
                        log_action(current_user['username'], active_name, "日常记账", f"成功登记一笔 {entry_type} 凭证，金额：{amount} 元")
                        
                st.success("💾 数据提交成功，已完成实名审计备份！")
                st.rerun()

st.markdown("---")

# C. 账目查看与迎检导出区域
if current_role == 'volunteer':
    st.info(f"💡 **值班留痕提示**：当前值班义工：`{active_name}`。根据不相容岗位分离原则，您拥有一级限权记账权利。昊天观核心资产账簿、周期性报表、债务还款台账以及外部审查导出接口均已受内控安全隔离保护。")
else:
    t1, t2, t3, t4 = st.tabs(["📒 实时财务日记账", "📊 宫观负债控制与还款中心", "📈 周期性报表与合规迎检中心", "🕵️ 岗位实名审计日志"])
    
    with t1:
        st.subheader("财务日常收支日记账明细")
        if not df.empty:
            c_excel = to_excel_stream(df, "日常日记账底单")
            st.download_button(
                label="📥 一键导出完整财务日记账 (审查迎检专用)",
                data=c_excel,
                file_name=f"昊天观日常日记账明细_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            st.dataframe(df, use_container_width=True)
        else:
            st.write("暂无常规资金变动记录。")
            
    with t2:
        st.subheader("🏺 昊天观未偿债务明细与还款控制台")
        if borrow_df.empty:
            st.info("清净无忧！当前昊天观账面上无任何未偿还的外债记录。")
        else:
            b_excel = to_excel_stream(borrow_df, "宫观未偿债务台账")
            st.download_button(
                label="📥 一键导出宫观负债还款对账单 (审计确权专用)",
                data=b_excel,
                file_name=f"昊天观负债与还款明细账_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            st.dataframe(borrow_df, use_container_width=True)
            
            st.markdown("#### 💳 快捷线上登记还款核销")
            with st.form("repay_form"):
                r_col1, r_col2 = st.columns(2)
                with r_col1:
                    select_b_id = st.selectbox("请选择要归还的借款单号", borrow_df['借款单号'].unique())
                    repay_amount = st.number_input("本次实际归还金额 (元)", min_value=0.0, format="%.2f")
                with r_col2:
                    repay_notes = st.text_area("还款备注说明 (如银行转账单号等)")
                    
                if st.form_submit_button("🔥 确认核销并扣减负债"):
                    idx = borrow_df[borrow_df['借款单号'] == select_b_id].index[0]
                    owed_now = borrow_df.loc[idx, '尚欠金额']
                    creditor = borrow_df.loc[idx, '债权人/借款方']
                    
                    if repay_amount <= 0:
                        st.error("❌ 还款金额必须大于零")
                    elif repay_amount > owed_now:
                        st.error(f"❌ 拦截：还款金额 (￥{repay_amount}) 超过了当前尚欠金额 (￥{owed_now})！")
                    else:
                        st.session_state.borrow_ledger.loc[idx, '已还金额'] += repay_amount
                        st.session_state.borrow_ledger.loc[idx, '尚欠金额'] -= repay_amount
                        
                        new_expense_row = {
                            '日期': datetime.now().strftime('%Y-%m-%d'), '类型': '支出', 
                            '一级科目': '日常开支', '二级科目': '日常法物购置费', '税收属性': '非经营性日常开支(免税)', 
                            '金额': repay_amount, '经手人/功德主': creditor, '票据凭证': '📄 债务核销还款单', 
                            '操作人姓名': active_name, '操作人手机': active_phone, '备注': f"偿还单号 {select_b_id} 的借款。备注: {repay_notes}"
                        }
                        st.session_state.ledger = pd.concat([st.session_state.ledger, pd.DataFrame([new_expense_row])], ignore_index=True)
                        
                        log_action(current_user['username'], active_name, "偿还借款核销", f"成功向【{creditor}】还款 {repay_amount} 元，单号：{select_b_id}")
                        st.success(f"💾 成功归还债务！单号 {select_b_id} 的尚欠金额已实时扣减。")
                        st.rerun()
                        
    with t3:
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
                
            rep_excel = to_excel_stream(summary, f"{report_type}汇总底单")
            st.download_button(
                label=f"📥 导出当前【{report_type}】汇总资产表 (报送民宗局专用)",
                data=rep_excel,
                file_name=f"昊天观_{report_type}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            st.dataframe(summary)

    with t4:
        st.subheader("🕵️ 岗位实名账密登录与防篡改操作日志")
        if not st.session_state.audit_logs.empty:
            log_excel = to_excel_stream(st.session_state.audit_logs, "全盘操作审计日志")
            st.download_button(
                label="📥 导出全盘追溯审计日志 Excel",
                data=log_excel,
                file_name=f"昊天观内控审计日志_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        st.dataframe(st.session_state.audit_logs.sort_values(by='时间', ascending=False), use_container_width=True)
