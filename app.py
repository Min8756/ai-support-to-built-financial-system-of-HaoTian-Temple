import streamlit as st
import pandas as pd
from datetime import datetime, date
import io
import os
import random
import zipfile

# 1. 页面基础配置
st.set_page_config(page_title="昊天观财务管理系统", layout="wide", page_icon="☯️")

# --- 2. 数据库与持久化基础配置 ---
CONFIG_FILE = "haotian_config.txt"
DEFAULT_BG = "https://raw.githubusercontent.com/Min8756/ai-support-to-built-financial-system-of-HaoTian-Temple/main/Gemini_Generated_Image_iaz9q7iaz9q7iaz9.png"
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

# 系统会话控制状态初始化
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = None

# 核心用户凭证名册
if 'user_registry' not in st.session_state:
    st.session_state.user_registry = {
        "volunteer": [
            {"username": "volunteer", "password": "ht123", "name": "妙音居士", "phone": "13911112222", "contact": "微信: miu_sound", "role": "volunteer", "title": "值班义工", "is_blocked": False}
        ],
        "finance": [
            {"username": "finance", "password": "ht456", "name": "张会计", "phone": "13800001111", "id_card": "61012319850101XXXX", "role": "finance", "title": "财务总账", "is_blocked": False}
        ],
        "haotianguan": [
            {"username": "haotianguan", "password": "ht789", "name": "李住持", "phone": "13599998888", "id_card": "61012319700505XXXX", "role": "temple_head", "title": "当家住持", "is_blocked": False}
        ]
    }

# 审计日志引擎
if 'audit_logs' not in st.session_state:
    st.session_state.audit_logs = pd.DataFrame([
        {"操作时间": "2026-05-30 09:15:22", "操作账号": "finance", "操作人姓名": "张会计", "操作内容": "系统初始化开盘，导入符合《民间非营利组织会计制度》的期初数据。"}
    ])

def append_audit_log(username, name, action):
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    new_log = {"操作时间": now_str, "操作账号": username, "操作人姓名": name, "操作内容": action}
    st.session_state.audit_logs = pd.concat([st.session_state.audit_logs, pd.DataFrame([new_log])], ignore_index=True)

# ======================== ⛩️ 依据最新《会计体系.docx》完美重构的科目树 ========================
ACCOUNTING_STRUCTURE = {
    "资产类": {
        "1001 库存现金": ["日常零星开支", "庙内功德箱每日清点前临时周转现金"],
        "1002 银行存款": ["庙宇对公账户资金存管", "指定收款账户资金存管"],
        "1101 应收账款/预付账款": ["预付大型修缮工程款", "法会物资订金"],
        "1201 库存商品/物资采购": ["结缘香烛", "护身符", "佛珠", "经书", "民俗文化用品"],
        "1501 固定资产": ["庙宇主体建筑", "大殿", "神像", "大型香炉", "办公设备"],
        "1502 累计折旧": ["固定资产价值损耗备抵"]
    },
    "负债类": {
        "2001 应付账款": ["未结清修缮工程尾款", "采购香烛等物资未结货款"],
        "2101 预收账款/暂收款": ["预定未来特定法会款", "预定牌位款", "大型供奉活动未办款"],
        "2201 应付职工薪酬": ["长住人员生活补贴", "管理人员报酬", "法会临时帮工劳务费"],
        "2301 短期借款/长期借款": ["银行商业贷款", "向特定组织/大德居士的有息、无息借款"]
    },
    "净资产类": {
        "3001 非限定性净资产": ["可自由支配日常累计结余(无特定指定用途的资金)"],
        "3002 限定性净资产": ["信众明确指定用途的专项神像重塑款", "指定专项大殿修缮款"]
    },
    "收入类": {
        "4001 功德捐赠收入——非限定性": ["随喜功德款", "日常投入功德箱", "扫码捐赠"],
        "4002 功德捐赠收入——限定性（专项）": ["信众明确指定用途的专项捐款(如专项贴金/修缮)"],
        "4101 法会服务收入": ["消灾/祈福/度亡法会收入", "光明灯/太岁灯点灯收入", "立牌位服务收入"],
        "4201 经营结缘收入": ["香烛售卖流通收入", "文创产品结缘收入", "开光法物取得收入"],
        "4301 其他收入": ["银行利息收入", "地方文保及政府相关补助补贴"]
    },
    "支出类": {
        "5001 宗教活动支出": ["法会直接消耗物资/供品", "法器采购", "法事人员劳务费用(嚫资)"],
        "5101 经营结缘成本": ["香烛采购进价成本", "开光法物进价成本", "文创产品进价成本"],
        "5201 管理费用": ["水电燃气费", "日常维修费", "办公用品", "服务器托管维护费", "接待费"],
        "5301 文物及建筑修缮支出": ["庙宇主体建筑重建", "殿堂翻新", "神像贴金专项开支"],
        "5401 慈善公益支出": ["对外施粥/济贫", "助学/灾区捐款支出"]
    }
}

if 'ledger' not in st.session_state:
    test_data = [
        {
            '流水号': 'HT-202605-001', '日期': '2026-05-30', '会计要素': '收入类', '一级科目': '4001 功德捐赠收入——非限定性', '二级科目': '日常投入功德箱',
            '金额': 5000.0, '经手人': '妙音居士', '凭证附件': '收据_2026053001.jpg', '操作员': '张会计', '操作员电话': '13800001111',
            '备注': '香客自愿投递功德箱结余', '审批状态': '无需审批', '接待对象': '无', '接待事由': '无'
        },
        {
            '流水号': 'HT-202605-002', '日期': '2026-05-30', '会计要素': '支出类', '一级科目': '5201 管理费用', '二级科目': '水电燃气费',
            '金额': 1200.0, '经手人': '自来水公司', '凭证附件': '发票_2026053001.pdf', '操作员': '张会计', '操作员电话': '13800001111',
            '备注': '解缴第二季度观内日常水费', '审批状态': '无需审批', '接待对象': '无', '接待事由': '无'
        }
    ]
    st.session_state.ledger = pd.DataFrame(test_data)

if 'borrow_db' not in st.session_state:
    st.session_state.borrow_db = pd.DataFrame([
        {
            '合同单号': 'HT-LOAN-2026-001', '借贷方向': '借入(负债)', '债权/债务人': '城固商业银行', '本金金额': 500000.0,
            '年化利率(%)': 4.15, '签署日期': '2026-02-15', '到期时限': '2026-12-31', '经办人': '张会计',
            '凭证附件': '借款合同_2026021501.pdf', '审批状态': '住持已批准', '备注': '筹措斋堂扩建工程款'
        }
    ])

if 'file_vault' not in st.session_state:
    st.session_state.file_vault = {
        '收据_2026053001.jpg': b"IMAGE_BINARY_DATA_STREAM",
        '发票_2026053001.pdf': b"PDF_BINARY_DATA_STREAM",
        '借款合同_2026021501.pdf': b"CONTRACT_BINARY_DATA_STREAM"
    }

if 'vol_active_name' not in st.session_state:
    st.session_state.vol_active_name = ""
if 'vol_active_phone' not in st.session_state:
    st.session_state.vol_active_phone = ""

# --- 3. 全局动态视觉渲染引擎 ---
if not st.session_state.logged_in:
    st.markdown(f"""
    <style>
    .stApp {{ background-image: url("{st.session_state.bg_img_url}") !important; background-size: cover !important; background-position: center !important; background-attachment: fixed !important; }}
    h1, h2, h3 {{ color: #8B0000 !important; font-family: 'Kaiti', 'STKaiti', 'serif'; text-shadow: 1px 1px 2px white; }}
    .stButton>button {{ background-color: #8B0000; color: white; border-radius: 5px; }}
    [data-testid="stForm"], .stForm {{ background-color: rgba(255, 255, 255, 0.96) !important; padding: 25px; border-radius: 12px; box-shadow: 0px 4px 15px rgba(0,0,0,0.4); }}
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <style>
    .stApp {{ background-color: {st.session_state.op_theme_color} !important; background-image: none !important; }}
    [data-testid="stSidebar"] {{ background-color: #F5F5DC !important; border-right: 2px solid #8B4513; }}
    h1, h2, h3 {{ color: #8B0000 !important; font-family: 'Kaiti', 'STKaiti', 'serif'; }}
    [data-testid="stMetricValue"] {{ color: #8B0000 !important; font-weight: bold; }}
    .stButton>button {{ background-color: #8B0000; color: white; border-radius: 5px; }}
    [data-testid="stForm"], .stForm {{ background-color: #FFFFFF !important; border: 1px solid #E0DDC8; padding: 20px; border-radius: 10px; }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. 核心工具包通用引擎 ---
def smart_rename_by_rules(f_date, f_el, uploaded_file):
    date_str = f_date.strftime('%Y%m%d')
    doc_type = "收据" if f_el in ["收入类", "净资产类"] else "发票"
    all_attachments = []
    if not st.session_state.ledger.empty:
        all_attachments += list(st.session_state.ledger['凭证附件'].dropna())
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
    return f"{doc_type}_{date_str}{str(day_count).zfill(2)}{ext}"

def make_zip_archive_selected(df_target):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        excel_buffer = io.BytesIO()
        try:
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                df_target.to_excel(writer, index=False, sheet_name="明细清册")
        except:
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                df_target.to_excel(writer, index=False, sheet_name="明细清册")
        zip_file.writestr("账目明细归档.xlsx", excel_buffer.getvalue())
        if '凭证附件' in df_target.columns:
            unique_files = df_target['凭证附件'].dropna().unique()
            for fname in unique_files:
                if fname in st.session_state.file_vault:
                    zip_file.writestr(str(fname), st.session_state.file_vault[fname])
    return zip_buffer.getvalue()

# --- 5. 统一认证登录分流中心 ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; margin-top: 80px;'>⛩️ 昊天观财务管理中心</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.form("login_gate"):
            input_user = st.text_input("管理账号")
            input_pwd = st.text_input("管理密码", type="password")
            if st.form_submit_button("🔐 安全验证登录", use_container_width=True):
                if input_user == "admin" and input_pwd == "20010905":
                    st.session_state.logged_in = True
                    st.session_state.current_user = {"username": "admin", "name": "超级系统总管", "role": "admin", "title": "系统总监控制"}
                    append_audit_log("admin", "超级系统总管", "至高安全管理员正式入闸登录。")
                    st.rerun()
                else:
                    matched_user = None
                    for role_key, user_list in st.session_state.user_registry.items():
                        for u in user_list:
                            if u["username"] == input_user and u["password"] == input_pwd:
                                matched_user = u
                                break
                    if matched_user:
                        if matched_user.get("is_blocked", False):
                            st.error("❌ 抱歉，该执事账号当前已被系统拉黑封禁，不可登台！")
                        else:
                            st.session_state.logged_in = True
                            st.session_state.current_user = matched_user.copy()
                            append_audit_log(matched_user["username"], matched_user["name"], "常规职能账户完成登录。")
                            st.rerun()
                    else:
                        st.error("❌ 密码配钥失败或该账号未注册。")
            st.stop() # 核心熔断守卫

# 🛡️ 安全隔离区：只有登录后才允许解析身份字典
current_user = st.session_state.current_user if st.session_state.current_user is not None else {}
current_role = current_user.get("role", "volunteer")

st.sidebar.markdown(f"### 🕯️ 执事人：{current_user.get('name', '匿名用户')}")
st.sidebar.markdown(f"当前岗位：`{current_user.get('title', '常驻执事')}`")
if st.sidebar.button("🚪 安全换班交接", use_container_width=True):
    append_audit_log(current_user.get("username", "unknown"), current_user.get("name", "unknown"), "退出登录，交接完毕。")
    st.session_state.logged_in = False
    st.session_state.current_user = None
    st.rerun()

# ==============================================================================
# 🎮 权限模块一：ADMIN 超级管理员至高控制台
# ==============================================================================
if current_role == "admin":
    st.markdown("## 👑 昊天观·超级管理员特权天盘")
    adm_tabs = st.tabs(["👁️ 操作流水监控", "🛠️ 账目审计与修缮", "📦 凭证档案馆", "👥 账户设置与管理"])
    
    with adm_tabs[0]:
        st.markdown("#### 📜 全系统审计追踪监控日志 (Trace)")
        st.dataframe(st.session_state.audit_logs.iloc[::-1], use_container_width=True)
        if st.button("🧹 清空冗余审计痕迹"):
            st.session_state.audit_logs = st.session_state.audit_logs.iloc[0:1]
            st.rerun()
            
    with adm_tabs[1]:
        st.markdown("#### 🛠️ 账目审计与修缮 (支持安全联动修改)")
        if st.session_state.ledger.empty:
            st.info("总账清空，无数据。")
        else:
            selected_idx = st.selectbox(
                "选择需要紧急修正或移除的账目流水号", 
                st.session_state.ledger.index, 
                format_func=lambda x: f"{st.session_state.ledger.loc[x, '流水号']} | 金额:{st.session_state.ledger.loc[x, '金额']} | {st.session_state.ledger.loc[x, '备注']}"
            )
            row_data = st.session_state.ledger.loc[selected_idx]
            
            # 🛡️ 联动安全重构逻辑区（防止错配爆错）
            with st.form("adm_modify_form"):
                ed_date = st.text_input("账目日期", str(row_data['日期']))
                
                # 要素大类
                elements_list = list(ACCOUNTING_STRUCTURE.keys())
                el_default_idx = elements_list.index(row_data['会计要素']) if row_data['会计要素'] in elements_list else 0
                ed_el = st.selectbox("会计要素大类", elements_list, index=el_default_idx, key=f"adm_el_val_{selected_idx}")
                
                # 安全一级科目防护
                c1_opts = list(ACCOUNTING_STRUCTURE[ed_el].keys())
                c1_default_idx = c1_opts.index(row_data['一级科目']) if row_data['一级科目'] in c1_opts else 0
                ed_c1 = st.selectbox("一级科目", c1_opts, index=c1_default_idx, key=f"adm_c1_val_{selected_idx}")
                
                # 安全二级科目防护
                c2_opts = ACCOUNTING_STRUCTURE[ed_el][ed_c1]
                c2_default_idx = c2_opts.index(row_data['二级科目']) if row_data['二级科目'] in c2_opts else 0
                ed_c2 = st.selectbox("二级科目", c2_opts, index=c2_default_idx, key=f"adm_c2_val_{selected_idx}")
                
                ed_amount = st.number_input("金额 (元)", value=float(row_data['金额']))
                ed_person = st.text_input("经手报销人", str(row_data['经手人']))
                ed_file = st.text_input("挂载凭证文件名", str(row_data['凭证附件']))
                ed_memo = st.text_area("详细说明", str(row_data['备注']))
                
                col_btn1, col_btn2 = st.columns(2)
                if col_btn1.form_submit_button("💾 确认保存修改并覆盖发布"):
                    st.session_state.ledger.loc[selected_idx] = [
                        row_data['流水号'], ed_date, ed_el, ed_c1, ed_c2, float(ed_amount), ed_person, ed_file,
                        "超级管理员", "N/A", ed_memo, row_data.get('审批状态', '无需审批'), row_data.get('接待对象', '无'), row_data.get('接待事由', '无')
                    ]
                    append_audit_log("admin", "超级总管", f"强制审计修改流水账目: {row_data['流水号']}")
                    st.success("🎉 修改大盘发布成功！")
                    st.rerun()
                if col_btn2.form_submit_button("🗑️ 彻底斩断抹除此条账目"):
                    st.session_state.ledger = st.session_state.ledger.drop(selected_idx).reset_index(drop=True)
                    append_audit_log("admin", "超级总管", f"深度抹除流水账目: {row_data['流水号']}")
                    st.warning("💥 该条目已被永久粉碎抹除！")
                    st.rerun()
                    
    with adm_tabs[2]:
        st.markdown("#### 📦 凭证归档与导出中心")
        kv_search = st.text_input("按时间或文件关键词快速检索档案卷宗")
        vault_keys = list(st.session_state.file_vault.keys())
        filtered_keys = [k for k in vault_keys if kv_search in k] if kv_search else vault_keys
        if filtered_keys:
            for fname in filtered_keys:
                c_f1, c_f2 = st.columns([4, 1])
                c_f1.markdown(f"📁 归档会计凭证：`{fname}`")
                c_f2.download_button("📥 调阅提取", st.session_state.file_vault[fname], file_name=fname, key=f"v_dl_{fname}")
        else:
            st.info("凭证档案馆空虚。")
            
    with adm_tabs[3]:
        st.markdown("#### 👥 账户全角色设置与管理面板")
        with st.form("new_user_form"):
            new_u = st.text_input("新账号登录名")
            new_p = st.text_input("初始安全密码")
            new_n = st.text_input("法名/真实姓名")
            new_ph = st.text_input("绑定联络电话")
            new_r = st.selectbox("分配系统岗位入口角色", ["volunteer", "finance", "temple_head"])
            if st.form_submit_button("➕ 登记并开放系统权限"):
                title_map = {"volunteer": "值班义工", "finance": "财务总账", "temple_head": "当家住持"}
                st.session_state.user_registry[new_r].append({
                    "username": new_u, "password": new_p, "name": new_n, "phone": new_ph, "role": new_r, "title": title_map[new_r], "is_blocked": False
                })
                append_audit_log("admin", "超级管理员", f"录入新账号: {new_u}")
                st.success("🎉 新执事信息成功录入大盘！")
                st.rerun()

# ==============================================================================
# 🧑‍🌾 权限模块二：VOLUNTEER 值班义工快捷账台
# ==============================================================================
elif current_role == "volunteer":
    st.markdown("## ⛩️ 昊天观·值班义工快捷账台")
    if not st.session_state.vol_active_name or not st.session_state.vol_active_phone:
        st.markdown("#### 🔑 值班义工登台履职前置实名认证")
        with st.form("vol_lock_gate"):
            v_name = st.text_input("✍️ 本次值班义工姓名/法名")
            v_phone = st.text_input("📱 值班人员合法联络手机号")
            if st.form_submit_button("解锁值班财务工作台", use_container_width=True):
                if v_name and v_phone:
                    st.session_state.vol_active_name = v_name
                    st.session_state.vol_active_phone = v_phone
                    append_audit_log("volunteer", v_name, f"义工认证登台，手机：{v_phone}")
                    st.rerun()
                else:
                    st.error("❌ 请务必填写完整方可开盘！")
        st.stop()
        
    st.markdown(f"**当前值班履职义工：`{st.session_state.vol_active_name}` ({st.session_state.vol_active_phone})**")
    v_tabs = st.tabs(["📝 快捷凭证流水登记", "🔍 今日日记账浏览"])
    
    with v_tabs[0]:
        with st.form("vol_form"):
            v_date = st.date_input("1. 发生日期", date.today())
            v_nature = st.radio("2. 确定资财收支属性", ["信众随喜捐赠类收入", "观内场所日常维护/小额办公支出"], horizontal=True)
            
            if "收入" in v_nature:
                el_auto = "收入类"
                c1_auto = "4001 功德捐赠收入——非限定性"
            else:
                el_auto = "支出类"
                c1_auto = "5201 管理费用"
                
            opts = ACCOUNTING_STRUCTURE[el_auto][c1_auto]
            v_c2 = st.selectbox("3. 选择合规对应的二级子目", opts)
            v_amount = st.number_input("4. 资财变动金额 (元)", min_value=0.0, step=10.0)
            v_memo = st.text_area("5. 录入详细说明与疏文摘要")
            v_file = st.file_uploader("6. 上传原始小票/法务功德单据存", type=["jpg", "png", "pdf"])
            
            if st.form_submit_button("🔥 提交入库并触发系统自编号归档", use_container_width=True):
                if not v_memo:
                    st.error("❌ 请填报摘要说明！")
                else:
                    assigned_name = smart_rename_by_rules(v_date, el_auto, v_file)
                    st.session_state.file_vault[assigned_name] = v_file.getvalue() if v_file else b"NO_DATA"
                    f_id = f"HT-VOL-{datetime.now().strftime('%Y%m%d')}-{random.randint(100,999)}"
                    app_status = "等待住持审批" if (el_auto == "支出类" and float(v_amount) >= 10000.0) else "无需审批"
                    new_row = {
                        '流水号': f_id, '日期': v_date.strftime('%Y-%m-%d'), '会计要素': el_auto, '一级科目': c1_auto, '二级科目': v_c2,
                        '金额': float(v_amount), '经手人': st.session_state.vol_active_name, '凭证附件': assigned_name,
                        '操作员': f"义工:{st.session_state.vol_active_name}", '操作员电话': st.session_state.vol_active_phone,
                        '备注': v_memo, '审批状态': app_status, '接待对象': '无', '接待事由': '无'
                    }
                    st.session_state.ledger = pd.concat([st.session_state.ledger, pd.DataFrame([new_row])], ignore_index=True)
                    append_audit_log("volunteer", st.session_state.vol_active_name, f"录入简记账目: {f_id}")
                    st.success(f"🎉 登记入账成功！大档案编号为：`{assigned_name}`")
                    st.rerun()

    with v_tabs[1]:
        st.markdown("#### 📅 今日发生的简易日记账清册")
        t_str = date.today().strftime('%Y-%m-%d')
        df_t = st.session_state.ledger[st.session_state.ledger['日期'] == t_str].copy()
        st.dataframe(df_t, use_container_width=True)

# ==============================================================================
# 👑 权限模块三：FINANCE 财务总账 / TEMPLE_HEAD 当家住持 联合核算大盘
# ==============================================================================
else:
    title_display = current_user.get('title', '专业会计执事')
    st.markdown(f"## ⛩️ {title_display}专业核算大盘")
    tabs = st.tabs(["📝 规范化手工记账台", "📊 历史明细账档案馆", "📜 财务报表大盘", "🪵 借贷与债务风险追踪"])
    
    # --- 标签 1：规范化手工记账台（死锁防御重构） ---
    with tabs[0]:
        if current_role == "temple_head":
            st.markdown("### 🏛️ 当家住持专属：内控审批与审计法盘")
            # 审批流核心面板
            df_pending_expense = st.session_state.ledger[st.session_state.ledger['审批状态'] == "等待住持审批"]
            if df_pending_expense.empty:
                st.info("太极清静，当前暂无等待审批的大额开支条目。")
            else:
                for idx in df_pending_expense.index:
                    item = df_pending_expense.loc[idx]
                    with st.expander(f"⚠️ 支出流水: {item['流水号']} | 科目: {item['二级科目']} | 金额: ￥{item['金额']:,} 元", expanded=True):
                        st.write(f"**经手申请人**: {item['经手人']} | **摘要说明**: {item['备注']}")
                        if item['二级科目'] == "接待费":
                            st.warning(f"接待特定对象: {item.get('接待对象','未说明')} | 接待事由: {item.get('接待事由','未说明')}")
                        ap_col1, ap_col2 = st.columns(2)
                        if ap_col1.button("🟢 同意批准开支", key=f"app_y_{idx}"):
                            st.session_state.ledger.loc[idx, '审批状态'] = "住持已批准"
                            append_audit_log(current_user.get("username"), current_user.get("name"), f"住持批准了大额支出: {item['流水号']}")
                            st.rerun()
                        if ap_col2.button("🔴 不同意/驳回款项", key=f"app_n_{idx}"):
                            st.session_state.ledger.loc[idx, '审批状态'] = "住持已驳回"
                            append_audit_log(current_user.get("username"), current_user.get("name"), f"住持驳回了大额支出: {item['流水号']}")
                            st.rerun()
            st.markdown("---")
        
        st.markdown("### ✍️ 经办做账手工填报台")
        
        # 🛡️ 联动死锁防范核心重构：利用 Session State 分步安全拦截
        if "form_el" not in st.session_state:
            st.session_state.form_el = "资产类"
        if "form_c1" not in st.session_state:
            st.session_state.form_c1 = list(ACCOUNTING_STRUCTURE["资产类"].keys())[0]

        # 表单外部使用非硬编码的动态回调防止索引崩溃
        selected_element = st.selectbox("1. 选择会计大类要素", list(ACCOUNTING_STRUCTURE.keys()), key="main_el_select")
        
        # 当要素改变，强制清空及刷新子科目列表防止错配
        c1_options = list(ACCOUNTING_STRUCTURE[selected_element].keys())
        selected_c1 = st.selectbox("2. 一级会计科目", c1_options, key="main_c1_select")
        
        c2_options = ACCOUNTING_STRUCTURE[selected_element][selected_c1]
        selected_c2 = st.selectbox("3. 二级核算细目", c2_options, key="main_c2_select")

        with st.form("manual_bookkeeping_form_fixed"):
            f_date = st.date_input("记账日期", date.today())
            f_amount = st.number_input("4. 发生业务金额 (元)", min_value=0.0, step=100.0)
            f_person = st.text_input("5. 经手人/报销报账人签名")
            f_memo = st.text_area("6. 业务事由详细描述说明")
            f_file = st.file_uploader("7. 上传权威合规原始档案凭证", type=["pdf", "png", "jpg"])
            
            st.markdown("##### 🍽️ 宗教特定合规审查辅助区 (选填)")
            rec_obj = st.text_input("特定接待对象 (如：外来参访团名称/学者专家)", "无")
            rec_reason = st.text_input("公务接待特定事由说明", "无")
            
            if st.form_submit_button("🕊️ 确认无误·提交大盘总账"):
                if f_amount <= 0 or not f_person or not f_memo:
                    st.error("❌ 基础要素数据不齐，无法完成正式做账！")
                elif selected_c2 == "接待费" and (rec_obj == "无" or rec_reason == "无"):
                    st.error("❌ 依《宗教活动场所财务监督管理办法》，特殊接待支出必须严审并填写接待对象与事由！")
                else:
                    assigned_name = smart_rename_by_rules(f_date, selected_element, f_file)
                    st.session_state.file_vault[assigned_name] = f_file.getvalue() if f_file else b"NO_DATA"
                    f_id = f"HT-{f_date.strftime('%Y%m')}-{random.randint(100,999)}"
                    
                    app_status = "等待住持审批" if (selected_element == "支出类" and float(f_amount) >= 10000.0) else "无需审批"
                    
                    new_row = {
                        '流水号': f_id, '日期': f_date.strftime('%Y-%m-%d'), '会计要素': selected_element, '一级科目': selected_c1, '二级科目': selected_c2,
                        '金额': float(f_amount), '经手人': f_person, '凭证附件': assigned_name, '操作员': current_user.get('name'),
                        '操作员电话': current_user.get('phone', 'N/A'), '备注': f_memo, '审批状态': app_status,
                        '接待对象': rec_obj, '接待事由': rec_reason
                    }
                    st.session_state.ledger = pd.concat([st.session_state.ledger, pd.DataFrame([new_row])], ignore_index=True)
                    append_audit_log(current_user.get('username'), current_user.get('name'), f"手工记账: {f_id} | 状态: {app_status}")
                    st.success(f"🎉 成功做账！自小编号凭证卷宗：`{assigned_name}`")
                    st.rerun()

    # --- 标签 2：历史明细账档案馆 ---
    with tabs[1]:
        st.markdown("### 📊 昊天观历史明细总账电子档案")
        c_col1, c_col2, c_col3 = st.columns(3)
        q_start = c_col1.date_input("筛选：起始日期", date(2026, 1, 1))
        q_end = c_col2.date_input("筛选：截止日期", date(2026, 12, 31))
        kw_search = c_col3.text_input("输入流水的关键词/经手人模糊检索")
        
        df_filter = st.session_state.ledger.copy()
        df_filter['日期'] = pd.to_datetime(df_filter['日期']).dt.date
        df_filter = df_filter[(df_filter['日期'] >= q_start) & (df_filter['日期'] <= q_end)]
        if kw_search:
            df_filter = df_filter[df_filter['备注'].str.contains(kw_search) | df_filter['经手人'].str.contains(kw_search)]
            
        if df_filter.empty:
            st.info("在此过滤条件下未查询到任何明细账目数据。")
        else:
            selected_rows = []
            for idx in df_filter.index:
                row = df_filter.loc[idx]
                r_c1, r_c2 = st.columns([12, 1])
                is_sel = r_c1.checkbox(f"流水号: {row['流水号']} | 日期: {row['日期']} | {row['会计要素']}->{row['二级科目']} | 金额: ￥{row['金额']:,} | 状态: {row['审批状态']} | 备注: {row['备注']}", value=True, key=f"ledger_chk_{idx}")
                if row['凭证附件'] in st.session_state.file_vault:
                    r_c2.download_button("📄 凭证", st.session_state.file_vault[row['凭证附件']], file_name=str(row['凭证附件']), key=f"dl_single_f_{idx}")
                else:
                    r_c2.write("无")
                if is_sel:
                    selected_rows.append(row)
                    
            if selected_rows:
                df_export = pd.DataFrame(selected_rows)
                st.markdown("---")
                exp_zip = make_zip_archive_selected(df_export)
                st.download_button("📥 批量打包导出选中的明细账目及对应凭证 (ZIP)", exp_zip, file_name="昊天观选定账目包.zip", mime="application/zip", use_container_width=True)

    # --- 标签 3：财务报表大盘 ---
    with tabs[2]:
        st.markdown("### 📜 规范化财务报表大盘（按非营利组织制度定义）")
        rep_period = st.selectbox("请选择要生成的会计报表周期阶段", ["2026年05月度中盘报表", "2026年第二季度周期报表", "2026年年度决算预估总表"])
        
        df_l = st.session_state.ledger[st.session_state.ledger['审批状态'].isin(["无需审批", "住持已批准"])]
        sum_asset = df_l[df_l['会计要素'] == '资产类']['金额'].sum() + 500000.0
        sum_liab = df_l[df_l['会计要素'] == '负债类']['金额'].sum() + st.session_state.borrow_db['本金金额'].sum()
        sum_rev = df_l[df_l['会计要素'] == '收入类']['金额'].sum()
        sum_exp = df_l[df_l['会计要素'] == '支出类']['金额'].sum()
        sum_net = sum_rev - sum_exp + 300000.0
        
        m_c1, m_c2, m_c3 = st.columns(3)
        m_c1.metric("1. 资产总计 (含期初及变动)", f"￥{sum_asset:,} 元")
        m_c2.metric("2. 负债总计 (含银行长线信贷)", f"￥{sum_liab:,} 元")
        m_c3.metric("3. 净资产运营期末总结余", f"￥{sum_net:,} 元")
        
        st.markdown("##### 📉 业务活动收支结余动态走势")
        df_report_view = pd.DataFrame({
            '财务指标类别': ['功德捐赠与随喜总收入', '日常宗教与行政管理总支出', '当期业务结余差异值'],
            '当期累计归集发生额(元)': [sum_rev, sum_exp, sum_rev - sum_exp]
        })
        st.table(df_report_view)
        
        excel_rep = io.BytesIO()
        with pd.ExcelWriter(excel_rep, engine='openpyxl') as wr:
            df_report_view.to_excel(wr, index=False, sheet_name="核心业务收支表")
        st.download_button("📊 提取此阶段规范财务平衡报表(Excel)", excel_rep.getvalue(), file_name=f"{rep_period}.xlsx", use_container_width=True)

    # --- 标签 4：借贷与债务风险追踪 ---
    with tabs[3]:
        st.markdown("### 🪵 观内融资借贷与债务存续法律契约风险追踪")
        st.dataframe(st.session_state.borrow_db, use_container_width=True)
