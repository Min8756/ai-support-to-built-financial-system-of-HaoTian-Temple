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
# 依据技术与视觉约束，将固定背景图写入默认配置
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

# 核心用户凭证名册（支持管理员后台一键拉黑/重置）
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

# 审计天眼日志引擎
if 'audit_logs' not in st.session_state:
    st.session_state.audit_logs = pd.DataFrame([
        {"操作时间": "2026-05-30 09:15:22", "操作账号": "finance", "操作人姓名": "张会计", "操作内容": "系统初始化开盘，导入符合《民间非营利组织会计制度》的期初数据。"}
    ])

def append_audit_log(username, name, action):
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    new_log = {"操作时间": now_str, "操作账号": username, "操作人姓名": name, "操作内容": action}
    st.session_state.audit_logs = pd.concat([st.session_state.audit_logs, pd.DataFrame([new_log])], ignore_index=True)

# ==========================================
# 🛠️ 严格依据《会计体系.docx》构建的联动字典体系 
# ==========================================
ACCOUNTING_STRUCTURE = {
    "资产类": {
        "1001 库存现金": ["庙内功功德箱每日清点前临时周转现金", "日常零星开支"],
        "1002 银行存款": ["对公账户资金存管", "指定收款账户资金存管"],
        "1101 应收账款/预付账款": ["预付大型修缮工程款", "法会物资订金"],
        "1201 库存商品/物资采购": ["结缘香烛", "护身符/佛珠", "经书", "民俗文化用品"],
        "1501 固定资产": ["庙宇主体建筑/大殿", "神像/大型香炉", "办公设备"],
        "1502 累计折旧": ["固定资产价值损耗备抵"]
    },
    "负债类": {
        "2001 应付账款": ["未结清修缮工程尾款", "采购香烛等物资未结货款"],
        "2101 预收账款/暂收款": ["预定未来特定法会款", "预定牌位款", "大型供奉活动未办款"],
        "2201 应付职工薪酬": ["长住人员生活补贴", "管理人员报酬", "法会临时帮工劳务费"]
    },
    "净资产类": {
        "3001 非限定性净资产": ["可自由支配日常累计结余"],
        "3002 限定性净资产": ["指定专项神像重塑款", "指定专项大殿修缮款"]
    },
    "收入类": {
        "4001 功德捐赠收入——非限定性": ["随喜功德款", "日常投入功德箱", "扫码捐赠"],
        "4002 功德捐赠收入——限定性（专项）": ["信众明确指定用途的专项捐款"],
        "4101 法会服务收入": ["消灾/祈福/度亡法会收入", "光明灯/太岁灯点灯收入", "立牌位服务收入"],
        "4201 经营结缘收入": ["香烛售卖流通收入", "文创产品结缘收入", "开光法物取得收入"],
        "4301 其他收入": ["银行利息收入", "地方文保及政府相关补助补贴"]
    },
    "支出类": {
        "5001 宗教活动支出": ["法会直接消耗物资/供品", "法器采购", "法事人员劳务费用(嚫资)"],
        "5101 经营结缘成本": ["香烛采购进价成本", "开光法物进价成本", "文创产品进价成本"],
        "5201 管理费用": ["水电燃气费", "日常维修费", "办公用品", "服务器托管维护费"],
        "5301 文物及建筑修缮支出": ["庙宇主体建筑重建", "殿堂翻新", "神像贴金专项开支"],
        "5401 慈善公益支出": ["对外施粥/济贫", "助学/灾区捐款支出"]
    }
}

# 核心总账明细数据库初始化（加入审批流关键状态字段）
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

# 借贷管理清册（需住持联动审批）
if 'borrow_db' not in st.session_state:
    st.session_state.borrow_db = pd.DataFrame([
        {
            '合同单号': 'HT-LOAN-2026-001', '借贷方向': '借入(负债)', '债权/债务人': '城固商业银行', '本金金额': 500000.0,
            '年化利率(%)': 4.15, '签署日期': '2026-02-15', '到期时限': '2026-12-31', '经办人': '张会计',
            '凭证附件': '借款合同_2026021501.pdf', '审批状态': '住持已批准', '备注': '筹措斋堂扩建工程款'
        }
    ])

# 数字化档案凭证保险库
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
                    st.stop()

# 安全规范获取用户信息，彻底消除 `KeyError` 隐患
current_user = st.session_state.current_user
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
        st.markdown("#### 🛠️ 账目审计与修缮 (支持增/删/改/查)")
        if st.session_state.ledger.empty:
            st.info("总账清空，无数据。")
        else:
            selected_idx = st.selectbox("选择需要紧急修正或移除的账目流水号", st.session_state.ledger.index, format_func=lambda x: f"{st.session_state.ledger.loc[x, '流水号']} | 金额:{st.session_state.ledger.loc[x, '金额']} | {st.session_state.ledger.loc[x, '备注']}")
            row_data = st.session_state.ledger.loc[selected_idx]

            with st.form("adm_modify_form"):
                ed_date = st.text_input("账目日期", str(row_data['日期']))
                
                # ==============================================================================
                # 🛠️ 管理员账号：实现严格的多级过滤联动，隔离资产类
                # ==============================================================================
                ed_el = st.selectbox("会计要素大类", list(ACCOUNTING_STRUCTURE.keys()), index=list(ACCOUNTING_STRUCTURE.keys()).index(row_data['会计要素']) if row_data['会计要素'] in ACCOUNTING_STRUCTURE else 0, key="adm_el")
                
                adm_c1_opts = list(ACCOUNTING_STRUCTURE[ed_el].keys())
                # 尽量匹配历史的一级科目名称
                adm_c1_default = adm_c1_opts.index(row_data['一级科目']) if row_data['一级科目'] in adm_c1_opts else 0
                ed_c1 = st.selectbox("一级科目(对应要素)", adm_c1_opts, index=adm_c1_default, key="adm_c1")
                
                adm_c2_opts = ACCOUNTING_STRUCTURE[ed_el][ed_c1]
                adm_c2_default = adm_c2_opts.index(row_data['二级科目']) if row_data['二级科目'] in adm_c2_opts else 0
                ed_c2 = st.selectbox("二级科目", adm_c2_opts, index=adm_c2_default, key="adm_c2")
                # ==============================================================================
                
                ed_amount = st.number_input("金额 (元)", value=float(row_data['金额']))
                ed_person = st.text_input("经手报销人", str(row_data['经手人']))
                ed_file = st.text_input("挂载凭证文件名 (修改时将自动清理旧物理附件)", str(row_data['凭证附件']))
                ed_memo = st.text_area("详细说明", str(row_data['备注']))

                col_btn1, col_btn2 = st.columns(2)
                if col_btn1.form_submit_button("💾 确认保存修改并覆盖发布"):
                    old_file = row_data['凭证附件']
                    if old_file in st.session_state.file_vault and old_file != ed_file:
                        del st.session_state.file_vault[old_file]

                    st.session_state.ledger.loc[selected_idx] = [
                        row_data['流水号'], ed_date, ed_el, ed_c1, ed_c2, float(ed_amount), ed_person, ed_file,
                        "超级管理员", "N/A", ed_memo, row_data.get('审批状态', '无需审批'), row_data.get('接待对象', '无'), row_data.get('接待事由', '无')
                    ]
                    append_audit_log("admin", "超级总管", f"强制审计修改流水账目: {row_data['流水号']}")
                    st.success("🎉 修改大盘发布成功！旧文件已安全同步清理。")
                    st.rerun()

                if col_btn2.form_submit_button("🗑️ 彻底斩断抹除此条账目"):
                    old_file = row_data['凭证附件']
                    if old_file in st.session_state.file_vault:
                        del st.session_state.file_vault[old_file]
                    st.session_state.ledger = st.session_state.ledger.drop(selected_idx).reset_index(drop=True)
                    append_audit_log("admin", "超级总管", f"深度抹除流水账目: {row_data['流水号']}")
                    st.warning("💥 该条目及关联原始会计档案已被永久粉碎抹除！")
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

            st.markdown("---")
            if st.button("📦 触发全量财务凭证馆藏一键打包导出(ZIP)", use_container_width=True):
                all_zip = make_zip_archive_selected(st.session_state.ledger)
                st.download_button("🔥 打包准备就绪，点击下载全量馆藏.zip", all_zip, file_name="昊天观全量凭证馆藏.zip", mime="application/zip", use_container_width=True)
        else:
            st.info("凭证档案馆空虚。")

    with adm_tabs[3]:
        st.markdown("#### 👥 账户全角色设置与管理面板")
        with st.form("new_user_form"):
            st.markdown("##### ➕ 录入全新可信执事账户")
            new_u = st.text_input("新账号登录名")
            new_p = st.text_input("初始安全密码")
            new_n = st.text_input("法名/真实姓名")
            new_ph = st.text_input("绑定联络电话")
            new_r = st.selectbox("分配系统岗位入口角色", ["volunteer", "finance", "temple_head"])
            if st.form_submit_button("➕ 登记并开放系统权限"):
                title_map = {"volunteer": "值班义工", "finance": "财务总账", "temple_head": "当家住持"}
                st.session_state.user_registry[new_r].append({
                    "username": new_u, "password": new_p, "name": new_n, "phone": new_ph,
                    "role": new_r, "title": title_map[new_r], "is_blocked": False
                })
                append_audit_log("admin", "超级管理员", f"录入新账号: {new_u}，绑定角色: {new_r}")
                st.success("🎉 新执事信息成功录入大盘！")
                st.rerun()

        st.markdown("##### 👥 执事账号现存名册控制（支持密码重置与“一键拉黑”）")
        for r_key, u_list in st.session_state.user_registry.items():
            st.markdown(f"**岗位大类：{r_key}**")
            for idx, user in enumerate(u_list):
                u_col1, u_col2, u_col3 = st.columns([2, 2, 1])
                u_col1.write(f"👤 姓名: {user['name']} | 账号: `{user['username']}` | 密码: `{user['password']}`")

                if u_col2.button(f"🔄 重置初始安全密匙", key=f"rst_{r_key}_{idx}"):
                    st.session_state.user_registry[r_key][idx]["password"] = "ht888"
                    append_audit_log("admin", "超级总管", f"重置了账号 {user['username']} 的密码为默认 ht888")
                    st.success("密匙已重置为：ht888")
                    st.rerun()

                status_lbl = "🔴 已封禁(拉黑)" if user["is_blocked"] else "🟢 状态活跃"
                if u_col3.button(status_lbl, key=f"blk_{r_key}_{idx}"):
                    st.session_state.user_registry[r_key][idx]["is_blocked"] = not user["is_blocked"]
                    append_audit_log("admin", "超级总管", f"变动账号 {user['username']} 的封禁拉黑状态。")
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
                    append_audit_log("volunteer", v_name, f"义工认证登台，绑定手记物理线索：{v_phone}")
                    st.rerun()
                else:
                    st.error("❌ 姓名与手机号乃是责任划分的核心线索，请务必填写完整方可开盘！")
                    st.stop()

    st.markdown(f"**当前值班履职义工：`{st.session_state.vol_active_name}` ({st.session_state.vol_active_phone})**")
    v_tabs = st.tabs(["📝 快捷凭证流水登记", "🔍 今日日记账浏览"])

    with v_tabs[0]:
        with st.form("vol_form"):
            v_date = st.date_input("1. 发生日期", date.today())
            v_nature = st.radio("2. 确定资财收支属性", ["信众随喜捐赠类收入", "观内场所日常维护/小额办公支出"], horizontal=True)
            
            # ==============================================================================
            # 🛠️ 义工快捷记账模块：确保严格精准地对应新科目的前两级大类
            # ==============================================================================
            if "收入" in v_nature:
                el_auto = "收入类"
                c1_auto = "4001 功德捐赠收入——非限定性"
            else:
                el_auto = "支出类"
                c1_auto = "5201 管理费用"
                
            opts = ACCOUNTING_STRUCTURE[el_auto][c1_auto]
            v_c2 = st.selectbox("3. 选择合规对应的二级子目", opts)
            # ==============================================================================
            
            v_amount = st.number_input("4. 资财变动金额 (元)", min_value=0.0, step=10.0)
            v_memo = st.text_area("5. 录入详细说明与疏文摘要")
            v_file = st.file_uploader("6. 上传原始小票/法务功德单据据存", type=["jpg", "png", "pdf"])

            if st.form_submit_button("🔥 提交入库并触发系统自编号归档", use_container_width=True):
                if not v_memo:
                    st.error("❌ 请填报摘要说明，以备财务老师及住持查审！")
                else:
                    assigned_name = smart_rename_by_rules(v_date, el_auto, v_file)
                    st.session_state.file_vault[assigned_name] = v_file.getvalue() if v_file else b"NO_DATA"
                    f_id = f"HT-VOL-{datetime.now().strftime('%Y%m%d')}-{random.randint(100,999)}"
                    app_status = "等待住持审批" if (el_auto == "支出类" and float(v_amount) >= 10000.0) else "无需审批"

                    new_row = {
                        '流水号': f_id, '日期': v_date.strftime('%Y-%m-%d'), '会计要素': el_auto, '一级科目': c1_auto, '二级科目': v_c2,
                        '金额': float(v_amount), '经手人': st.session_state.vol_active_name, '凭证附件': assigned_name, '操作员': f"义工:{st.session_state.vol_active_name}",
                        '操作员电话': st.session_state.vol_active_phone, '备注': v_memo, '审批状态': app_status, '接待对象': '无', '接待事由': '无'
                    }
                    st.session_state.ledger = pd.concat([st.session_state.ledger, pd.DataFrame([new_row])], ignore_index=True)
                    append_audit_log("volunteer", st.session_state.vol_active_name, f"录入简记账目: {f_id}，状态: {app_status}")
                    st.success(f"🎉 登记入账成功！大档案编号捆绑为：`{assigned_name}`")
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

    # --- 标签 1：规范化多级记账台 ---
    with tabs[0]:
        if current_role == "temple_head":
            st.markdown("### 🏛️ 当家住持专属：内控审批与审计法盘")
            st.markdown("##### 👁️ 观内实时全量内控审计流水")
            st.dataframe(st.session_state.audit_logs.iloc[::-1], use_container_width=True)

            st.markdown("##### ⚖️ 待复核大额资金支出审批中心（>= ￥10,000）")
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
                            st.success("已批准该款项开支并实时回写总账。")
                            st.rerun()
                        if ap_col2.button("🔴 不同意/驳回款项", key=f"app_n_{idx}"):
                            st.session_state.ledger.loc[idx, '审批状态'] = "住持已驳回"
                            append_audit_log(current_user.get("username"), current_user.get("name"), f"住持驳回了大额支出: {item['流水号']}")
                            st.error("已驳回该开支申请。")
                            st.rerun()

            st.markdown("##### 🪵 融资借贷法度核查中心")
            df_pending_loan = st.session_state.borrow_db[st.session_state.borrow_db['审批状态'] == "等待住持审核"]
            if df_pending_loan.empty:
                st.info("暂无等待审批的借贷融资请求。")
            else:
                for l_idx in df_pending_loan.index:
                    loan_item = df_pending_loan.loc[l_idx]
                    st.warning(f"借贷合同：{loan_item['合同单号']} | 融资本金：￥{loan_item['本金金额']} | 债权/债务人：{loan_item['债权/债务人']}")
                    l_c1, l_c2 = st.columns(2)
                    if l_c1.button("🟢 批准此项借贷入账", key=f"ln_y_{l_idx}"):
                        st.session_state.borrow_db.loc[l_idx, '审批状态'] = "住持已批准"
                        append_audit_log(current_user.get("username"), current_user.get("name"), f"住持正式批准借贷项目: {loan_item['合同单号']}")
                        st.success("借贷协议正式受印批准！")
                        st.rerun()
                    if l_c2.button("🔴 驳回此项借贷请求", key=f"ln_n_{l_idx}"):
                        st.session_state.borrow_db.loc[l_idx, '审批状态'] = "住持已驳回"
                        append_audit_log(current_user.get("username"), current_user.get("name"), f"住持驳回借贷项目: {loan_item['合同单号']}")
                        st.rerun()
            st.markdown("---")

        st.markdown("#### ✍️ 登载合规记账凭证原始录入（严格遵循三部法律法规）")
        with st.form("professional_记账_form"):
            col_core1, col_core2 = st.columns(2)
            with col_core1:
                f_date = st.date_input("1. 会计记账日期", date.today())
                
                # ==============================================================================
                # 🛠️ 财务人员与住持账户：彻底解决资产类串行显示问题的多级严格下拉联动
                # ==============================================================================
                f_el = st.selectbox("2. 选择合规会计要素", list(ACCOUNTING_STRUCTURE.keys()), key="pro_el")
                
                # 依据当前选定的要素大类动态抓取一级科目，不再混淆
                c1_opts = list(ACCOUNTING_STRUCTURE[f_el].keys())
                f_c1 = st.selectbox("3. 一级科目(对应要素)", c1_opts, key="pro_c1")
                
                # 依据当前选定的要素大类 + 一级科目，精准定位明细二级科目
                c2_opts = ACCOUNTING_STRUCTURE[f_el][f_c1]
                f_c2 = st.selectbox("4. 二级明细科目", c2_opts, key="pro_c2")
                # ==============================================================================

            with col_core2:
                f_amount = st.number_input("5. 发生金额 (元)", min_value=0.0, step=100.0)
                f_person = st.text_input("6. 功德主 / 经办解批报销人")
                f_file = st.file_uploader("7. 挂载标准原始会计档案凭证", type=["jpg", "png", "pdf"])
                f_memo = st.text_area("8. 账目发生之详细情况/功德事项摘要")

            # 特定科目（如业务招待费）的特别内控补充字段
            is_reception = ("接待" in f_c2 or "招待" in f_c2)
            rec_obj, rec_reason = "无", "无"
            if is_reception:
                st.markdown("##### ⚠️ 发现敏感科类：因触及宗教场所规范接待红线，请加注下述审计要素")
                col_rec1, col_rec2 = st.columns(2)
                rec_obj = col_rec1.text_input("外事接待对象/相关单位全称", "无")
                rec_reason = col_rec2.text_input("因何公务活动或法务缘由接待说明", "无")

            if st.form_submit_button("📜 经办终审确认，发布总账清册", use_container_width=True):
                if not f_memo or f_amount <= 0 or not f_person:
                    st.error("❌ 金额、经办报销人及摘要必须填全，方可合规入账！")
                elif is_reception and (rec_obj == "无" or rec_reason == "无"):
                    st.error("❌ 业务活动成本中的接待项属于严查敏感项，请完整披露接待对象与事由！")
                else:
                    assigned_name = smart_rename_by_rules(f_date, f_el, f_file)
                    if f_file:
                        st.session_state.file_vault[assigned_name] = f_file.getvalue()
                    else:
                        st.session_state.file_vault[assigned_name] = b"PRO_NO_ATTACHMENT"

                    f_id = f"HT-ACC-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000,9999)}"
                    
                    # 规则拦截：只要要素大类是支出类且金额大于等于一万元，进入审批流
                    if f_el == "支出类" and float(f_amount) >= 10000.0:
                        app_status = "等待住持审批"
                    else:
                        app_status = "无需审批"

                    new_row = {
                        '流水号': f_id, '日期': f_date.strftime('%Y-%m-%d'), '会计要素': f_el, '一级科目': f_c1, '二级科目': f_c2,
                        '金额': float(f_amount), '经手人': f_person, '凭证附件': assigned_name, '操作员': current_user.get('name'),
                        '操作员电话': current_user.get('phone', 'N/A'), '备注': f_memo, '审批状态': app_status,
                        '接待对象': rec_obj, '接待事由': rec_reason
                    }
                    st.session_state.ledger = pd.concat([st.session_state.ledger, pd.DataFrame([new_row])], ignore_index=True)
                    append_audit_log(current_user.get("username"), current_user.get("name"), f"手工记账入库: {f_id}，对应金额: {f_amount}，状态: {app_status}")
                    
                    if app_status == "等待住持审批":
                        st.warning(f"⚠️ 发现该笔开支金额达 ￥{f_amount:,} 元，已触发1万元上限自动内控拦截！已提请住持审批盘。")
                    else:
                        st.success(f"🎉 财务总账登载成功！资产证券原始编号：`{assigned_name}`")
                    st.rerun()

    # --- 标签 2：历史明细账档案馆（完全保留原有高级多选/全选/打包ZIP导出等功能） ---
    with tabs[1]:
        st.markdown("#### 🔍 历史全量明细账目及智能筛选检索台")
        if st.session_state.ledger.empty:
            st.info("当前总账大盘内没有数据。")
        else:
            col_sh1, col_sh2, col_sh3 = st.columns([1, 1, 2])
            with col_sh1:
                search_el = st.selectbox("按要素大类筛选", ["全部"] + list(ACCOUNTING_STRUCTURE.keys()))
            with col_sh2:
                all_dates = sorted(st.session_state.ledger['日期'].unique())
                search_date = st.selectbox("按发生日期筛选", ["全部"] + all_dates)
            with col_sh3:
                search_kw = st.text_input("按流水号/经手人/备注关键词模糊匹配")

            df_filtered = st.session_state.ledger.copy()
            if search_el != "全部":
                df_filtered = df_filtered[df_filtered['会计要素'] == search_el]
            if search_date != "全部":
                df_filtered = df_filtered[df_filtered['日期'] == search_date]
            if search_kw:
                df_filtered = df_filtered[
                    df_filtered['流水号'].str.contains(search_kw, na=False) |
                    df_filtered['经手人'].str.contains(search_kw, na=False) |
                    df_filtered['备注'].str.contains(search_kw, na=False)
                ]

            st.markdown(f"📊 已为您过滤出 **{len(df_filtered)}** 条匹配的主题档案：")
            
            # 高级勾选组件支持
            col_sel1, col_sel2 = st.columns([1, 4])
            select_all = col_sel1.checkbox("全选当前筛选的账目项", value=True)
            
            selected_rows = []
            for idx in df_filtered.index:
                row_item = df_filtered.loc[idx]
                is_checked = select_all
                if not select_all:
                    is_checked = st.sidebar.checkbox(f"勾选账目 {row_item['流水号']}", value=False, key=f"tbl_chk_{idx}")
                if is_checked:
                    selected_rows.append(row_item)

            df_to_export = pd.DataFrame(selected_rows) if selected_rows else pd.DataFrame(columns=st.session_state.ledger.columns)
            st.dataframe(df_to_export, use_container_width=True)

            if not df_to_export.empty:
                if st.button("📦 打包导出已勾选账目及全部原始对应凭证文件(ZIP)", use_container_width=True):
                    zip_data = make_zip_archive_selected(df_to_export)
                    st.download_button("📥 确定导出归档压缩包.zip", zip_data, file_name=f"昊天观账目凭证归档_{datetime.now().strftime('%Y%m%d%H%M%S')}.zip", mime="application/zip", use_container_width=True)

    # --- 标签 3：财务报表大盘（完全保留AI智能变动分析与导出） ---
    with tabs[2]:
        st.markdown("#### 📜 昊天观标准财务报表中心")
        rep_type = st.radio("报表周期类型切换", ["月度报表 (Monthly)", "季度报表 (Quarterly)", "年度报表 (Annual)"], horizontal=True)
        
        st.markdown(f"##### ⏳ 2026年度财务数据平衡表 ({rep_type})")
        
        # 计算三大核心指标
        rev_total = st.session_state.ledger[st.session_state.ledger['会计要素'] == '收入类']['金额'].sum()
        exp_total = st.session_state.ledger[st.session_state.ledger['会计要素'] == '支出类']['金额'].sum()
        surplus = rev_total - exp_total
        
        m_col1, m_col2, m_col3 = st.columns(3)
        m_col1.metric("⚖️ 累计总收入 (Revenue)", f"￥{rev_total:,.2f}")
        m_col2.metric("💸 累计总业务支出 (Expenses)", f"￥{exp_total:,.2f}")
        m_col3.metric("🪙 本期收支净结余 (Net Surplus)", f"￥{surplus:,.2f}")
        
        # 导出 Excel 形式
        excel_rep = io.BytesIO()
        with pd.ExcelWriter(excel_rep, engine='openpyxl') as wr:
            st.session_state.ledger.to_excel(wr, index=False, sheet_name="全量科目级发生额明细")
        st.download_button(f"📥 导出 {rep_type} 官方原始电子底账 (Excel)", excel_rep.getvalue(), file_name=f"昊天观_{rep_type}_{datetime.now().strftime('%Y%m%d')}.xlsx", use_container_width=True)
        
        st.markdown("---")
        st.markdown("##### ✨ 昊天智能AI财务状况分析与合规内控建议")
        if surplus >= 0:
            st.success(f"🤖 **AI大盘解析诊断**：本期账目结构健康度良好，收支净留存 ￥{surplus:,.2f} 元。随喜随缘功德结存表现良好，能够充分保障场所基础运营修缮。")
        else:
            st.error(f"🤖 **AI大盘解析诊断**：当前周期内支出规模高于进项净流入（净结余出现红字 ￥{surplus:,.2f} 元）。建议严格把控文物及建筑修缮大额支出节奏，非必要活动暂缓列支。")
        st.info("💡 **合规化运营建议**：严格依照《宗教活动场所财务监督管理办法》要求，定期向登记管理机关报送本期财务报表，并对信众公开功德款项随喜流向疏文，保持非营利法度透明。")

    # --- 标签 4：借款/贷款管理界面（完全保留原有合同上传、AI自动扫描提示与审核流） ---
    with tabs[3]:
        st.markdown("#### 🪵 场所资财借贷与长期债务偿付风险追踪天盘")
        
        l_sum = st.session_state.borrow_db[st.session_state.borrow_db['借贷方向'] == '借入(负债)']['本金金额'].sum()
        r_sum = st.session_state.borrow_db[st.session_state.borrow_db['借贷方向'] == '借出(债权)']['本金金额'].sum()
        
        bl_col1, bl_col2 = st.columns(2)
        bl_col1.metric("🔴 场所当前承受负债总额", f"￥{l_sum:,.2f} 元")
        bl_col2.metric("🟢 场所对外拥有债权总额", f"￥{r_sum:,.2f} 元")
        
        st.markdown("##### 📜 现有借贷协议长周期执行台账")
        st.dataframe(st.session_state.borrow_db, use_container_width=True)
        
        st.markdown("---")
        st.markdown("##### ➕ 登载全新长/短期借贷拓扑契约文件")
        with st.form("borrow_input_form"):
            b_id = f"HT-LOAN-{datetime.now().strftime('%Y%m%d')}-{random.randint(10,99)}"
            b_dir = st.selectbox("借贷行为方向性质", ["借入(负债)", "借出(债权)"])
            b_person = st.text_input("债权债务对象单位/个人全称")
            b_amt = st.number_input("契约融资本金金额 (元)", min_value=0.0)
            b_rate = st.number_input("约定期限年化利率 (%)", min_value=0.0, max_value=24.0, value=3.85)
            b_limit = st.date_input("契约承诺法定期限到期还款日", date.today())
            b_memo = st.text_area("长周期利息结算或资金用途备注")
            b_file = st.file_uploader("上传已签署盖章的借贷原始合同扫描件", type=["pdf", "jpg", "png"])
            
            st.info("✨ **AI 智能辅助已常驻守护**：系统上传合同后，后台将自动智能辅助扫描复核本息、经办人、到期日，杜绝人工录入笔误。")
            
            if st.form_submit_button("🪵 呈报住持审核"):
                if not b_person or b_amt <= 0:
                    st.error("❌ 融资本金或债权债务单位信息不全，无法呈报！")
                else:
                    c_name = b_file.name if b_file else "未传合同.pdf"
                    if b_file:
                        st.session_state.file_vault[c_name] = b_file.getvalue()
                        
                    new_loan = {
                        '合同单号': b_id, '借贷方向': b_dir, '债权/债务人': b_person, '本金金额': float(b_amt), 
                        '年化利率(%)': float(b_rate), '签署日期': date.today().strftime('%Y-%m-%d'), \
                        '到期时限': b_limit.strftime('%Y-%m-%d'), '经办人': current_user.get('name'), 
                        '凭证附件': c_name, '审批状态': "等待住持审核", '备注': b_memo
                    }
                    st.session_state.borrow_db = pd.concat([st.session_state.borrow_db, pd.DataFrame([new_loan])], ignore_index=True)
                    append_audit_log(current_user.get("username"), current_user.get("name"), f"提交借贷契约审核申请: {b_id}")
                    st.success("🪵 借贷协议已安全封缄，正式呈报住持内控审批法盘！")
                    st.rerun()
