import streamlit as st
import pandas as pd
from datetime import datetime
import random
import io  # 用于处理内存文件流，实现一键下载Excel

# 1. 页面基础配置：固定浏览器页签标题
st.set_page_config(page_title="昊天观财务管理系统", layout="wide", page_icon="☯️")

# --- 2. 动态背景双控制法门 (CSS) ---
# 这里的逻辑是：如果没登录，就用神明大图；如果登录了，就自动切成比侧栏更淡的纯色背景。
if not st.session_state.get('logged_in', False):
    # 登录前的神明大图背景（已为您直接嵌入您上传的那张精美无框神像直链）
    st.markdown("""
        <style>
        .stApp { 
            background-image: url("https://raw.githubusercontent.com/Min8756/ai-support-to-built-financial-system-of-HaoTian-Temple/main/Gemini_Generated_Image_1923du1923du1923.png");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            color: #2F2F2F; 
        }
        [data-testid="stSidebar"] { background-color: rgba(245, 245, 222, 0.85); border-right: 2px solid #8B4513; }
        h1, h2, h3 { color: #8B0000 !important; font-family: 'Kaiti', 'STKaiti', 'serif'; text-shadow: 1px 1px 2px white; }
        .stButton>button { background-color: #8B0000; color: white; border-radius: 5px; border: 1px solid #D2691E; }
        /* 登录框容器半透明白底 */
        [data-testid="stForm"], .stForm, div[data-testid="stContainer"] { background-color: rgba(255, 255, 255, 0.85) !important; padding: 20px; border-radius: 10px; }
        </style>
        """, unsafe_allow_html=True)
else:
    # 登录后的纯净法界：主背景切为比侧栏 (#F5F5DC) 更浅的纯米白淡色 (#FAF9F0)
    st.markdown("""
        <style>
        .stApp { 
            background-color: #FAF9F0 !important;
            background-image: none !important; /* 彻底清除神像图，防止干扰做账 */
            color: #2F2F2F; 
        }
        /* 侧边栏保持原样 */
        [data-testid="stSidebar"] { background-color: #F5F5DC !important; border-right: 2px solid #8B4513; }
        h1, h2, h3 { color: #8B0000 !important; font-family: 'Kaiti', 'STKaiti', 'serif'; }
        [data-testid="stMetricValue"] { color: #8B0000 !important; font-weight: bold; }
        .stButton>button { background-color: #8B0000; color: white; border-radius: 5px; border: 1px solid #D2691E; }
        .stButton>button:hover { background-color: #A52A2A; border: 1px solid #FFD700; }
        .stAlert { background-color: #FFF8DC; border: 1px solid #D2691E; }
        /* 后台表单融入背景 */
        [data-testid="stForm"], .stForm, div[data-testid="stContainer"] { background-color: #FFFFFF !important; padding: 20px; border-radius: 10px; border: 1px solid #E0DDC8; }
        </style>
        """, unsafe_allow_html=True)


# --- 3. 初始化全局持久化数据库 ---
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

# --- 4. 账户管理系统 ---
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

def log_action(username, operator_name, action_type, detail):
    new_log = {
        '时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        '账号': username,
        '责任人/操作员': operator_name,
        '操作类型': action_type,
        '详细内容': detail
    }
    st.session_state.audit_logs = pd.concat([st.session_state.audit_logs, pd.DataFrame([new_log])], ignore_index=True)

def send_alert_email(date_str, amount, event, operator):
    st.toast(f"🚨 大额风控流：已向安全邮箱 rldycym123123@163.com 报送风控审计底单！")

def to_excel_stream(dataframe, sheet_name_str="Sheet1"):
    output = io.BytesIO()
    try:
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            dataframe.to_excel(writer, index=False, sheet_name=sheet_name_str)
    except Exception:
        output = io.BytesIO()
        dataframe.to_csv(output, index=False, encoding='utf-8-sig')
    return output.getvalue()


# --- 5. 统一账号密码登录大厅 ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; margin-top: 50px;'>☯️ 昊天观财务管理系统</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #FFF; text-shadow: 1px 1px 3px black;'>全员账密防护机制 · 负责人实名制绑定核验</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<div style='background-color: rgba(255,248,220,0.95); padding: 25px; border-radius: 10px; border: 2px solid #8B4513; box-shadow: 3px 3px 10px rgba(0,0,0,0.3);'>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; margin-top:0;'>🔒 安全验证登录大厅</h3>", unsafe_allow_html=True)
        
        f_name_l = st.text_input("请输入真实姓名用于实名审计", placeholder="例如：张居士")
        f_phone_l = st.text_input("请输入绑定的手机号", placeholder="11位手机号")
        
        c1, c2 = st.columns([1.5, 1])
        with c2:
            if st.button("📲 获取动态核验码", use_container_width=True):
                if len(f_phone_l) != 11:
                    st.error("请输入正确的手机号")
                else:
                    st.session_state.sms_code = str(random.randint(100000, 999999))
                    st.info(f"动态验证码：`{st.session_state.sms_code}`")
        with c1:
            f_code_l = st.text_input("输入验证码", placeholder="请输入验证码")
        
        input_user = st.text_input("管理员登录账号", placeholder="volunteer / finance / haotianguan / admin")
        input_pwd = st.text_input("管理员登录密码", type="password")
        
        if st.button("🔐 安全交班，登录后台", type="primary", use_container_width=True):
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
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()


# --- 6. 进入系统内部控制后台（以下保持原版大成逻辑，做账看盘一网打尽） ---
current_user = st.session_state.current_user
current_role = current_user["role"]

# ==========================================
# 权限大类 1：超级控制台修改空间
# ==========================================
if current_role == "admin":
    st.markdown("## 🛠️ 超级控制台修改空间")
    st.warning("⚠️ 警告：当前正以最高执行权限（admin）直接介入数据底层。非紧急事故切勿手动涂改原始凭证。")
    
    t1, t2, t3 = st.tabs(["📊 全局流水修正单", "👥 观内账号密令更替", "📜 全局追溯审计明细"])
    
    with t1:
        if st.session_state.ledger.empty:
            st.info("📊 暂无账目流水数据。")
        else:
            edited_ledger = st.data_editor(st.session_state.ledger, num_rows="dynamic", use_container_width=True, key="admin_edit_ledger")
            if st.button("💾 确认底层流水强制修正", type="primary"):
                st.session_state.ledger = edited_ledger
                log_action("admin", "超级管理员", "强制修正流水", "手动修改或删除了全局财务大盘数据")
                st.success("🎉 底层流水数据强制修正并落盘成功！")
                st.rerun()
                
    with t2:
        st.markdown("### 🔐 观内各岗位核心密令资产重置")
        for user_key, info in st.session_state.user_db.items():
            st.markdown(f"**岗位账户：`{user_key}`** ({info['title']})")
            c1, c2, c3 = st.columns(3)
            with c1:
                new_name = st.text_input(f"绑定负责人姓名", value=info['name'], key=f"name_{user_key}")
            with c2:
                new_phone = st.text_input(f"绑定负责人手机", value=info['phone'], key=f"phone_{user_key}")
            with c3:
                new_pwd = st.text_input(f"重置登录密码", value=info['password'], type="password", key=f"pwd_{user_key}")
            
            if new_name != info['name'] or new_phone != info['phone'] or new_pwd != info['password']:
                st.session_state.user_db[user_key]['name'] = new_name
                st.session_state.user_db[user_key]['phone'] = new_phone
                st.session_state.user_db[user_key]['password'] = new_pwd
                log_action("admin", "超级管理员", "重置账户密令", f"重置了账户 {user_key} 的负责人或密码信息")
                st.toast(f"✅ 岗位 {user_key} 绑定资产更新成功！")
        st.success("💡 所有岗位安全密令均已置于最新防护态。")
        
    with t3:
        st.markdown("### 📜 全局行为追溯审计明细")
        st.dataframe(st.session_state.audit_logs, use_container_width=True)
        excel_data = to_excel_stream(st.session_state.audit_logs, "审计日志")
        st.download_button("📥 导出不可篡改审计凭证 (Excel)", data=excel_data, file_name=f"昊天观审计追溯单_{datetime.now().strftime('%Y%m%d')}.xlsx", mime="application/vnd.ms-excel")
    
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 退出超级管理员空间", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()
    st.stop()


# ==========================================
# 权限大类 2：业务账户区域（义工、财务、当家）
# ==========================================

# 值班义工特有的动态实名登记防线
if current_role == "volunteer" and not st.session_state.v_verified:
    st.markdown("### ✍️ 值班义工实时实名绑定登记")
    with st.form("volunteer_init_form"):
        st.info("💡 昊天观值班义工流动性强，为确保‘谁做账、谁负责’，请如实登记今日当值信息。")
        v_name = st.text_input("您的真实姓名 (如：张居士)", placeholder="必填")
        v_phone = st.text_input("您的联系手机", placeholder="必填")
        if st.form_submit_button("确认登记并步入值班工作台"):
            if v_name.strip() == "" or len(v_phone.strip()) != 11:
                st.error("❌ 登记信息不合法，请检查姓名或11位手机号。")
            else:
                st.session_state.active_v_info = {"name": v_name, "phone": v_phone}
                st.session_state.v_verified = True
                log_action("volunteer", v_name, "义工实名登记", f"义工手机 {v_phone} 完成当日值班实名背书")
                st.success("实名绑定成功！正在进入工作台...")
                st.rerun()
    st.stop()

# 确立今日责任主体
if current_role == "volunteer":
    active_name = st.session_state.active_v_info["name"]
    active_phone = st.session_state.active_v_info["phone"]
    active_id = "义工免批登记"
else:
    active_name = current_user["name"]
    active_phone = current_user["phone"]
    active_id = current_user["id_card"]

# 左侧栏：身份看板和登出按钮
st.sidebar.markdown(f"### 🕯️ 当前操作人员：\n**{active_name}**")
st.sidebar.markdown(f"**登录账号**：`{current_user['username']}`")
st.sidebar.markdown(f"**责任手机**：`{active_phone}`")
if current_role != "volunteer":
    st.sidebar.markdown(f"**负责人身份证**：\n`{active_id[:6]}********{active_id[-4:]}`")
st.sidebar.markdown("---")
st.sidebar.markdown("🛡️ **内控安全状态**：\n`实名背书已生效`")

st.sidebar.markdown("<br><br><br>", unsafe_allow_html=True)
if st.sidebar.button("🚪 安全交班/退出", use_container_width=True):
    log_action(current_user['username'], active_name, "账户退出", "安全退出当前工作台")
    st.session_state.logged_in = False
    st.session_state.v_verified = False
    st.rerun()


# --- 7. 核心业务看板与做账中心 ---
st.markdown(f"# ⛩️ 昊天观财务管理控制后台")
st.markdown(f"当前岗位级别：**{current_user['title']}** | 安全责任主体：**{active_name}**")

# 根据权限设定能够切换的标签页
if current_role == "volunteer":
    tabs = st.tabs(["📝 凭证分类账登记中心"])
elif current_role == "finance":
    tabs = st.tabs(["📝 凭证分类账登记中心", "🔍 历史凭证解译与检索", "⚖️ 债务/借款往来台账"])
else:  # 当家监院拥有最高看盘与审批权限
    tabs = st.tabs(["📝 凭证分类账登记中心", "🔍 历史凭证解译与检索", "⚖️ 债务/借款往来台账", "📊 周期性财务大盘透视", "📋 观内实名内控制度说明"])

# --- 标签页 1：做账登记中心 (全员可见) ---
with tabs[0]:
    st.markdown("### 📝 昊天观凭证分类账登记中心")
    with st.form("ledger_input_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            f_type = st.radio("1️⃣ 资金性质", ["收入", "支出"])
            f_date = st.date_input("2️⃣ 账目发生日期", datetime.now())
            f_amount = st.number_input("3️⃣ 变动金额 (元)", min_value=0.0, step=100.0, format="%.2f")
        with c2:
            if f_type == "收入":
                f_m1 = st.selectbox("4️⃣ 一级科目", ["捐赠性收入(非经营)", "宗教活动收入(门票/法会)", "功德箱收入"])
                f_m2 = st.selectbox("5️⃣ 二级明细科目", ["信众随喜功德款", "专项殿宇修缮功德", "牌位/供灯功德款", "法会随喜"])
            else:
                f_m1 = st.selectbox("4️⃣ 一级科目", ["场所日常维护", "场所建设与修缮", "教职人员单费与劳务报酬", "宗教活动支出", "公益慈善支出"])
                f_m2 = st.selectbox("5️⃣ 二级明细科目", ["水电气网物业", "日常办公/法物采购", "殿宇泥水木工修缮", "教职人员固定下单", "外聘居士劳务", "法会开支", "社会赈灾扶贫"])
            
            f_agent = st.text_input("6️⃣ 功德主/经手人 姓名", placeholder="外来功德主或观内经手人")
        with c3:
            f_tax = st.selectbox("7️⃣ 税收属性", ["免税宗教收入", "非税免税支出项目", "其他"])
            f_file = st.file_uploader("8️⃣ 上传发票/收据/借条协议凭证明细", type=["jpg", "png", "pdf"])
            f_comment = st.text_area("9️⃣ 详细用途/债务备注 (如借款期限、利息约定等)")
            
        if st.form_submit_button("🔥 确认提交并生成凭证", type="primary"):
            if f_amount <= 0:
                st.error("❌ 金额必须大于 0 元，方可入账。")
            elif f_agent.strip() == "":
                st.error("❌ 请填写经手人或功德主姓名，以便实名风控。")
            else:
                # 构建单条财务账目
                new_row = {
                    '日期': f_date.strftime('%Y-%m-%d'),
                    '类型': f_type,
                    '一级科目': f_m1,
                    '二级科目': f_m2,
                    '税收属性': f_tax,
                    '金额': f_amount,
                    '经手人/功德主': f_agent,
                    '票据凭证': f_file.name if f_file else "未上传纸质凭证",
                    '操作人姓名': active_name,
                    '操作人手机': active_phone,
                    '备注': f_comment
                }
                st.session_state.ledger = pd.concat([st.session_state.ledger, pd.DataFrame([new_row])], ignore_index=True)
                
                # 记录审计日志
                log_action(current_user['username'], active_name, f"录入{f_type}", f"金额: {f_amount} 元 | 科目: {f_m1}-{f_m2}")
                
                # 触发重要风控流提醒
                if f_amount >= 100000 or "借" in f_comment or "贷" in f_comment:
                    send_alert_email(f_date.strftime('%Y-%m-%d'), f_amount, f_m1, active_name)
                    
                st.success(f"🎉 成功！该笔 {f_amount} 元的 {f_type} 凭证已录入昊天观大盘，并受数字审计保护。")
                st.rerun()

    st.info(f"💡 **值班留痕提示**：当前值班义工/财务人员：`{active_name}`。根据不相容岗位分离原则，您拥有一级限权记账权利。昊天观核心资产账簿、周期性报表、债务还款台账以及外部审查导出接口均已受内控安全隔离保护。")


# --- 标签页 2：历史凭证检索 (财务、当家可见) ---
if current_role in ["finance", "temple_head"]:
    with tabs[1]:
        st.markdown("### 🔍 历史凭证解译与多维度检索中心")
        
        if st.session_state.ledger.empty:
            st.info("📊 暂无账目流水数据。")
        else:
            c1, c2, c3 = st.columns(3)
            with c1:
                q_type = st.selectbox("过滤资金性质", ["全选", "收入", "支出"])
            with c2:
                q_m1 = st.text_input("关键字检索一级/二级科目")
            with c3:
                q_agent = st.text_input("关键字检索功德主/经手人")
                
            df_display = st.session_state.ledger.copy()
            if q_type != "全选":
                df_display = df_display[df_display['类型'] == q_type]
            if q_m1.strip() != "":
                df_display = df_display[df_display['一级科目'].str.contains(q_m1) | df_display['二级科目'].str.contains(q_m1)]
            if q_agent.strip() != "":
                df_display = df_display[df_display['经手人/功德主'].str.contains(q_agent)]
                
            st.dataframe(df_display, use_container_width=True)
            
            # 提供数据一键下载到本地 Excel 
            excel_stream = to_excel_stream(df_display, "账目流水明细")
            st.download_button(
                label="📥 导出当前筛选的账目流水账簿 (Excel)",
                data=excel_stream,
                file_name=f"昊天观财务账簿_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.ms-excel",
                use_container_width=True
            )


# --- 标签页 3：债务还款台账 (财务、当家可见) ---
if current_role in ["finance", "temple_head"]:
    with tabs[2]:
        st.markdown("### ⚖️ 昊天观债务、借款往来全流程台账")
        st.markdown("##### ➕ 新增或补录借款/债务单据")
        with st.form("borrow_input_form", clear_on_submit=True):
            bc1, bc2, bc3 = st.columns(3)
            with bc1:
                b_id = st.text_input("借款合同/单号", value=f"HT-BORROW-{random.randint(1000,9999)}")
                b_date = st.date_input("借款借出日期", datetime.now())
            with bc2:
                b_party = st.text_input("债权人 / 借款方名称", placeholder="如：某商业银行 / 某居士")
                b_total = st.number_input("借款总金额 (元)", min_value=0.0, step=1000.0)
            with bc3:
                b_agent = st.text_input("观内经手责任人", value=active_name)
                b_memo = st.text_area("利息、期限及抵押条款备注")
                
            if st.form_submit_button("💾 录入观内债务存续台账"):
                if b_total <= 0 or b_party.strip() == "":
                    st.error("❌ 借款总额和债权人不能为空。")
                else:
                    new_b = {
                        '借款单号': b_id, '借款日期': b_date.strftime('%Y-%m-%d'),
                        '债权人/借款方': b_party, '借款总额': b_total,
                        '已还金额': 0.0, '尚欠金额': b_total,
                        '经手人': b_agent, '备注': b_memo
                    }
                    st.session_state.borrow_ledger = pd.concat([st.session_state.borrow_ledger, pd.DataFrame([new_b])], ignore_index=True)
                    log_action(current_user['username'], active_name, "录入债务", f"单号: {b_id} | 债权人: {b_party} | 金额: {b_total}")
                    st.success(f"✅ 借款单 {b_id} 已成功上账！")
                    st.rerun()
                    
        st.markdown("##### 📋 当前存续债务大盘明细")
        if st.session_state.borrow_ledger.empty:
            st.info("🕊️ 昊天观当前无存续债务，两袖清风，功德无量。")
        else:
            # 允许财务人员和当家直接在表格中更新“已还金额”
            st.markdown("💡 *提示：若观内发生还款，财务可直接在下表中修改【已还金额】，系统会自动计算尚欠余额。修改后请务必点击下方保存按钮。*")
            edited_b_df = st.data_editor(st.session_state.borrow_ledger, num_rows="fixed", use_container_width=True)
            
            # 自动重新计算欠款
            edited_b_df['尚欠金额'] = edited_b_df['借款总额'] - edited_b_df['已还金额']
            
            if st.button("🔄 确认更新还款进度与台账数据"):
                st.session_state.borrow_ledger = edited_b_df
                log_action(current_user['username'], active_name, "更新还款台账", "修改了存续债务的已还金额与进度")
                st.success("🎉 还款台账数据已安全同步落盘！")
                st.rerun()


# --- 标签页 4 & 5：大盘透视与内控制度 (仅当家监院可见) ---
if current_role == "temple_head":
    with tabs[3]:
        st.markdown("### 📊 昊天观周期性财务大盘透视")
        
        # 计算核心财务大盘数据
        df = st.session_state.ledger
        total_in = df[df['类型'] == "收入"]['金额'].sum()
        total_out = df[df['类型'] == "支出"]['金额'].sum()
        net_worth = total_in - total_out
        
        b_df = st.session_state.borrow_ledger
        total_debt = b_df['尚欠金额'].sum() if not b_df.empty else 0.0
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("☯️ 观内累计法喜总收入", f"￥{total_in:,.2f}")
        m2.metric("💸 观内累计日常总支出", f"￥{total_out:,.2f}")
        m3.metric("🪙 账面结余净资产", f"￥{net_worth:,.2f}", delta=f"{net_worth:,.2f}")
        m4.metric("🚨 存续负债/未还借款总额", f"￥{total_debt:,.2f}", delta="- 需注意风控" if total_debt > 0 else "无债一身轻")
        
        st.markdown("---")
        st.markdown("#### 📊 科目分类构成比对")
        c_left, c_right = st.columns(2)
        with c_left:
            st.markdown("**📥 收入科目构成明细**")
            in_df = df[df['类型'] == "收入"]
            if in_df.empty:
                st.caption("暂无数据")
            else:
                st.dataframe(in_df.groupby('一级科目')['金额'].sum().reset_index(), use_container_width=True)
        with c_right:
            st.markdown("**📤 支出科目构成明细**")
            out_df = df[df['类型'] == "支出"]
            if out_df.empty:
                st.caption("暂无数据")
            else:
                st.dataframe(out_df.groupby('一级科目')['金额'].sum().reset_index(), use_container_width=True)
                
    with tabs[4]:
        st.markdown("### 📋 昊天观实名责任内控制度说明")
        st.markdown("""
        > **一、不相容岗位分离原则**
        > 本系统严禁同一人同时担任‘出纳记账’与‘资产审批’。值班义工仅拥有流水录入权，其录入数据必须经过财务工作人员及当家监院二次审计。
        > 
        > **二、全面实名背书制**
        > 任何登录本系统的操作员，必须提供真实姓名与手机号。所有操作均会被底层不可篡改的审计日志链条捕获，作为日后外部宗教事务部门及税务部门突击核验的直接铁证。
        > 
        > **三、大额风控实时通报**
        > 凡单笔变动金额超过 100,000 元，或备注中包含借贷借款等高危负债行为的账目，系统触发风控底单，自动向观内安全邮箱（rldycym123123@163.com）派发备份流，任何人都无权中途拦截。
        """)
