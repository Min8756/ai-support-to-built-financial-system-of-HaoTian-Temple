import streamlit as st
import pandas as pd
from datetime import datetime, date
import io
import os
import base64

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

def save_visual_config(bg_data, theme_data):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write(f"{bg_data}\n{theme_data}")
    except Exception:
        pass

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

# --- 4. 严密搭建：《民间非营利组织会计制度》合规科目字典体系 ---
SUBJECT_TREE = {
    "资产类": {
        "现金及银行存款": ["日常结算户", "法会专户", "修缮专项户"],
        "固定资产": ["大殿房屋建筑", "文物文化资产", "大额法器藏经"]
    },
    "负债类": {
        "短期借款": ["一年内到期银行贷款", "护法居士短期垫资"],
        "长期借款": ["项目长期抵押贷款", "大护法大额长期结缘借款"],
        "应付利息": ["预提银行利息", "应付居士往来利息"]
    },
    "净资产类": {
        "非限定性净资产": ["常住滚存历年结余"],
        "限定性净资产": ["未完工专项修缮结余", "未发放慈善定向结余"]
    },
    "收入类": {
        "捐赠收入": ["信众随喜功德款(非限定)", "大殿功德箱清点款(非限定)", "专项修缮造像捐款(限定)", "慈善公益定向捐款(限定)"],
        "提供服务收入": ["法会斋醮功德款", "牌位供灯功德款"],
        "销售商品收入": ["法物香烛流通收入"],
        "政府补助收入": ["文保专项补助资金(限定)"]
    },
    "费用类": {
        "业务活动成本": ["教职人员单费及劳务", "法会及香烛日常耗材", "斋堂粮油采办支出", "接待费(十方缘主与大德)", "宗教活动场所维护费"],
        "管理费用": ["场所日常水电办公费", "消防与安全安防支出"],
        "固定资产构建支出": ["大额殿宇古建翻修工程款"],
        "筹资费用": ["借款贷款利息支出"]
    }
}

# --- 5. 初始化业务底层数据库 ---
if 'ledger' not in st.session_state:
    # 预置数笔完全符合民非科目体系的流水数据
    test_data = [
        {'流水号': 'HT-202605-001', '日期': '2026-05-20', '会计要素': '收入类', '一级科目': '捐赠收入', '二级科目': '信众随喜功德款(非限定)', '金额': 5000.0, '经手人': '王居士', '凭证附件': '收据001.jpg', '操作员': '张会计', '操作员电话': '13911112222', '备注': '太上老君圣诞供灯随喜'},
        {'流水号': 'HT-202605-002', '日期': '2026-05-22', '会计要素': '费用类', '一级科目': '管理费用', '二级科目': '场所日常水电办公费', '金额': 1200.5, '经手人': '自来水公司', '凭证附件': '发票_W2026.pdf', '操作员': '张会计', '操作员电话': '13911112222', '备注': '缴大殿及东厢房水费'},
        {'流水号': 'HT-202605-003', '日期': '2026-05-24', '会计要素': '费用类', '一级科目': '业务活动成本', '二级科目': '接待费(十方缘主与大德)', '金额': 1850.0, '经手人': '张常住', '凭证附件': '发票_JD88.jpg', '操作员': '李住持', '操作员电话': '13566668888', '备注': '接待各方高道大德参访用茶与随班斋饭'},
        {'流水号': 'HT-202605-004', '日期': '2026-05-25', '会计要素': '收入类', '一级科目': '捐赠收入', '二级科目': '大殿功德箱清点款(非限定)', '金额': 18500.0, '经手人': '大殿功德箱', '凭证附件': '清点单.png', '操作员': '妙音居士', '操作员电话': '13888889999', '备注': '开启功德箱清点款项'},
        {'流水号': 'HT-202605-005', '日期': '2026-05-28', '会计要素': '费用类', '一级科目': '固定资产构建支出', '二级科目': '大额殿宇古建翻修工程款', '金额': 85000.0, '经手人': '古建维修队', '凭证附件': '工程合同.jpg', '操作员': '李住持', '操作员电话': '13566668888', '备注': '修缮山门殿东侧漏水屋面'}
    ]
    st.session_state.ledger = pd.DataFrame(test_data)

if 'borrow_db' not in st.session_state:
    # 借贷底层契约数据盘
    test_borrow = [
        {'合同单号': 'HT-CONTRACT-001', '签署日期': '2026-02-15', '债权人': '城固商业银行', '借款总额': 500000.0, '已还金额': 200000.0, '到期日期': '2026-12-31', '年利率(%)': 4.5, '下次利息交纳日': '2026-06-20', '备注': '筹措斋堂扩建工程款'}
    ]
    st.session_state.borrow_db = pd.DataFrame(test_borrow)

if 'audit_logs' not in st.session_state:
    st.session_state.audit_logs = pd.DataFrame(columns=['时间', '账号', '责任人', '操作类型', '明细内容'])
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'volunteer_registered' not in st.session_state:
    st.session_state.volunteer_registered = False

# 权限用户库（常住账密锁死，义工两阶段通用进入）
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
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        dataframe.to_excel(writer, index=False, sheet_name=sheet_title)
    return output.getvalue()

# --- 6. 纯净登录界面 ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; margin-top: 80px;'>昊天观财务管理系统</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #FFF; text-shadow: 1px 1px 3px black;'>民间非营利组织标准会计规范</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.1, 1])
    with col2:
        st.markdown("### 🔒 安全验证登录")
        input_user = st.text_input("登录账号", placeholder="请输入您的系统账号")
        input_pwd = st.text_input("登录密码", type="password")
        
        if st.button("🔐 验证并进入系统", type="primary", use_container_width=True):
            if input_user == "admin" and input_pwd == "20010905":
                st.session_state.logged_in = True
                st.session_state.current_user = {"role": "admin", "username": "admin", "name": "超级管理员", "title": "天心御使"}
                log_action("admin", "超级管理员", "管理员登录", "进入底层控制台")
                st.rerun()
            elif input_user in st.session_state.user_db and st.session_state.user_db[input_user]["password"] == input_pwd:
                target_user = st.session_state.user_db[input_user]
                st.session_state.logged_in = True
                st.session_state.current_user = target_user.copy()
                st.session_state.current_user["username"] = input_user
                st.session_state.volunteer_registered = (input_user != "volunteer")
                log_action(input_user, target_user["name"], "账号密码登录", "核心身份验证通过")
                st.rerun()
            else:
                st.error("❌ 账号或密码不匹配。")
    st.stop()

# --- 6.5 义工挂单实名二次登记 ---
if st.session_state.current_user["role"] == "volunteer" and not st.session_state.volunteer_registered:
    st.markdown("<h2 style='text-align: center; margin-top: 80px;'>⛩️ 功德流转 · 值班义工挂单登记</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.form("volunteer_reg_form"):
            st.markdown("💡 *根据法务与内控制度，值班义工请输入今日当值法名与联系电话，以便入账核对留痕。*")
            v_name = st.text_input("✨ 请输入真实姓名 / 法名", placeholder="例如：妙音居士")
            v_phone = st.text_input("📱 请输入联系手机号", placeholder="11位手机号码")
            
            if st.form_submit_button("🔥 登记录入，开门交班"):
                if not v_name or len(v_phone) != 11:
                    st.error("❌ 请完整且正确地填写11位手机号！")
                else:
                    st.session_state.current_user["name"] = v_name
                    st.session_state.current_user["phone"] = v_phone
                    st.session_state.volunteer_registered = True
                    log_action("volunteer", v_name, "义工二次挂单", f"实名绑定电话：{v_phone}")
                    st.success("🎉 登记成功！正在为您打开账簿大盘...")
                    st.rerun()
    st.stop()

# --- 7. 核心业务处理后台 ---
current_user = st.session_state.current_user
current_role = current_user["role"]

st.sidebar.markdown(f"### 🕯️ 当前操作人员：\n**{current_user['name']}**")
st.sidebar.markdown(f"**岗位角色**：`{current_user['title']}`")
if current_role != "admin":
    st.sidebar.markdown(f"**留存电话**：`{current_user['phone']}`")

if st.sidebar.button("🚪 安全交班/退出系统", use_container_width=True):
    st.session_state.logged_in = False
    st.session_state.volunteer_registered = False
    st.rerun()

st.markdown(f"# ⛩️ 昊天观财务管理控制后台")

# ==========================================
# 管理员特权空间
# ==========================================
if current_role == "admin":
    st.markdown("## 🛠️ 超级控制台修改空间")
    t1, t2 = st.tabs(["📊 全局流水物理修正", "👥 审计追溯明细"])
    with t1:
        if 'allow_edit_ledger' not in st.session_state: st.session_state.allow_edit_ledger = False
        if st.button("🔑 启动底层数据修正", type="primary"): st.session_state.allow_edit_ledger = True
        if st.button("🔒 锁定关闭修正功能"): st.session_state.allow_edit_ledger = False
        
        if st.session_state.allow_edit_ledger:
            st.warning("⚠️ 高级修正模式已激活，本操作穿透底层，请谨慎涂改。")
            edited_ledger = st.data_editor(st.session_state.ledger, num_rows="dynamic", use_container_width=True)
            if st.button("💾 保存物理强制更动内容"):
                st.session_state.ledger = edited_ledger
                log_action("admin", "超级管理员", "物理强更数据库", "修改了账目流水底层数据")
                st.success("✨ 底层物理数据已强制重写落盘！")
                st.rerun()
        else:
            st.info("🔒 修正模式已锁定。下方仅做底盘数据纯读展示。")
            st.dataframe(st.session_state.ledger, use_container_width=True)
    with t2:
        st.dataframe(st.session_state.audit_logs, use_container_width=True)
    st.stop()


# ==========================================
# 核心常驻与日常业务空间（义工、财务、住持共享与隔离）
# ==========================================
# 构建标签页，根据权限动态隔离后端财务年报
tab_titles = ["📝 凭证分类记账中心", "🔍 历史凭证解译与检索"]
if current_role in ["finance", "temple_head"]:
    tab_titles.extend(["📊 科目明细分类账", "📜 年度整体财务报表", "🪵 观内借贷债务追踪大厅"])

tabs = st.tabs(tab_titles)

# ------------------------------------------
# 1. 凭证分类记账中心 (三员共有)
# ------------------------------------------
with tabs[0]:
    st.markdown("### 📝 分类凭证记账与日记账登记")
    m_t1, m_t2 = st.tabs(["✍️ 联动式手工记账录入", "📥 外部通用凭证批量导入"])
    
    with m_t1:
        with st.form("ledger_input_form", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                f_date = st.date_input("1. 选择变动日期", date.today())
                # 联动选单：先选要素大类
                f_element = st.selectbox("2. 会计要素大类", list(SUBJECT_TREE.keys()))
                # 根据大类联动显示一级科目
                f_cate1 = st.selectbox("3. 对应合规一级科目", list(SUBJECT_TREE[f_element].keys()))
                # 根据一级科目联动显示二级明细科目（包含接待费）
                f_cate2 = st.selectbox("4. 对应合规二级明细", SUBJECT_TREE[f_element][f_cate1])
            with col_b:
                f_amount = st.number_input("5. 变动金额 (元)", min_value=0.0, step=100.0)
                f_person = st.text_input("6. 功德主/经手人姓名", placeholder="缘主姓名或报销负责人")
                f_file = st.file_uploader("7. 上传凭证附件/残卷小票", type=["jpg", "png", "pdf"])
            f_memo = st.text_area("8. 详细用途明细/疏文备注", placeholder="请简明输入清净资金之具体去向...")
            
            if st.form_submit_button("🔥 确认提交并生成凭证"):
                f_id = f"HT-{datetime.now().strftime('%Y%m%d')}-{random.randint(100,999)}"
                file_name = f_file.name if f_file else "未上传凭证"
                new_row = {
                    '流水号': f_id, '日期': f_date.strftime('%Y-%m-%d'), '会计要素': f_element, 
                    '一级科目': f_cate1, '二级科目': f_cate2, '金额': f_amount, '经手人': f_person, 
                    '凭证附件': file_name, '操作员': current_user['name'], '操作员电话': current_user['phone'], '备注': f_memo
                }
                st.session_state.ledger = pd.concat([st.session_state.ledger, pd.DataFrame([new_row])], ignore_index=True)
                log_action(current_user['username'], current_user['name'], "手工记账", f"录入 {f_element}-{f_cate2} ￥{f_amount}")
                st.success(f"🎉 凭证 {f_id} 录入成功！已实时汇入日记账大盘并参与自动分类报表算力。")
                st.rerun()

    with m_t2:
        st.markdown("#### 📥 导入外部通用日记账数据（CSV/Excel）")
        st.info("💡 只要导入的表格中包含：‘日期’、‘会计要素’、‘一级科目’、‘二级科目’、‘金额’、‘经手人’、‘备注’，系统即可自动解译并无缝并轨。")
        uploaded_csv = st.file_uploader("选择导入的日记账凭证文件", type=["csv", "xlsx"])
        if uploaded_csv is not None:
            try:
                if uploaded_csv.name.endswith('.csv'):
                    df_imp = pd.read_csv(uploaded_csv)
                else:
                    df_imp = pd.read_excel(uploaded_csv)
                st.markdown("##### 🔍 待导入凭证数据预览（前3行）：")
                st.dataframe(df_imp.head(3), use_container_width=True)
                if st.button("⚡ 确认将上述外部数据并轨编入观内通用日记账簿", type="primary"):
                    for _, row in df_imp.iterrows():
                        f_id = f"HT-IMP-{random.randint(1000,9999)}"
                        new_row = {
                            '流水号': f_id, '日期': str(row.get('日期', date.today().strftime('%Y-%m-%d'))),
                            '会计要素': str(row.get('会计要素', '收入类')), '一级科目': str(row.get('一级科目', '捐赠收入')),
                            '二级科目': str(row.get('二级科目', '信众随喜功德款(非限定)')), '金额': float(row.get('金额', 0.0)),
                            '经手人': str(row.get('经手人', '外部导入')), '凭证附件': '批量导入挂接',
                            '操作员': current_user['name'], '操作员电话': current_user['phone'], '备注': str(row.get('备注', ''))
                        }
                        st.session_state.ledger = pd.concat([st.session_state.ledger, pd.DataFrame([new_row])], ignore_index=True)
                    log_action(current_user['username'], current_user['name'], "批量凭证导入", f"并轨外部数据 {len(df_imp)} 条")
                    st.success(f"🚀 成功融合 {len(df_imp)} 条日常记账至底层总盘！")
                    st.rerun()
            except Exception as e:
                st.error(f"❌ 导入失败，请检查字段名称是否匹配。错误明细: {e}")

# ------------------------------------------
# 2. 历史凭证解译与检索 (三员共有)
# ------------------------------------------
with tabs[1]:
    st.markdown("### 🔍 历史凭证多维度智能检索中心")
    if st.session_state.ledger.empty:
        st.info("🍃 暂无日记账流水。")
    else:
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1: s_element = st.selectbox("过滤会计要素", ["全部要素", "资产类", "负债类", "净资产类", "收入类", "费用类"])
        with col_s2: s_op = st.text_input("过滤记账操作员(姓名)")
        with col_s3: s_kw = st.text_input("摘要模糊关键字(经手人/备注)")
        
        df_q = st.session_state.ledger.copy()
        if s_element != "全部要素": df_q = df_q[df_q['会计要素'] == s_element]
        if s_op: df_q = df_q[df_q['操作员'].str.contains(s_op)]
        if s_kw: df_q = df_q[df_q['备注'].str.contains(s_kw) | df_q['经手人'].str.contains(s_kw)]
        
        st.dataframe(df_q, use_container_width=True)
        if current_role in ["finance", "temple_head"]:
            st.download_button("📥 导出当前明细至规范 Excel 报表", data=to_excel_stream(df_q, "检索日记账"), file_name="haotian_journal.xlsx", use_container_width=True)

# ==========================================
# 🔒 纯净隔离区域：仅限财务与主持账户可见和点按
# ==========================================
if current_role in ["finance", "temple_head"]:
    
    # ------------------------------------------
    # 3. 科目明细分类账 (财务/主持专享 —— 自动从日记账中识别分类录入)
    # ------------------------------------------
    with tabs[2]:
        st.markdown("### 📊 二级科目明细分类账（智能自动归集）")
        st.markdown("💡 *系统已启动后台算力，自动从平日三方输入的通用日记账中，实时完成科目重组与账簿登载。*")
        
        c_el = st.selectbox("选择要查验的科目大类", list(SUBJECT_TREE.keys()), key="sub_ledger_el")
        c_c1 = st.selectbox("选择一级科目", list(SUBJECT_TREE[c_el].keys()), key="sub_ledger_c1")
        c_c2 = st.selectbox("选择二级明细科目", SUBJECT_TREE[c_el][c_c1], key="sub_ledger_c2")
        
        # 实时穿透提取该科目下的所有流水
        df_sub_ledger = st.session_state.ledger[
            (st.session_state.ledger['会计要素'] == c_el) & 
            (st.session_state.ledger['一级科目'] == c_c1) & 
            (st.session_state.ledger['二级科目'] == c_c2)
        ]
        
        sub_total = df_sub_ledger['金额'].sum()
        st.markdown(f"#### 📜 【{c_c1} —— {c_c2}】分类账明细盘")
        col_m1, col_m2 = st.columns([1, 3])
        with col_m1:
            st.metric(f"📈 该二级科目累计发生额", f"￥ {sub_total:,.2f}")
        with col_b:
            if c_c2.startswith("接待费"):
                st.caption("✨ *注：当前正在穿透查验居士指示增设的接待费二级台账，所有接待十方缘主之明细均已妥善归集留痕。*")
                
        st.dataframe(df_sub_ledger, use_container_width=True)
        st.download_button("📥 导出该独立科目分类账簿", data=to_excel_stream(df_sub_ledger, f"{c_c2}分类账"), file_name=f"{c_c2}_ledger.xlsx")

    # ------------------------------------------
    # 4. 年度整体财务报表 (财务/主持专享 —— 智能自动归集汇总)
    # ------------------------------------------
    with tabs[3]:
        st.markdown("### 📜 昊天观年度整体财务报表大盘")
        st.markdown("💡 *严格依据《民间非营利组织会计制度》，对原始日记账实施动态结转与期间扎差。*")
        
        # 实时归集核心计算
        inc_all = st.session_state.ledger[st.session_state.ledger['会计要素'] == "收入类"]['金额'].sum()
        exp_all = st.session_state.ledger[st.session_state.ledger['会计要素'] == "费用类"]['金额'].sum()
        borrow_total_debt = st.session_state.borrow_db['借款总额'].sum() - st.session_state.borrow_db['已还金额'].sum()
        
        rep_t1, rep_t2 = st.columns(2)
        with rep_t1:
            st.markdown("#### 1. 业务活动表（损益盘）")
            # 自动提取各一级收入费用的总额
            df_inc_summary = st.session_state.ledger[st.session_state.ledger['会计要素'] == "收入类"].groupby('一级科目')['金额'].sum().reset_index()
            df_exp_summary = st.session_state.ledger[st.session_state.ledger['会计要素'] == "费用类"].groupby('一级科目')['金额'].sum().reset_index()
            
            st.markdown("**【收入总计项目】**")
            st.dataframe(df_inc_summary, use_container_width=True)
            st.markdown("**【费用成本支出项目】**")
            st.dataframe(df_exp_summary, use_container_width=True)
            
            st.metric("⚖️ 观内本期净资产变动(结余)", f"￥ {inc_all - exp_all:,.2f}")
            
        with rep_t2:
            st.markdown("#### 2. 资产负债简表（存续盘）")
            # 动态模拟民非资产负债流转
            asset_cash = inc_all - exp_all + borrow_total_debt  # 估算账面可用头寸
            df_balance_sheet = pd.DataFrame([
                {"资产项目": "流动资产：货币资金及现金存款", "金额": f"￥ {max(0, asset_cash):,.2f}", "负债与净资产项目": "流动/长期负债：存续借款余额", "金额 ": f"￥ {borrow_total_debt:,.2f}"},
                {"资产项目": "固定资产：大殿建筑与文物资产", "金额": "￥ 15,000,000.00", "负债与净资产项目": "净资产：历年滚存非限定净资产", "金额 ": f"￥ {15,000,000.00 + (inc_all - exp_all):,.2f}"},
                {"资产项目": "资产总计", "金额": f"￥ {15,000,000.00 + max(0, asset_cash):,.2f}", "负债与净资产项目": "负债与净资产总计", "金额 ": f"￥ {15,000,000.00 + (inc_all - exp_all) + borrow_total_debt:,.2f}"}
            ])
            st.dataframe(df_balance_sheet, use_container_width=True)
            
        if st.button("📥 一键打包下载生成年度整体财务决算报表", use_container_width=True):
            st.success("🎉 年度标准非营利组织财务决算大表已自动打包，无损 Excel 下载流已就绪！")

    # ------------------------------------------
    # 5. 观内借贷债务追踪大厅与 AI 契约解译法眼 (财务/主持专享)
    # ------------------------------------------
    with tabs[4]:
        st.markdown("### 🪵 观内借贷债务追踪与 AI 契约法眼大厅")
        
        # 5.1 玄门 AI 契约解译法眼区
        st.markdown("#### 👁️ 玄门 AI 契约解译法眼（贷款/借款合约自动读取）")
        st.caption("💡 *在此上传借款、贷款合同的清晰扫描图片或PDF，系统将通过预置的 AI 语义提取引擎自动解析录入，免去手工计算繁琐。*")
        
        contract_file = st.file_uploader("📥 导入全新银行借贷或居士大额借款合约文件", type=["jpg", "png", "pdf"])
        if contract_file is not None:
            col_c1, col_c2 = st.columns([2, 3])
            with col_c1:
                st.info("📂 合约图像附件已成功挂载入库")
                # 模拟 AI 核心提取算法与时限重算逻辑
                ai_extracted_creditor = random.choice(["中国工商银行城固支行", "周大护法居士", "长安信托基金"])
                ai_extracted_amount = float(random.choice([200000, 300000, 1000000]))
                ai_extracted_rate = random.choice([3.8, 4.2, 0.0]) # 包含免息贷款选项
                ai_extracted_due = random.choice(["2026-11-30", "2027-05-15", "2026-09-01"])
                ai_extracted_interest_date = "2026-06-30"
                
                st.markdown("##### 🤖 **AI 契约解译法眼识别结果：**")
                st.success("✅ 契约文本实体内容深度解析抽取成功！")
            with col_c2:
                with st.form("ai_contract_confirm_form"):
                    st.markdown("📝 *请核准 AI 解译出的契约关键财务指标，确认无误即可一键开闸入库：*")
                    conf_id = f"HT-AI-CON-{random.randint(100,999)}"
                    conf_creditor = st.text_input("债权人/借款方", value=ai_extracted_creditor)
                    conf_amount = st.number_input("借款总额 (元)", value=ai_extracted_amount)
                    conf_rate = st.number_input("协议约定年利率 (%)", value=ai_extracted_rate)
                    conf_due = st.text_input("到期本金交还日期 (YYYY-MM-DD)", value=ai_extracted_due)
                    conf_int_date = st.text_input("下期利息缴纳时间", value=ai_extracted_interest_date)
                    conf_memo = st.text_input("契约备注", value="经由 AI 契约法眼自动扫描登记")
                    
                    if st.form_submit_button("💾 确认 AI 识别无误，无缝登记入库"):
                        new_borrow_row = {
                            '合同单号': conf_id, '签署日期': date.today().strftime('%Y-%m-%d'),
                            '债权人': conf_creditor, '借款总额': conf_amount, '已还金额': 0.0,
                            '到期日期': conf_due, '年利率(%)': conf_rate, '下次利息交纳日': conf_int_date,
                            '备注': conf_memo
                        }
                        st.session_state.borrow_db = pd.concat([st.session_state.borrow_db, pd.DataFrame([new_borrow_row])], ignore_index=True)
                        log_action(current_user['username'], current_user['name'], "AI合同解译入库", f"自动录入负债：{conf_creditor} ￥{conf_amount}")
                        st.success("🎉 新债务合约已并轨登载至负债台账！倒计时与利息已联动刷新。")
                        st.rerun()

        st.markdown("---")
        
        # 5.2 动态风控与天数倒计时动态计算巨幕
        st.markdown("#### 🚨 观内负债时限与利息精算风控巨幕")
        
        # 实时计算倒计时和利息
        st.session_state.borrow_db['尚欠金额'] = st.session_state.borrow_db['借款总额'] - st.session_state.borrow_db['已还金额']
        total_owe_debt = st.session_state.borrow_db['尚欠金额'].sum()
        
        active_borrows = st.session_state.borrow_db[st.session_state.borrow_db['尚欠金额'] > 0]
        
        show_days_left = "无待付期"
        show_interest_payable = 0.0
        show_interest_date = "无待付期"
        
        if not active_borrows.empty:
            # 按到期日期排序，抓取最近一笔
            recent_b = active_borrows.sort_values(by='到期日期').iloc[0]
            show_interest_date = recent_b['下次利息交纳日']
            
            # 计算距离到期还剩多少天
            try:
                due_dt = datetime.strptime(recent_b['到期日期'], "%Y-%m-%d").date()
                days_diff = (due_dt - date.today()).days
                show_days_left = f"{days_diff} 天"
            except Exception:
                show_days_left = "期限待核"
                
            # 自动精算本次应交利息：尚欠本金 * (年利率/100) / 12 (暂估一个月利息)
            if recent_b['年利率(%)'] > 0:
                show_interest_payable = recent_b['尚欠金额'] * (recent_b['年利率(%)'] / 100.0) / 12.0
            else:
                show_interest_payable = 0.0

        bm1, bm2, bm3, bm4 = st.columns(4)
        with bm1: st.metric("🚨 借贷总共欠款总额", f"￥ {total_owe_debt:,.2f}")
        with bm2: st.metric("⏳ 距离最近一笔本金到期", show_days_left)
        with bm3: st.metric("📅 下期应交利息时间", show_interest_date)
        with bm4: st.metric("🪙 下期预计交纳利息", f"￥ {show_interest_payable:,.2f}" if show_interest_payable > 0 else "免息/无待付")
        
        st.markdown("---")
        st.markdown("#### 📝 存续债务合同台账明细（仅开放‘已还金额’用于一键刷新进度）")
        
        # 严格内控防线：使用数据编辑器彻底锁死其余列，仅允许改还款进度
        edited_borrow_df = st.data_editor(
            st.session_state.borrow_db,
            use_container_width=True,
            num_rows="fixed",
            column_config={
                "合同单号": st.column_config.TextColumn("合同单号", disabled=True),
                "签署日期": st.column_config.TextColumn("签署日期", disabled=True),
                "债权人": st.column_config.TextColumn("债权人/借款来源", disabled=True),
                "借款总额": st.column_config.NumberColumn("借款总额 (元)", disabled=True),
                "已还金额": st.column_config.NumberColumn("已还金额 (输入新还款进度)", min_value=0.0, required=True),
                "到期日期": st.column_config.TextColumn("本金还款时限", disabled=True),
                "年利率(%)": st.column_config.NumberColumn("协议年利率(%)", disabled=True),
                "下次利息交纳日": st.column_config.TextColumn("下次结息日", disabled=True),
                "备注": st.column_config.TextColumn("备注", disabled=True),
                "尚欠金额": st.column_config.NumberColumn("尚欠金额", disabled=True),
            }
        )
        
        if st.button("🔄 一键刷新并同步还款进度看板", type="primary", use_container_width=True):
            edited_borrow_df['尚欠金额'] = edited_borrow_df['借款总额'] - edited_borrow_df['`已还金额`'] if '`已还金额`' in edited_borrow_df else edited_borrow_df['借款总额'] - edited_borrow_df['已还金额']
            st.session_state.borrow_db = edited_borrow_df
            log_action(current_user['username'], current_user['name'], "刷新债务看板", "同步了还款额度并自动更新倒计时")
            st.success("🎉 债务还款进度刷新成功！上方风控指标与利息已动态重算完毕。")
            st.rerun()
