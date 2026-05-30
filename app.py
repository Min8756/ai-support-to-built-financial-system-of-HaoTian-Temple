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

# --- 4. 严格按照民间非营利组织与宗教活动场所准则构建的“一、二、三级联动字典” ---
ACCOUNTING_STRUCTURE = {
    "收入类": {
        "捐赠收入": {
            "信众随喜功德款": ["非限定性随喜", "限定性定向款"],
            "修缮专项捐款": ["大殿翻修限定", "神像贴金限定"],
            "大殿功功德箱款": ["日常开箱清点", "法会专项清点"]
        },
        "提供服务收入": {
            "斋醮祈福法务收入": ["日常法事随喜", "大型斋醮功德"],
            "牌位供奉收入": ["延生禄位供奉", "往生莲位供奉"]
        },
        "商品销售收入": {
            "法物结缘收入": ["香烛经书流通", "开光法器手串"]
        }
    },
    "费用类": {
        "业务活动成本": {
            "法务宗教活动支出": ["香烛供品采办", "法器耗材购置", "高功经师单费"],
            "文教与公益慈善": ["弘法布道支出", "十方施斋济贫", "助学奖学功德"],
            "文物保护与修缮": ["殿堂日常修补", "历史文物维护"]
        },
        "管理费用": {
            "场所日常办公费": ["观内水电公杂", "办公用品采购", "通讯网络网络"],
            "道众及人员薪给": ["常住道众补助", "雇员基本薪资"]
        },
        "筹资费用": {
            "借款利息": ["合法垫资利息"],
            "筹资手续费": ["微信支付宝提现手续费"]
        }
    },
    "资产类": {
        "流动资产": {
            "现金及银行存款": ["观内现金结存", "基本结算账户", "专项功德款专户"]
        },
        "固定资产": {
            "大殿建筑与文物资产": ["大殿房屋主体", "配殿及厢房", "历史保护文物"],
            "道教法器专项": ["大型青铜鼎炉", "铸铁悬钟", "大额宗教法器"]
        }
    },
    "负债类": {
        "流动负债": {
            "应付款项": ["应付延期工程款", "应付斋堂粮油款"]
        },
        "长期负债": {
            "长期借款": ["护法居士大额长期借款", "项目长期垫资款"]
        }
    },
    "净资产类": {
        "非限定性净资产": {
            "历年滚存结余": ["常住历年滚存结余"]
        },
        "限定性净资产": {
            "特殊定向结存": ["未完工修缮项目结存", "定向慈善救济结存"]
        }
    }
}

# 智能白话与凭证双重解译引擎（义工端模糊匹配用）
def interpret_details(is_income, details_text):
    text = details_text if details_text else ""
    if is_income:
        el = "收入类"
        if any(k in text for k in ["功德箱", "开箱", "清点"]):
            return el, "捐赠收入", "大殿功功德箱款", "日常开箱清点"
        elif any(k in text for k in ["修缮", "造像", "建庙", "翻修", "大殿施工"]):
            return el, "捐赠收入", "修缮专项捐款", "大殿翻修限定"
        elif any(k in text for k in ["法会", "斋醮", "法事", "超度", "祈福"]):
            return el, "提供服务收入", "斋醮祈福法务收入", "日常法事随喜"
        elif any(k in text for k in ["牌位", "供灯", "点灯"]):
            return el, "提供服务收入", "牌位供奉收入", "延生禄位供奉"
        elif any(k in text for k in ["流通", "法物", "手串", "护身符"]):
            return el, "商品销售收入", "法物结缘收入", "香烛经书流通"
        else:
            return el, "收入类", "捐赠收入", "信众随喜功德款"
    else:
        el = "费用类"
        if any(k in text for k in ["接待", "大德", "客堂", "吃饭", "茶水"]):
            return el, "管理费用", "场所日常办公费", "观内水电公杂"
        elif any(k in text for k in ["单费", "劳务", "法师", "高功"]):
            return el, "业务活动成本", "法务宗教活动支出", "高功经师酬劳"
        elif any(k in text for k in ["香烛", "耗材", "疏文", "黄纸", "香火"]):
            return el, "业务活动成本", "法务宗教活动支出", "香烛供品采办"
        elif any(k in text for k in ["翻修", "漏水", "修缮", "修庙"]):
            return el, "业务活动成本", "文物保护与修缮", "殿堂日常修补"
        elif any(k in text for k in ["利息", "贷款"]):
            return el, "筹资费用", "借款利息", "合法垫资利息"
        else:
            return el, "管理费用", "场所日常办公费", "观内水电公杂"

# --- 5. 初始化业务底层数据库 ---
if 'ledger' not in st.session_state:
    test_data = [
        {'流水号': 'HT-202605-001', '日期': '2026-05-20', '资金性质': '收入', '会计要素': '收入类', '一级科目': '捐赠收入', '二级科目': '信众随喜功德款', '三级科目': '非限定性随喜', '金额': 5000.0, '经手人': '王居士', '凭证附件': '收据001.jpg', '操作员': '张会计', '备注': '2026年5月20日10时15分，王居士来随喜供灯交付5000元。'},
        {'流水号': 'HT-202605-002', '日期': '2026-05-22', '资金性质': '支出', '会计要素': '费用类', '一级科目': '管理费用', '二级科目': '场所日常办公费', '三级科目': '观内水电公杂', '金额': 1200.5, '经手人': '自来水公司', '凭证附件': '发票_W2026.pdf', '操作员': '张会计', '备注': '2026年5月22日15时30分大殿交纳水费1200.5元。'},
        {'流水号': 'HT-202605-003', '日期': '2026-05-24', '资金性质': '支出', '会计要素': '费用类', '一级科目': '业务活动成本', '二级科目': '法务宗教活动支出', '三级科目': '香烛供品采办', '金额': 1850.0, '经手人': '张常住', '凭证附件': '发票_JD88.jpg', '操作员': '李住持', '备注': '2026年5月24日采办斋醮法会香烛黄纸1850元。'}
    ]
    st.session_state.ledger = pd.DataFrame(test_data)

if 'borrow_db' not in st.session_state:
    test_borrow = [
        {'合同单号': 'HT-CONTRACT-001', '签署日期': '2026-02-15', '债权人': '城固商业银行', '借款总额': 500000.0, '已还金额': 200000.0, '到期日期': '2026-12-31', '备注': '筹措斋堂扩建工程款'}
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

# 隔离标签页
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
        st.markdown("#### 🪵 义工快捷流水登记（免填专业会计科目）")
        GUIDE_PROMPT = "某年某月某日几时几分，谁来，做什么，交付了多少钱/什么事情花了多少钱，有关凭证请上传，方便系统识别和工作人员处理。"
        
        with st.form("volunteer_easy_form", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                v_date = st.date_input("1. 发生日期", date.today())
                v_type = st.radio("2. 资金流向性质", ["收入", "支出"])
            with col_b:
                v_amount = st.number_input("3. 实际发生金额 (元)", min_value=0.0, step=10.0)
                v_person = st.text_input("4. 功德主 / 经手报销人姓名")
            
            v_memo = st.text_area("5. 详细用途明细说明（🌟请严格按照提示模板修改填写）", value=GUIDE_PROMPT)
            v_file = st.file_uploader("6. 📤 必须上传对应的原始小票凭证 / 现金收据图片", type=["jpg", "png", "jpeg", "pdf"])
            
            if st.form_submit_button("🔥 触发系统交叉识别并登记入账"):
                if v_amount <= 0: st.error("❌ 金额必须大于 0 元！")
                elif not v_file: st.error("❌ 请上传原始凭证照片！")
                elif v_memo == GUIDE_PROMPT or not v_memo: st.error("❌ 请根据实际发生的真实情况修改框内的提示词文本！")
                else:
                    auto_el, auto_c1, auto_c2, auto_c3 = interpret_details((v_type == "收入"), v_memo)
                    f_id = f"HT-{datetime.now().strftime('%Y%m%d')}-{random.randint(100,999)}"
                    
                    new_row = {
                        '流水号': f_id, '日期': v_date.strftime('%Y-%m-%d'), '资金性质': v_type,
                        '会计要素': auto_el, '一级科目': auto_c1, '二级科目': auto_c2, '三级科目': auto_c3,
                        '金额': v_amount, '经手人': v_person, '凭证附件': v_file.name, 
                        '操作员': current_user['name'], '备注': v_memo
                    }
                    st.session_state.ledger = pd.concat([st.session_state.ledger, pd.DataFrame([new_row])], ignore_index=True)
                    log_action("volunteer", current_user['name'], "交叉识别记账", f"义工录入归集至【{auto_c3}】")
                    st.success(f"🎉 系统自动交叉解析成功！已自动归集至：{auto_el}➔{auto_c1}➔{auto_c2}➔{auto_c3}")
                    st.rerun()
                    
    else:
        st.markdown("#### 👑 财务管理人员/当家住持专业记账台")
        
        with st.form("professional_ledger_form", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                f_date = st.date_input("1. 账目日期", date.today())
                f_type = st.radio("2. 资金流向", ["收入", "支出"], horizontal=True)
                
                # 🔥【核心修复：完美实现全动态级联机制，拒绝混淆资产类】
                selected_el = st.selectbox("3. 选择会计要素大类", list(ACCOUNTING_STRUCTURE.keys()))
                
                level_1_opts = list(ACCOUNTING_STRUCTURE[selected_el].keys())
                selected_c1 = st.selectbox("4. 对应合规一级科目", level_1_opts)
                
                level_2_opts = list(ACCOUNTING_STRUCTURE[selected_el][selected_c1].keys())
                selected_c2 = st.selectbox("5. 对应合规二级科目", level_2_opts)
                
                level_3_opts = ACCOUNTING_STRUCTURE[selected_el][selected_c1][selected_c2]
                selected_c3 = st.selectbox("6. 对应合规三级细目", level_3_opts)
                
            with col_b:
                f_amount = st.number_input("7. 金额 (元)", min_value=0.0, step=100.0)
                f_person = st.text_input("8. 功德主 / 经手报销人")
                f_file = st.file_uploader("9. 挂载标准会计原始凭证", type=["jpg", "png", "pdf"])
            f_memo = st.text_area("10. 凭证摘要说明 / 疏文备注")
            
            if st.form_submit_button("💾 核对无误 · 登载入库"):
                f_id = f"HT-{datetime.now().strftime('%Y%m%d')}-{random.randint(100,999)}"
                file_name = f_file.name if f_file else "未上传凭证"
                
                new_row = {
                    '流水号': f_id, '日期': f_date.strftime('%Y-%m-%d'), '资金性质': f_type,
                    '会计要素': selected_el, '一级科目': selected_c1, '二级科目': selected_c2, '三级科目': selected_c3,
                    '金额': f_amount, '经手人': f_person, '凭证附件': file_name, '操作员': current_user['name'], '备注': f_memo
                }
                st.session_state.ledger = pd.concat([st.session_state.ledger, pd.DataFrame([new_row])], ignore_index=True)
                log_action(current_user['username'], current_user['name'], "财务严谨做账", f"录入 {selected_c3} ￥{f_amount}")
                st.success(f"🎉 财务标准科目凭证 {f_id} 登载成功。")
                st.rerun()

# ------------------------------------------
# 2. 历史流水检索（三员共有）
# ------------------------------------------
with tabs[1]:
    st.markdown("### 🔍 日常流水账目明细看板")
    if st.session_state.ledger.empty:
        st.info("🍃 暂无日记账流水。")
    else:
        st.dataframe(st.session_state.ledger, use_container_width=True)

# ------------------------------------------
# 3. 科目明细分类账
# ------------------------------------------
if current_role in ["finance", "temple_head"]:
    with tabs[2]:
        st.markdown("### 📊 科目明细分类账簿（全联动实时自动归集）")
        v_el = st.selectbox("查验要素分类", list(ACCOUNTING_STRUCTURE.keys()))
        v_c1 = st.selectbox("查验一级科目", list(ACCOUNTING_STRUCTURE[v_el].keys()))
        v_c2 = st.selectbox("查验二级科目", list(ACCOUNTING_STRUCTURE[v_el][v_c1].keys()))
        
        df_sub = st.session_state.ledger[
            (st.session_state.ledger['会计要素'] == v_el) & 
            (st.session_state.ledger['一级科目'] == v_c1) & 
            (st.session_state.ledger['二级科目'] == v_c2)
        ]
        st.metric("📈 该二级科目累计发生金额", f"￥ {pd.to_numeric(df_sub['金额'], errors='coerce').sum():,.2f}")
        st.dataframe(df_sub, use_container_width=True)

    # ------------------------------------------
    # 4. 年度整体财务报表
    # ------------------------------------------
    with tabs[3]:
        st.markdown("### 📜 昊天观年度整体财务决算表大盘")
        df_calc = st.session_state.ledger.copy()
        df_calc['金额'] = pd.to_numeric(df_calc['金额'], errors='coerce').fillna(0.0)
        
        inc_all = df_calc[df_calc['资金性质'] == "收入"]['金额'].sum()
        exp_all = df_calc[df_calc['资金性质'] == "支出"]['金额'].sum()
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 1. 业务活动汇总表")
            st.dataframe(df_calc.groupby(['一级科目', '二级科目'])['金额'].sum().reset_index(), use_container_width=True)
            st.metric("⚖️ 本期场所净资产变动(结余)", f"￥ {inc_all - exp_all:,.2f}")
        with c2:
            st.markdown("#### 2. 每月动态资产负债简表")
            bs_data = {
                "流动资产项目": ["流动资产：货币资金及现金存款", "固定资产：观内房屋建筑", "资产总计金额"],
                "账面价值": [f"￥ {inc_all - exp_all:,.2f}", "￥ 15,000,000.00", f"￥ {15000000.00 + (inc_all - exp_all):,.2f}"]
            }
            st.dataframe(pd.DataFrame(bs_data), use_container_width=True)

    # ------------------------------------------
    # 5. 观内借贷债务追踪大厅
    # ------------------------------------------
    with tabs[4]:
        st.markdown("### 🪵 观内借贷债务追踪大厅")
        st.dataframe(st.session_state.borrow_db, use_container_width=True)
