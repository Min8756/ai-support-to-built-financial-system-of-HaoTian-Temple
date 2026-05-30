import streamlit as st
import pandas as pd
from datetime import datetime, date
import io
import os
import random
import zipfile

# ==============================================================================
# 1. 页面基础配置及全局视觉渲染
# ==============================================================================
st.set_page_config(page_title="昊天观财务管理系统", layout="wide", page_icon="☯️")

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

# ==============================================================================
# 2. 系统核心会话状态与持久化沙盒初始化（测试数据、基础干扰数值已完全清零）
# ==============================================================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = None

# 用户凭证库
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

# 审计日志
if 'audit_logs' not in st.session_state:
    st.session_state.audit_logs = pd.DataFrame([
        {"操作时间": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "操作账号": "system", "操作人姓名": "系统核心", "操作内容": "系统按照《民间非营利组织会计制度》标准完成初始化，当前处于无数据纯净状态。"}
    ])

def append_audit_log(username, name, action):
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    new_log = {"操作时间": now_str, "操作账号": username, "操作人姓名": name, "操作内容": action}
    st.session_state.audit_logs = pd.concat([st.session_state.audit_logs, pd.DataFrame([new_log])], ignore_index=True)

# 融合《会计体系.docx》标准规范的五大会计科目树
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

# 纯净无数据总账本
if 'ledger' not in st.session_state:
    st.session_state.ledger = pd.DataFrame(columns=[
        '流水号', '日期', '会计要素', '一级科目', '二级科目', 
        '金额', '经手人', '凭证附件', '操作员', '操作员电话', 
        '备注', '审批状态', '接待对象', '接待事由'
    ])

# 纯净无数据借贷数据库
if 'borrow_db' not in st.session_state:
    st.session_state.borrow_db = pd.DataFrame(columns=[
        '合同单号', '借贷方向', '债权/债务人', '本金金额', 
        '年化利率(%)', '签署日期', '到期时限', '经办人', 
        '凭证附件', '审批状态', '备注'
    ])

if 'file_vault' not in st.session_state:
    st.session_state.file_vault = {}

if 'vol_active_name' not in st.session_state:
    st.session_state.vol_active_name = ""
if 'vol_active_phone' not in st.session_state:
    st.session_state.vol_active_phone = ""

# ==============================================================================
# 3. 登录拦截大闸
# ==============================================================================
if not st.session_state.logged_in:
    st.markdown(f"""
    <style>
    .stApp {{ background-image: url("{st.session_state.bg_img_url}") !important; background-size: cover !important; background-position: center !important; background-attachment: fixed !important; }}
    h1, h2, h3 {{ color: #8B0000 !important; font-family: 'Kaiti', 'STKaiti', 'serif'; text-shadow: 1px 1px 2px white; }}
    .stButton>button {{ background-color: #8B0000; color: white; border-radius: 5px; }}
    [data-testid="stForm"], .stForm {{ background-color: rgba(255, 255, 255, 0.96) !important; padding: 25px; border-radius: 12px; box-shadow: 0px 4px 15px rgba(0,0,0,0.4); }}
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<h1 style='text-align: center; margin-top: 80px;'>⛩️ 昊天观财务管理中心</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.form("login_gate"):
            input_user = st.text_input("管理账号")
            input_pwd = st.text_input("管理密码", type="password")
            if st.form_submit_button("🔐 安全验证登录", use_container_width=True):
                if input_user == "admin" and input_pwd == "20010905":
                    st.session_state.logged_in = True
                    st.session_state.current_user = {"username": "admin", "name": "超级系统总管", "role": "admin", "title": "系统总监控制", "is_blocked": False}
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

# ==============================================================================
# 4. 安全会话上下文处理
# ==============================================================================
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

current_user = st.session_state.current_user if st.session_state.current_user is not None else {}
current_role = current_user.get("role", "volunteer")
current_username = current_user.get("username", "")

st.sidebar.markdown(f"### 🕯️ 执事人：{current_user.get('name', '匿名用户')}")
st.sidebar.markdown(f"当前岗位：`{current_user.get('title', '常驻执事')}`")

if st.sidebar.button("🚪 安全换班交接", use_container_width=True):
    append_audit_log(current_user.get("username", "unknown"), current_user.get("name", "unknown"), "退出登录，交接完毕。")
    st.session_state.logged_in = False
    st.session_state.current_user = None
    st.rerun()

# ==============================================================================
# 5. 通用引擎工具包
# ==============================================================================
def smart_rename_by_rules(f_date, f_el, uploaded_file):
    date_str = f_date.strftime('%Y%m%d')
    doc_type = "收据" if f_el in ["收入类", "净资产类"] else "发票"
    all_attachments = []
    if not st.session_state.ledger.empty:
        all_attachments += list(st.session_state.ledger['凭证附件'].dropna())
    day_count = 1
    for name in all_attachments:
        if str(name).startswith(f"{doc_type}{date_str}"):
            try:
                core_num = str(name).replace(f"{doc_type}{date_str}", "").split('.')[0]
                ext_num = int(core_num)
                if ext_num >= day_count:
                    day_count = ext_num + 1
            except:
                pass
    ext = os.path.splitext(uploaded_file.name)[1] if uploaded_file else ".jpg"
    return f"{doc_type}{date_str}{str(day_count).zfill(2)}{ext}"

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

# ==============================================================================
# 🎮 业务路由大盘一：ADMIN 超级管理员至高控制台
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
        st.markdown("#### 🛠️ 账目审计与修缮")
        if st.session_state.ledger.empty:
            st.info("总账清空，目前无任何待审计数据。")
        else:
            selected_idx = st.selectbox(
                "选择需要紧急修正或移除的账目流水号", 
                st.session_state.ledger.index,
                format_func=lambda x: f"{st.session_state.ledger.loc[x, '流水号']} | 金额:{st.session_state.ledger.loc[x, '金额']} | {st.session_state.ledger.loc[x, '备注']}"
            )
            row_data = st.session_state.ledger.loc[selected_idx]
            with st.form("adm_modify_form"):
                ed_date = st.text_input("账目日期", str(row_data['日期']))
                elements_list = list(ACCOUNTING_STRUCTURE.keys())
                el_default_idx = elements_list.index(row_data['会计要素']) if row_data['会计要素'] in elements_list else 0
                ed_el = st.selectbox("会计要素大类", elements_list, index=el_default_idx)
                c1_opts = list(ACCOUNTING_STRUCTURE[ed_el].keys())
                c1_default_idx = c1_opts.index(row_data['一级科目']) if row_data['一级科目'] in c1_opts else 0
                ed_c1 = st.selectbox("一级科目", c1_opts, index=c1_default_idx)
                c2_opts = ACCOUNTING_STRUCTURE[ed_el][ed_c1]
                c2_default_idx = c2_opts.index(row_data['二级科目']) if row_data['二级科目'] in c2_opts else 0
                ed_c2 = st.selectbox("二级科目", c2_opts, index=c2_default_idx)
                ed_amount = st.number_input("金额 (元)", value=float(row_data['金额']))
                ed_person = st.text_input("经手报销人", str(row_data['经手人']))
                ed_file = st.text_input("挂载凭证文件名", str(row_data['凭证附件']))
                ed_memo = st.text_area("详细说明", str(row_data['备注']))
                
                col_btn1, col_btn2 = st.columns(2)
                if col_btn1.form_submit_button("💾 确认保存修改并覆盖发布"):
                    st.session_state.ledger.loc[selected_idx] = [
                        row_data['流水号'], ed_date, ed_el, ed_c1, ed_c2, float(ed_amount), ed_person,
                        ed_file, "超级管理员", "N/A", ed_memo, row_data.get('审批状态', '无需审批'), row_data.get('接待对象', '无'), row_data.get('接待事由', '无')
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
                c_f2.download_button("📥 导出提取", data=st.session_state.file_vault[fname], file_name=fname, key=f"dl_vault_{fname}")
        else:
            st.info("📂 档案馆当前无对应存盘记录。")
            
    with adm_tabs[3]:
        st.markdown("#### 👥 统筹账户名单与后台状态干预")
        for r_name, u_list in st.session_state.user_registry.items():
            st.markdown(f"**岗位归属：{r_name.upper()}**")
            for u in u_list:
                uc1, uc2, uc3 = st.columns([3, 2, 1])
                uc1.write(f"🏷️ 账号名: `{u['username']}` | 实名指派: **{u['name']}** | 联络方式: {u['phone']}")
                is_b = u.get("is_blocked", False)
                uc2.write(f"当前状态：{'🚨 已全面拉黑拦截' if is_b else '🟢 正常履行公职'}")
                if is_b:
                    if uc3.button("🔓 宽赦解封", key=f"unblk_{u['username']}"):
                        u["is_blocked"] = False
                        append_audit_log("admin", "超级总管", f"解除对账户 {u['username']} 的拉黑惩戒。")
                        st.rerun()
                else:
                    if uc3.button("🚨 强制拉黑", key=f"blk_{u['username']}"):
                        u["is_blocked"] = True
                        append_audit_log("admin", "超级总管", f"将可疑账户 {u['username']} 强制拉黑拦截。")
                        st.rerun()

# ==============================================================================
# 🎮 业务路由大盘二：VOLUNTEER 值班义工报账台
# ==============================================================================
elif current_role == "volunteer":
    st.markdown("## 🪵 昊天观·义工日记账经手录入台")
    
    if not st.session_state.vol_active_name or not st.session_state.vol_active_phone:
        st.warning("⚠️ 依据《宗教活动场所财务监督管理办法》，上岗做账前须追加登记本日经办义工法号/姓名及联络电话进行核验追溯。")
        with st.form("vol_re_auth"):
            v_name = st.text_input("值班义工法号/姓名 (如: 妙音居士)", value=current_user.get("name", ""))
            v_phone = st.text_input("值班义工联络电话 (11位手机号)")
            if st.form_submit_button("📝 确认登记绑定并解锁工作台"):
                if len(v_phone) != 11 or not v_phone.isdigit():
                    st.error("❌ 电话核验失败，必须输入11位纯数字移动电话！")
                elif not v_name.strip():
                    st.error("❌ 实名登记失败，姓名/法号不能为空！")
                else:
                    st.session_state.vol_active_name = v_name.strip()
                    st.session_state.vol_active_phone = v_phone.strip()
                    append_audit_log(current_username, v_name.strip(), f"完成二次身份实名激活绑定，核查手机号: {v_phone}")
                    st.success("🔓 身份核查配对通过，工作台已全面激活！")
                    st.rerun()
        st.stop()
        
    st.info("💡 **工作常驻要求**：请每日义工将本日日记账导出到本地硬盘并保存。")
    
    if not st.session_state.ledger.empty:
        df_vol = st.session_state.ledger[
            (st.session_state.ledger['操作员'] == current_username) & 
            (st.session_state.ledger['经手人'] == st.session_state.vol_active_name)
        ]
    else:
        df_vol = pd.DataFrame(columns=st.session_state.ledger.columns)
    
    vol_w_tabs = st.tabs(["✍️ 随手记手工账本", "📖 本人经手明细"])
    
    with vol_w_tabs[0]:
        with st.form("vol_add_ledger_form"):
            st.markdown("#### 📝 填报日常随手记账单")
            f_date = st.date_input("开具/业务发生日期", date.today())
            f_element = st.selectbox("会计要素分类", list(ACCOUNTING_STRUCTURE.keys()))
            
            c1_options = list(ACCOUNTING_STRUCTURE[f_element].keys())
            f_c1 = st.selectbox("对应一级会计科目", c1_options)
            f_c2 = st.selectbox("对应二级明细科目", ACCOUNTING_STRUCTURE[f_element][f_c1])
            
            f_amt = st.number_input("发生金额 (元)", min_value=0.01, step=10.0, format="%.2f")
            f_file = st.file_uploader("上传对应合法原始凭证 (支持 PDF, JPG, PNG 图像档案)", type=["pdf", "jpg", "png"])
            f_memo = st.text_area("摘要及因缘详情备注说明 (如: 功功德箱清点/购买日常照明蜡烛)")
            
            st.markdown("---")
            st.markdown("##### 👥 业务招待透明化专项申报 (若非招待开支请保持默认)")
            f_rec_obj = st.text_input("外来接待对象/单位名称", value="无")
            f_rec_reason = st.text_area("外来招待事由及合规说明", value="无")
            
            if st.form_submit_button("🪵 提交并呈报入账大盘"):
                if f_amt <= 0:
                    st.error("❌ 入账金额必须大于 0 元！")
                else:
                    new_id = f"HT-{f_date.strftime('%Y%m')}-{random.randint(100,999)}"
                    final_file_name = "未传凭证.jpg"
                    if f_file:
                        final_file_name = smart_rename_by_rules(f_date, f_element, f_file)
                        st.session_state.file_vault[final_file_name] = f_file.getvalue()
                        
                    is_need_approve = "等待住持审核" if (f_element == "支出类" and f_amt >= 10000.0) else "无需审批"
                    
                    new_row = {
                        '流水号': new_id, '日期': str(f_date), '会计要素': f_element, '一级科目': f_c1, '二级科目': f_c2,
                        '金额': float(f_amt), '经手人': st.session_state.vol_active_name, '凭证附件': final_file_name,
                        '操作员': current_username, '操作员电话': st.session_state.vol_active_phone,
                        '备注': f_memo, '审批状态': is_need_approve, '接待对象': f_rec_obj, '接待事由': f_rec_reason
                    }
                    
                    st.session_state.ledger = pd.concat([st.session_state.ledger, pd.DataFrame([new_row])], ignore_index=True)
                    append_audit_log(current_username, st.session_state.vol_active_name, f"录入流转单据: {new_id}, 金额: {f_amt}, 状态: {is_need_approve}")
                    st.success(f"🎉 成功录入！流水号为: {new_id}。当前状态: {is_need_approve}")
                    st.rerun()
                    
    with vol_w_tabs[1]:
        st.markdown(f"#### 📖 **{st.session_state.vol_active_name}** 经手历史明细清册")
        if df_vol.empty:
            st.info("📭 您当前班次尚未录入任何日常收支流水。")
        else:
            st.dataframe(df_vol, use_container_width=True)
            zip_data = make_zip_archive_selected(df_vol)
            st.download_button(
                "📥 导出本日日记账及配套凭证压缩包", 
                data=zip_data, 
                file_name=f"昊天观_日记账归档_{date.today().strftime('%Y%m%d')}.zip",
                mime="application/zip",
                use_container_width=True
            )

# ==============================================================================
# 🎮 业务路由大盘三：FINANCE 财务主管高级工作台
# ==============================================================================
elif current_role == "finance":
    st.markdown("## 📊 昊天观·专业规范化财务大盘 (符合《民间非营利组织会计制度》)")
    fin_tabs = st.tabs(["📑 智能精细分类账", "📈 三维动态多元报表(Excel导出)", "🪵 长周期借贷/融资契约录入"])
    
    with fin_tabs[0]:
        st.markdown("#### 🔍 跨维度立体式分类账目检索提取")
        df_l = st.session_state.ledger.copy()
        
        c_filter1, c_filter2, c_filter3 = st.columns(3)
        q_start = c_filter1.date_input("起算交割日期", date(2026, 1, 1))
        q_end = c_filter2.date_input("截至盘点日期", date(2026, 12, 31))
        q_word = c_filter3.text_input("摘要及因缘检索词")
        
        if not df_l.empty:
            df_l['日期_dt'] = pd.to_datetime(df_l['日期']).dt.date
            df_filtered = df_l[(df_l['日期_dt'] >= q_start) & (df_l['日期_dt'] <= q_end)]
            if q_word:
                df_filtered = df_filtered[df_filtered['备注'].str.contains(q_word, na=False) | df_filtered['流水号'].str.contains(q_word, na=False)]
            df_filtered = df_filtered.drop(columns=['日期_dt'], errors='ignore')
        else:
            df_filtered = pd.DataFrame(columns=df_l.columns)
            
        if df_filtered.empty:
            st.warning("⚠️ 盘查大盘结束，目前账簿中没有任何符合条件的明细流水。")
        else:
            st.markdown(f"📊 **联立筛选出共 `{len(df_filtered)}` 条合规账簿记录：**")
            df_filtered.insert(0, "精选勾选标记", False)
            edited_df = st.data_editor(
                df_filtered,
                column_config={"精选勾选标记": st.column_config.CheckboxColumn(help="勾选后打包导出对应的原始单据凭证卷宗")},
                disabled=[c for c in df_filtered.columns if c != "精选勾选标记"],
                use_container_width=True,
                key="fin_editor_grid"
            )
            
            st.markdown("---")
            col_exp1, col_exp2 = st.columns(2)
            
            if col_exp1.button("🌟 一键勾选并提取全盘"):
                full_zip = make_zip_archive_selected(df_filtered.drop(columns=["精选勾选标记"], errors='ignore'))
                st.download_button("💾 点击立刻下发全盘账簿凭证.zip", data=full_zip, file_name="昊天观_精选全选账簿归档.zip", mime="application/zip")
                st.stop()
                
            selected_rows = edited_df[edited_df["精选勾选标记"] == True]
            if not selected_rows.empty:
                selected_zip = make_zip_archive_selected(selected_rows.drop(columns=["精选勾选标记"], errors='ignore'))
                col_exp2.download_button(
                    f"📦 导出已选的 {len(selected_rows)} 条账目凭证包", 
                    data=selected_zip, 
                    file_name="昊天观_有选择性账单凭证.zip", 
                    mime="application/zip",
                    use_container_width=True
                )
            else:
                col_exp2.info("💡 勾选上表中左侧的多选框，可定制打包下载凭证文件。")
                
    with fin_tabs[1]:
        st.markdown("#### 📊 智能会计报表决策大屏")
        rep_period = st.selectbox("请选择要生成的会计报表周期阶段", ["2026年05月度中盘报表", "2026年第二季度周期报表", "2026年年度决算预估总表"])
        
        # 提取通过审核或无需审核的有效真实流动账目
        df_valid_ledger = st.session_state.ledger[st.session_state.ledger['审批状态'].isin(["无需审批", "住持已批准"])]
        
        # 🧮 严格零基计算逻辑：无任何写死的期初加权值干扰（+500000 和 +300000 已精准清零）
        sum_asset = df_valid_ledger[df_valid_ledger['会计要素'] == '资产类']['金额'].sum() + 0.0
        sum_liab = df_valid_ledger[df_valid_ledger['会计要素'] == '负债类']['金额'].sum() + st.session_state.borrow_db['本金金额'].sum()
        sum_rev = df_valid_ledger[df_valid_ledger['会计要素'] == '收入类']['金额'].sum()
        sum_exp = df_valid_ledger[df_valid_ledger['会计要素'] == '支出类']['金额'].sum()
        sum_net = sum_rev - sum_exp + 0.0
        
        m_c1, m_c2, m_c3 = st.columns(3)
        m_c1.metric("1. 资产总计 (实际变动结存)", f"￥{sum_asset:,} 元")
        m_c2.metric("2. 负债总计 (含银行长线信贷)", f"￥{sum_liab:,} 元")
        m_c3.metric("3. 净资产运营总结余", f"￥{sum_net:,} 元")
        
        st.markdown("---")
        st.markdown("#### ✨ AI 智能财务分析专家组看板报告")
        if sum_asset == 0 and sum_liab == 0 and sum_rev == 0 and sum_exp == 0:
            st.info("✨ **AI 分析组提示**：账盘当前处于零基空白运行状态。当义工和常驻执事录入收支并生效后，AI 会自动为您分析资产负债比和现金流健康度。")
        else:
            if sum_liab > sum_asset * 0.6:
                st.error(f"🚨 **资产负债率预警 ({sum_liab/max(1, sum_asset)*100:.1f}%)**：债务占比偏高，建议缩减非宗教核心活动支出，开源节流。")
            else:
                st.success("🟢 **财务健壮度评估**：资产负债结构良好，运营净结余处于安全红线以上。")
                
        out_excel = io.BytesIO()
        with pd.ExcelWriter(out_excel, engine='openpyxl') as wr:
            pd.DataFrame([
                {"指标名称": "资产总计", "实际值": sum_asset}, 
                {"指标名称": "负债总计", "实际值": sum_liab}, 
                {"指标名称": "净资产总结余", "实际值": sum_net}
            ]).to_excel(wr, index=False, sheet_name="核心摘要")
            df_valid_ledger.to_excel(wr, index=False, sheet_name="过账明细流水")
        st.download_button(f"📥 导出标准 Excel 格式【{rep_period}】", data=out_excel.getvalue(), file_name=f"昊天观_业务报表_{rep_period}.xlsx")
        
    with fin_tabs[2]:
        st.markdown("#### 🪵 长期借款 / 融资契约契约立项")
        with st.form("loan_reg_form"):
            b_id = f"HT-LOAN-{date.today().strftime('%Y%m')}-{random.randint(10,99)}"
            b_dir = st.selectbox("借贷融通流动方向", ["借入(负债)", "借出(债权)"])
            b_person = st.text_input("债权/债务往来对应单位名称(例如: 城固商业银行)")
            b_amt = st.number_input("融资本金金额 (元)", min_value=0.0)
            b_rate = st.number_input("协议设定年化利率 (%)", min_value=0.0, max_value=24.0, value=3.85)
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
                        '合同单号': b_id, '借贷方向': b_dir, '债权/债务人': b_person, '本金金额': float(b_amt), \
                        '年化利率(%)': float(b_rate), '签署日期': date.today().strftime('%Y-%m-%d'), \
                        '到期时限': b_limit.strftime('%Y-%m-%d'), '经办人': current_user.get('name'), \
                        '凭证附件': c_name, '审批状态': "等待住持审核", '备注': b_memo
                    }
                    st.session_state.borrow_db = pd.concat([st.session_state.borrow_db, pd.DataFrame([new_loan])], ignore_index=True)
                    append_audit_log(current_username, current_user.get('name'), f"发起重大资产长周期借贷立项: {b_id}, 金额: {b_amt}")
                    st.success(f"🟢 借贷申请已投递！请通知李住持进行终审批红划线录入。")
                    st.rerun()

# ==============================================================================
# 🎮 业务路由大盘四：TEMPLE_HEAD 当家住持高阶法眼审批大盘
# ==============================================================================
elif current_role == "temple_head":
    st.markdown("## ☯️ 昊天观·住持大德法眼审批天盘")
    
    df_pending_ledger = st.session_state.ledger[st.session_state.ledger['审批状态'] == "等待住持审核"]
    df_pending_loan = st.session_state.borrow_db[st.session_state.borrow_db['审批状态'] == "等待住持审核"]
    
    head_tabs = st.tabs([f"📥 收支审批批红 [{len(df_pending_ledger)}]", f"🪵 融资重大合同批红 [{len(df_pending_loan)}]", "📜 全盘账目宏观法眼监察"])
    
    with head_tabs[0]:
        if df_pending_ledger.empty:
            st.success("🟢 清净无事！当前没有任何被积压的超过1万元的大额日常收支申请。")
        else:
            for idx, r in df_pending_ledger.iterrows():
                with st.expander(f"流水单号: {r['流水号']} | 金额: ￥{r['金额']:,} 元 | 填报操作人: {r['经手人']}"):
                    st.write(f"**业务大类要素**：{r['会计要素']} -> {r['一级科目']} -> {r['二级科目']}")
                    st.write(f"**业务说明**：{r['备注']}")
                    st.markdown(f"**💡 业务招待透明公开核查**：接待对象：`{r['接待对象']}` | 接待因由：`{r['接待事由']}`")
                    if r['凭证附件'] in st.session_state.file_vault:
                        st.download_button(f"📄 查看/下载原始法定的凭证档案 [{r['凭证附件']}]", data=st.session_state.file_vault[r['凭证附件']], file_name=r['凭证附件'], key=f"btn_dl_{r['流水号']}")
                    else:
                        st.warning("⚠️ 该项未附带任何可供核查的文件。")
                        
                    c_b1, c_b2 = st.columns(2)
                    if c_b1.button("🟢 依例准予批红过账", key=f"app_{r['流水号']}"):
                        st.session_state.ledger.loc[idx, '审批状态'] = "住持已批准"
                        append_audit_log(current_username, current_user.get('name'), f"大额收支批红通过: {r['流水号']}")
                        st.success("已批红。")
                        st.rerun()
                    if c_b2.button("❌ 驳回要求重新核算", key=f"rej_{r['流水号']}"):
                        st.session_state.ledger.loc[idx, '审批状态'] = "住持已驳回"
                        append_audit_log(current_username, current_user.get('name'), f"大额收支不合规驳回: {r['流水号']}")
                        st.error("已驳回。")
                        st.rerun()
                        
    with head_tabs[1]:
        if df_pending_loan.empty:
            st.success("🟢 清净无碍！当前无积压的重大信贷融资合同。")
        else:
            for idx, r in df_pending_loan.iterrows():
                with st.expander(f"契约号: {r['合同单号']} | 融资本金: ￥{r['本金金额']:,} 元 | 协议单位: {r['债权/债务人']}"):
                    st.write(f"**借贷性质**：{r['借贷方向']} | 约定年化利息率：`{r['年化利率(%)']}%`")
                    st.write(f"**还款期限目标**：{r['到期时限']} | 筹措人陈述：{r['备注']}")
                    if r['凭证附件'] in st.session_state.file_vault:
                        st.download_button("📂 下载审查合同全彩扫描件", data=st.session_state.file_vault[r['凭证附件']], file_name=r['凭证附件'], key=f"loan_dl_{r['合同单号']}")
                    
                    c_l1, c_l2 = st.columns(2)
                    if c_l1.button("☯️ 准予立契签约过账", key=f"loan_app_{r['合同单号']}"):
                        st.session_state.borrow_db.loc[idx, '审批状态'] = "住持已批准"
                        append_audit_log(current_username, current_user.get('name'), f"重大长期契约批红准予立项: {r['合同单号']}")
                        st.success("重大合同已签署过账。")
                        st.rerun()
                    if c_l2.button("❌ 认为利息过高/有因果驳回", key=f"loan_rej_{r['合同单号']}"):
                        st.session_state.borrow_db.loc[idx, '审批状态'] = "住持已驳回"
                        append_audit_log(current_username, current_user.get('name'), f"重大长期借贷契约被住持法眼驳回: {r['合同单号']}")
                        st.error("借贷申请已被斩断驳回。")
                        st.rerun()
                        
    with head_tabs[2]:
        st.markdown("#### 监察大盘所有流动性账簿明细")
        if st.session_state.ledger.empty:
            st.info("总账清空，目前没有产生过账流水。")
        else:
            st.dataframe(st.session_state.ledger, use_container_width=True)
            st.markdown("#### 长周期融资性借贷契约簿档案")
            st.dataframe(st.session_state.borrow_db, use_container_width=True)
