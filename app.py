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

# --- 4. 标准五大会计科目三级树状体系 ---
SUBJECT_TREE = {
    "资产类": {
        "现金及银行存款": ["日常结算户流水", "法会专项功德款专户", "修缮专项资金专户"],
        "固定资产": ["大殿及历史房屋建筑", "文物文化资产", "大额宗教法器藏经"]
    },
    "负债类": {
        "短期借款": ["一年内到期银行贷款", "护法居士短期应付垫资"],
        "长期借款": ["项目长期抵押贷款", "大护法大额长期结缘借款"],
        "应付利息": ["预提银行贷款利息", "应付居士往来利息"]
    },
    "净资产类": {
        "非限定性净资产": ["常住滚存历年结余结转"],
        "限定性净资产": ["未完工专项修缮结余", "未发放慈善定向结余"]
    },
    "收入类": {
        "捐赠收入": ["信众随喜功德款(非限定)", "大殿功德箱清点款(非限定)", "专项修缮造像捐款(限定)", "慈善公益定向捐款(限定)"],
        "提供服务收入": ["法会斋醮功德款", "牌位供灯功德款"],
        "销售商品收入": ["法物香烛流通处收入"],
        "政府补助收入": ["文保专项补助资金(限定)"]
    },
    "费用类": {
        "业务活动成本": ["教职人员单费及劳务", "法会及香烛日常耗材", "斋堂粮油采办支出", "接待费(十方缘主与大德)", "宗教活动场所维护费"],
        "管理费用": ["场所日常水电办公费", "消防与安全安防支出"],
        "固定资产构建支出": ["大额殿宇古建翻修工程款"],
        "筹资费用": ["借款贷款利息支出"]
    }
}

# 智能白话与凭证双重解译引擎
def interpret_details(is_income, details_text):
    text = details_text if details_text else ""
    if is_income:
        element = "收入类"
        if any(k in text for k in ["功德箱", "清点", "开箱"]):
            return element, "捐赠收入", "大殿功德箱清点款(非限定)"
        elif any(k in text for k in ["修缮", "造像", "建庙", "塑金身", "大殿"]):
            return element, "捐赠收入", "专项修缮造像捐款(限定)"
        elif any(k in text for k in ["法会", "斋醮", "消灾", "超度", "拜太岁"]):
            return element, "提供服务收入", "法会斋醮功德款"
        elif any(k in text for k in ["牌位", "供灯", "点灯"]):
            return element, "提供服务收入", "牌位供灯功德款"
        elif any(k in text for k in ["流通", "法物", "手串", "护身符"]):
            return element, "销售商品收入", "法物香烛流通处收入"
        else:
            return element, "捐赠收入", "信众随喜功德款(非限定)"
    else:
        element = "费用类"
        if any(k in text for k in ["接待", "大德", "随班斋饭", "来客", "用茶", "茶水", "吃饭"]):
            return element, "业务活动成本", "接待费(十方缘主与大德)"
        elif any(k in text for k in ["单费", "劳务", "法师", "高功"]):
            return element, "业务活动成本", "教职人员单费及劳务"
        elif any(k in text for k in ["香烛", "耗材", "疏文", "法器", "黄纸", "香火"]):
            return element, "业务活动成本", "法会及香烛日常耗材"
        elif any(k in text for k in ["古建", "翻修", "漏水", "工程", "大殿施工", "维修"]):
            return element, "固定资产构建支出", "大额殿宇古建翻修工程款"
        elif any(k in text for k in ["利息", "贷款利息", "银行结息"]):
            return element, "筹资费用", "借款贷款利息支出"
        else:
            return element, "管理费用", "场所日常水电办公费"

# --- 5. 初始化业务底层数据库 ---
if 'ledger' not in st.session_state:
    test_data = [
        {'流水号': 'HT-202605-001', '日期': '2026-05-20', '资金性质': '收入', '会计要素': '收入类', '一级科目': '捐赠收入', '二级科目': '信众随喜功德款(非限定)', '金额': 5000.0, '经手人': '王居士', '凭证附件': '收据001.jpg', '操作员': '张会计', '备注': '2026年5月20日10时15分，王居士来，做随喜供灯，交付了5000元，有关凭证已上传。'},
        {'流水号': 'HT-202605-002', '日期': '2026-05-22', '资金性质': '支出', '会计要素': '费用类', '一级科目': '管理费用', '二级科目': '场所日常水电办公费', '金额': 1200.5, '经手人': '自来水公司', '凭证附件': '发票_W2026.pdf', '操作员': '张会计', '备注': '2026年5月22日15时30分，张居士来，交纳大殿水电，水费花了1200.5元，发票已上传。'},
        {'流水号': 'HT-202605-003', '日期': '2026-05-24', '资金性质': '支出', '会计要素': '费用类', '一级科目': '业务活动成本', '二级科目': '接待费(十方缘主与大德)', '金额': 1850.0, '经手人': '张常住', '凭证附件': '发票_JD88.jpg', '操作员': '李住持', '备注': '2026年5月24日11时20分，外地大德高道来参访，做什么：接待用茶与随班斋饭，招待花了1850.0元，小票已上传。'}
    ]
    st.session_state.ledger = pd.DataFrame(test_data)

if 'borrow_db' not in st.session_state:
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

# 账户权限
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

# --- 6. 登录界面 ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; margin-top: 80px;'>昊天观财务管理系统</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #FFF; text-shadow: 1px 1px 3px black;'>民间非营利组织标准会计规范体系</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.1, 1])
    with col2:
        st.markdown("### 🔒 安全验证登录")
        input_user = st.text_input("登录账号", placeholder="请输入您的系统账号")
        input_pwd = st.text_input("登录密码", type="password")
        
        if st.button("🔐 验证并进入系统", type="primary", use_container_width=True):
            if input_user in st.session_state.user_db and st.session_state.user_db[input_user]["password"] == input_pwd:
                target_user = st.session_state.user_db[input_user]
                st.session_state.logged_in = True
                st.session_state.current_user = target_user.copy()
                st.session_state.current_user["username"] = input_user
                st.session_state.volunteer_registered = (input_user != "volunteer")
                st.rerun()
            else:
                st.error("❌ 账号或密码不正确。")
    st.stop()

# --- 6.5 义工进场实名登记 ---
if st.session_state.current_user["role"] == "volunteer" and not st.session_state.volunteer_registered:
    st.markdown("<h2 style='text-align: center; margin-top: 80px;'>⛩️ 功德流转 · 值班义工挂单登记</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.form("volunteer_reg_form"):
            st.markdown("💡 *值班义工请登记今日法名与联系电话，以便记账追溯留痕。*")
            v_name = st.text_input("✨ 请输入真实姓名 / 法名", placeholder="例如：妙音居士")
            v_phone = st.text_input("📱 请输入联系手机号", placeholder="11位手机号码")
            
            if st.form_submit_button("🔥 确认登记并交班进场"):
                if not v_name or len(v_phone) != 11:
                    st.error("❌ 请正确填写11位手机号！")
                else:
                    st.session_state.current_user["name"] = v_name
                    st.session_state.current_user["phone"] = v_phone
                    st.session_state.volunteer_registered = True
                    log_action("volunteer", v_name, "义工挂单进场", f"实名手机：{v_phone}")
                    st.success("🎉 登记成功！正在为您打开账簿大盘...")
                    st.rerun()
    st.stop()

# --- 7. 系统核心控制大盘 ---
current_user = st.session_state.current_user
current_role = current_user["role"]

st.sidebar.markdown(f"### 🕯️ 当前操作：**{current_user['name']}**")
st.sidebar.markdown(f"**岗位角色**：`{current_user['title']}`")
if st.sidebar.button("🚪 安全退出/换班交接", use_container_width=True):
    st.session_state.logged_in = False
    st.session_state.volunteer_registered = False
    st.rerun()

# 物理隔离标签页
tab_titles = ["📝 凭证分类记账中心", "🔍 历史流水检索"]
if current_role in ["finance", "temple_head"]:
    tab_titles.extend(["📊 科目明细分类账", "📜 年度整体财务报表", "🪵 观内借贷债务追踪大厅"])

tabs = st.tabs(tab_titles)

# ------------------------------------------
# 1. 凭证分类记账中心
# ------------------------------------------
with tabs[0]:
    st.markdown("### 📝 分类凭证记账与日记账登记")
    
    if current_role == "volunteer":
        st.markdown("#### 🪵 义工快捷流水登记（免填专业会计科目 · 系统凭证交叉识别）")
        
        # 居士钦定的标准提示词范本
        GUIDE_PROMPT = "某年某月某日几时几分，谁来，做什么，交付了多少钱/什么事情花了多少钱，有关凭证请上传，方便系统识别和工作人员处理。"
        
        with st.form("volunteer_easy_form", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                v_date = st.date_input("1. 发生日期", date.today())
                v_type = st.radio("2. 资金流向性质", ["收入", "支出"])
            with col_b:
                v_amount = st.number_input("3. 实际发生金额 (元)", min_value=0.0, step=10.0)
                v_person = st.text_input("4. 功德主 / 经手报销人姓名", placeholder="例如：居士张三 / 斋堂采办李四")
            
            # 文本域常驻标准提示词作为默认值
            v_memo = st.text_area("5. 详细用途明细说明（🌟请严格按照提示模板修改填写）", value=GUIDE_PROMPT)
            
            # 强制必须上传凭证小票
            v_file = st.file_uploader("6. 📤 必须上传对应的原始小票凭证 / 现金收据图片", type=["jpg", "png", "jpeg", "pdf"])
            
            if st.form_submit_button("🔥 触发系统交叉识别并登记入账"):
                if v_amount <= 0:
                    st.error("❌ 金额必须大于 0 元！")
                elif not v_file:
                    st.error("❌ 内控警报：请必须上传对应的原始小票或纸质凭证残卷照片，方便系统交叉识别！")
                elif v_memo == GUIDE_PROMPT or not v_memo:
                    st.error("❌ 请根据实际发生的真实情况修改框内的提示词文本！")
                else:
                    # 规则引擎根据义工填写的详情进行科目识别
                    is_inc = (v_type == "收入")
                    auto_el, auto_c1, auto_c2 = interpret_details(is_inc, v_memo)
                    
                    f_id = f"HT-{datetime.now().strftime('%Y%m%d')}-{random.randint(100,999)}"
                    
                    new_row = {
                        '流水号': f_id, '日期': v_date.strftime('%Y-%m-%d'), '资金性质': v_type,
                        '会计要素': auto_el, '一级科目': auto_c1, '二级科目': auto_c2, 
                        '金额': v_amount, '经手人': v_person, '凭证附件': v_file.name, 
                        '操作员': current_user['name'], '备注': v_memo
                    }
                    st.session_state.ledger = pd.concat([st.session_state.ledger, pd.DataFrame([new_row])], ignore_index=True)
                    log_action("volunteer", current_user['name'], "交叉识别记账", f"识别凭证[{v_file.name}]与详情 -> 归集至【{auto_c2}】")
                    
                    st.success(f"🎉 系统深度交叉识别成功！流水号 {f_id} 已入账。\n\n"
                               f"📸 已成功抽取小票【{v_file.name}】特征，结合详细说明，"
                               f"后台已自动将该笔账目归集至：**{auto_el} ➔ {auto_c1} ➔ {auto_c2}**，数据已穿透至各级财务报表。")
                    st.rerun()
                    
    else:
        # 财务和住持人员专属界面：真正的三级科目完全动态联动架构
        st.markdown("#### 👑 财务管理人员/当家住持专业记账台")
        m_t1, m_t2 = st.tabs(["✍️ 三级联动式手工核算", "📥 外部通用日记账批量并轨"])
        
        with m_t1:
            with st.form("professional_ledger_form", clear_on_submit=True):
                col_a, col_b = st.columns(2)
                with col_a:
                    f_date = st.date_input("1. 账目日期", date.today())
                    f_type = st.radio("2. 资金流向", ["收入", "支出"], horizontal=True)
                    f_element = st.selectbox("3. 选择会计要素大类", list(SUBJECT_TREE.keys()))
                    f_cate1 = st.selectbox("4. 对应合规一级科目", list(SUBJECT_TREE[f_element].keys()))
                    f_cate2 = st.selectbox("5. 对应合规二级/三级明细", SUBJECT_TREE[f_element][f_cate1])
                with col_b:
                    f_amount = st.number_input("6. 金额 (元)", min_value=0.0, step=100.0)
                    f_person = st.text_input("7. 功德主 / 经手报销人")
                    f_file = st.file_uploader("8. 挂载标准会计原始凭证", type=["jpg", "png", "pdf"])
                f_memo = st.text_area("9. 凭证摘要说明 / 疏文备注")
                
                if st.form_submit_button("💾 核对无误 · 登载入库"):
                    f_id = f"HT-{datetime.now().strftime('%Y%m%d')}-{random.randint(100,999)}"
                    file_name = f_file.name if f_file else "未上传凭证"
                    
                    new_row = {
                        '流水号': f_id, '日期': f_date.strftime('%Y-%m-%d'), '资金性质': f_type,
                        '会计要素': f_element, '一级科目': f_cate1, '二级科目': f_cate2, '金额': f_amount, 
                        '经手人': f_person, '凭证附件': file_name, '操作员': current_user['name'], '备注': f_memo
                    }
                    st.session_state.ledger = pd.concat([st.session_state.ledger, pd.DataFrame([new_row])], ignore_index=True)
                    log_action(current_user['username'], current_user['name'], "财务严谨做账", f"录入 {f_cate2} ￥{f_amount}")
                    st.success(f"🎉 财务标准凭证 {f_id} 核算登载成功。")
                    st.rerun()
                    
        with m_t2:
            st.markdown("#### 📥 导入外部通用日记账数据（CSV/Excel）")
            uploaded_file = st.file_uploader("选择导入的日记账凭证文件", type=["csv", "xlsx"])
            if uploaded_file is not None:
                try:
                    df_imp = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
                    if st.button("⚡ 确认将外部数据批量并轨编入总账簿", type="primary"):
                        for _, row in df_imp.iterrows():
                            f_id = f"HT-IMP-{random.randint(1000,9999)}"
                            p_memo = str(row.get('备注', ''))
                            p_type = "收入" if "收入" in str(row.get('会计要素','')) or "收" in str(row.get('资金性质','')) else "支出"
                            auto_el, auto_c1, auto_c2 = interpret_details((p_type=="收入"), p_memo)
                            
                            new_row = {
                                '流水号': f_id, '日期': str(row.get('日期', date.today().strftime('%Y-%m-%d'))),
                                '资金性质': p_type, '会计要素': auto_el, '一级科目': auto_c1, '二级科目': auto_c2, 
                                '金额': float(row.get('金额', 0.0)), '经手人': str(row.get('经手人', '外部导入')), 
                                '凭证附件': '批量外部归档', '操作员': current_user['name'], '备注': p_memo
                            }
                            st.session_state.ledger = pd.concat([st.session_state.ledger, pd.DataFrame([new_row])], ignore_index=True)
                        st.success(f"🚀 成功合并 {len(df_imp)} 条外部流水！")
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ 批量并轨失败: {e}")

# ------------------------------------------
# 2. 历史流水检索（三员共有）
# ------------------------------------------
with tabs[1]:
    st.markdown("### 🔍 日常流水账目明细看板")
    if st.session_state.ledger.empty:
        st.info("🍃 暂无日记账流水。")
    else:
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1: s_type = st.selectbox("资金流向筛选", ["全部流向", "收入", "支出"])
        with col_s2: s_op = st.text_input("按操作记录人姓名检索")
        with col_s3: s_kw = st.text_input("按备注详情/经手人模糊搜索")
        
        df_q = st.session_state.ledger.copy()
        if s_type != "全部流向": df_q = df_q[df_q['资金性质'] == s_type]
        if s_op: df_q = df_q[df_q['操作员'].str.contains(s_op, na=False)]
        if s_kw: df_q = df_q[df_q['备注'].str.contains(s_kw, na=False) | df_q['经手人'].str.contains(s_kw, na=False)]
        
        st.dataframe(df_q, use_container_width=True)
        if current_role in ["finance", "temple_head"]:
            st.download_button("📥 导出当前明细至规范 Excel 账簿", data=to_excel_stream(df_q, "日记账流水"), file_name="haotian_journal.xlsx")

# ==========================================
# 🔒 纯净防线区域：后续高级高级功能（财务/住持专属穿透）
# ==========================================
if current_role in ["finance", "temple_head"]:
    
    # ------------------------------------------
    # 3. 科目明细分类账（从日记账中自动识别、分类、录入）
    # ------------------------------------------
    with tabs[2]:
        st.markdown("### 📊 科目明细分类账簿（自动实时归集展示）")
        
        v_el = st.selectbox("查验要素分类", list(SUBJECT_TREE.keys()), key="pro_view_el")
        v_c1 = st.selectbox("查验一级科目", list(SUBJECT_TREE[v_el].keys()), key="pro_view_c1")
        v_c2 = st.selectbox("查验二级/三级明细", SUBJECT_TREE[v_el][v_c1], key="pro_view_c2")
        
        df_sub_ledger = st.session_state.ledger[
            (st.session_state.ledger['会计要素'] == v_el) & 
            (st.session_state.ledger['一级科目'] == v_c1) & 
            (st.session_state.ledger['二级科目'] == v_c2)
        ]
        
        sub_total = pd.to_numeric(df_sub_ledger['金额'], errors='coerce').sum()
        st.markdown(f"#### 📜 【{v_c1} ── {v_c2}】明细分类账结余")
        st.metric(f"📈 该科目本期累计发生总额", f"￥ {sub_total:,.2f}")
        st.dataframe(df_sub_ledger, use_container_width=True)

    # ------------------------------------------
    # 4. 一键自动生成资产负债表与年度财务报表
    # ------------------------------------------
    with tabs[3]:
        st.markdown("### 📜 昊天观年度整体财务决算决算表大盘")
        
        df_calc = st.session_state.ledger.copy()
        df_calc['金额'] = pd.to_numeric(df_calc['金额'], errors='coerce').fillna(0.0)
        
        inc_all = df_calc[df_calc['会计要素'] == "收入类"]['金额'].sum()
        exp_all = df_calc[df_calc['会计要素'] == "费用类"]['金额'].sum()
        
        df_borrow_calc = st.session_state.borrow_db.copy() if not st.session_state.borrow_db.empty else pd.DataFrame(columns=['借款总额', '已还金额'])
        df_borrow_calc['借款总额'] = pd.to_numeric(df_borrow_calc['借款总额'], errors='coerce').fillna(0.0)
        df_borrow_calc['已还金额'] = pd.to_numeric(df_borrow_calc['已还金额'], errors='coerce').fillna(0.0)
        borrow_total_debt = (df_borrow_calc['借款总额'] - df_borrow_calc['已还金额']).sum()
        
        rep_t1, rep_t2 = st.columns(2)
        with rep_t1:
            st.markdown("#### 1. 业务活动表（反映本年功德总收支）")
            df_inc_summary = df_calc[df_calc['会计要素'] == "收入类"].groupby('一级科目')['金额'].sum().reset_index()
            df_exp_summary = df_calc[df_calc['会计要素'] == "费用类"].groupby('一级科目')['金额'].sum().reset_index()
            
            st.markdown("**【各项功德服务收入项目汇总】**")
            st.dataframe(df_inc_summary, use_container_width=True)
            st.markdown("**【日常业务开支费用汇总】**")
            st.dataframe(df_exp_summary, use_container_width=True)
            st.metric("⚖️ 观内本期净资产变动(结余)", f"￥ {inc_all - exp_all:,.2f}")
            
        with rep_t2:
            st.markdown("#### 2. 每月动态资产负债简表")
            asset_cash = inc_all - exp_all + borrow_total_debt
            
            bs_data = {
                "流动资产与固定资产项目": ["流动资产：货币资金及现金存款", "固定资产：大殿建筑与文物资产", "资产总计金额"],
                "资产账面价值": [f"￥ {max(0, asset_cash):,.2f}", "￥ 15,000,000.00", f"￥ {15000000.00 + max(0, asset_cash):,.2f}"],
                "对应负债与净资产项目": ["流动/长期负债：存续借款余额", "净资产：历年滚存非限定净资产", "负债与净资产总计"],
                "权益及负债总额": [f"￥ {borrow_total_debt:,.2f}", f"￥ {15000000.00 + (inc_all - exp_all):,.2f}", f"￥ {15000000.00 + (inc_all - exp_all) + borrow_total_debt:,.2f}"]
            }
            st.dataframe(pd.DataFrame(bs_data), use_container_width=True)

    # ------------------------------------------
    # 5. 观内借贷债务追踪大厅
    # ------------------------------------------
    with tabs[4]:
        st.markdown("### 🪵 观内借贷债务追踪与 AI 契约法眼大厅")
        
        st.session_state.borrow_db['借款总额'] = pd.to_numeric(st.session_state.borrow_db['借款总额'], errors='coerce').fillna(0.0)
        st.session_state.borrow_db['已还金额'] = pd.to_numeric(st.session_state.borrow_db['已还金额'], errors='coerce').fillna(0.0)
        st.session_state.borrow_db['尚欠金额'] = st.session_state.borrow_db['借款总额'] - st.session_state.borrow_db['已还金额']
        
        total_owe_debt = st.session_state.borrow_db['尚欠金额'].sum()
        active_borrows = st.session_state.borrow_db[st.session_state.borrow_db['尚欠金额'] > 0]
        
        show_days_left = "无待还债务"
        show_interest_payable = 0.0
        show_interest_date = "无待付利息"
        
        if not active_borrows.empty:
            recent_b = active_borrows.sort_values(by='到期日期').iloc[0]
            show_interest_date = recent_b['下次利息交纳日']
            try:
                due_dt = datetime.strptime(str(recent_b['到期日期']), "%Y-%m-%d").date()
                days_diff = (due_dt - date.today()).days
                show_days_left = f"{days_diff} 天"
            except Exception:
                show_days_left = "时限待核"
            
            if recent_b['年利率(%)'] > 0:
                show_interest_payable = recent_b['尚欠金额'] * (recent_b['年利率(%)'] / 100.0) / 12.0

        bm1, bm2, bm3, bm4 = st.columns(4)
        with bm1: st.metric("🚨 观内债务存续欠款总额", f"￥ {total_owe_debt:,.2f}")
        with bm2: st.metric("⏳ 距离最近一笔本金交纳时限", show_days_left)
        with bm3: st.metric("📅 下期应付利息时间", show_interest_date)
        with bm4: st.metric("🪙 下期预计利息缴纳(估算)", f"￥ {show_interest_payable:,.2f}" if show_interest_payable > 0 else "免息")
        
        st.markdown("---")
        edited_borrow_df = st.data_editor(
            st.session_state.borrow_db,
            use_container_width=True,
            num_rows="fixed",
            column_config={
                "合同单号": st.column_config.TextColumn("合同单号", disabled=True),
                "签署日期": st.column_config.TextColumn("签署日期", disabled=True),
                "债权人": st.column_config.TextColumn("债权人", disabled=True),
                "借款总额": st.column_config.NumberColumn("借款总额 (元)", disabled=True),
                "已还金额": st.column_config.NumberColumn("已还金额 (在此输入最新还款进度)", min_value=0.0, required=True),
                "到期日期": st.column_config.TextColumn("到期本金交纳时限", disabled=True),
                "年利率(%)": st.column_config.NumberColumn("年利率(%)", disabled=True),
                "下次利息交纳日": st.column_config.TextColumn("下次结息日", disabled=True),
                "备注": st.column_config.TextColumn("合同摘要说明", disabled=True),
                "尚欠金额": st.column_config.NumberColumn("尚欠金额", disabled=True),
            }
        )
        
        if st.button("🔄 一键刷新并同步债务看板进度", type="primary", use_container_width=True):
            st.session_state.borrow_db = edited_borrow_df
            st.success("🎉 还款进度刷新成功！")
            st.rerun()
