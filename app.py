import streamlit as st
import pandas as pd
from datetime import datetime
import random
import io
import os
import base64

# 1. 页面基础配置
st.set_page_config(page_title="昊天观财务管理系统", layout="wide", page_icon="☯️")

# --- 2. 持久化配置文件路径 ---
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

# 初始化视觉配置
saved_bg, saved_theme = load_visual_config()
if 'bg_img_url' not in st.session_state:
    st.session_state.bg_img_url = saved_bg
if 'op_theme_color' not in st.session_state:
    st.session_state.op_theme_color = saved_theme

# --- 3. 动态 CSS 视觉控制 ---
if not st.session_state.get('logged_in', False) or (st.session_state.get('logged_in', False) and st.session_state.get('current_user', {}).get('role') == 'volunteer' and not st.session_state.get('volunteer_registered', False)):
    # 登录页及义工未登记页：载入精美神明全景背景
    st.markdown(f"""
        <style>
        .stApp {{ 
            background-image: url("{st.session_state.bg_img_url}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            color: #2F2F2F; 
        }}
        [data-testid="stSidebar"] {{ background-color: rgba(245, 245, 222, 0.85); border-right: 2px solid #8B4513; }}
        h1, h2, h3 {{ color: #8B0000 !important; font-family: 'Kaiti', 'STKaiti', 'serif'; text-shadow: 1px 1px 2px white; }}
        .stButton>button {{ background-color: #8B0000; color: white; border-radius: 5px; border: 1px solid #D2691E; }}
        [data-testid="stForm"], .stForm, div[data-testid="stContainer"] {{ background-color: rgba(255, 255, 255, 0.92) !important; padding: 25px; border-radius: 12px; box-shadow: 0px 4px 15px rgba(0,0,0,0.2); }}
        </style>
        """, unsafe_allow_html=True)
else:
    # 核心做账后台：纯色极简保护视力
    st.markdown(f"""
        <style>
        .stApp {{ 
            background-color: {st.session_state.op_theme_color} !important;
            background-image: none !important; 
            color: #2F2F2F; 
        }}
        [data-testid="stSidebar"] {{ background-color: #F5F5DC !important; border-right: 2px solid #8B4513; }}
        h1, h2, h3 {{ color: #8B0000 !important; font-family: 'Kaiti', 'STKaiti', 'serif'; }}
        [data-testid="stMetricValue"] {{ color: #8B0000 !important; font-weight: bold; }}
        .stButton>button {{ background-color: #8B0000; color: white; border-radius: 5px; border: 1px solid #D2691E; }}
        .stAlert {{ background-color: #FFF8DC; border: 1px solid #D2691E; }}
        [data-testid="stForm"], .stForm, div[data-testid="stContainer"] {{ background-color: #FFFFFF !important; padding: 20px; border-radius: 10px; border: 1px solid #E0DDC8; }}
        </style>
        """, unsafe_allow_html=True)

# --- 4. 初始化业务数据库 (内置真实演示流水) ---
if 'ledger' not in st.session_state:
    test_data = [
        {'日期': '2026-05-20', '类型': '收入', '一级科目': '捐赠性收入(非经营)', '二级科目': '信众随喜功德款', '税收属性': '免税资产', '金额': 5000.0, '经手人/功德主': '王居士', '票据凭证': '收据001.jpg', '操作人姓名': '张会计', '操作人手机': '13911112222', '备注': '太上老君圣诞供灯随喜'},
        {'日期': '2026-05-22', '类型': '支出', '一级科目': '场所日常维护', '二级科目': '水电开支', '税收属性': '不涉及税项', '金额': 1200.5, '经手人/功德主': '自来水公司', '票据凭证': '发票_W2026.pdf', '操作人姓名': '张会计', '操作人手机': '13911112222', '备注': '缴大殿水费'},
        {'日期': '2026-05-25', '类型': '收入', '一级科目': '功德箱收入', '二级科目': '信众随喜功德款', '税收属性': '免税资产', '金额': 18500.0, '经手人/功德主': '大殿功德箱', '票据凭证': '清点三人签字单.png', '操作人姓名': '李住持', '操作人手机': '13566668888', '备注': '开启功德箱清点款项'},
        {'日期': '2026-05-28', '类型': '支出', '一级科目': '场所建设与修缮', '二级科目': '日常维修与施工支出', '税收属性': '不涉及税项', '金额': 85000.0, '经手人/功德主': '古建维修队', '票据凭证': '工程合同.jpg', '操作人姓名': '李住持', '操作人手机': '13566668888', '备注': '修缮山门殿东侧漏水屋面'}
    ]
    st.session_state.ledger = pd.DataFrame(test_data)

if 'borrow_ledger' not in st.session_state:
    test_borrow = [
        {'借款单号': 'HT-BORROW-001', '借款日期': '2026-02-15', '债权人/借款方': '城固商业银行', '借款总额': 500000.0, '已还金额': 200000.0, '本金还款时限': '2026-12-31', '下次结息日': '2026-06-20', '应交利息(元)': 4800.0, '经手人': '李住持', '备注': '筹措斋堂扩建工程款'},
        {'借款单号': 'HT-BORROW-002', '借款日期': '2026-05-10', '债权人/借款方': '陈大护法居士', '借款总额': 100000.0, '已还金额': 0.0, '本金还款时限': '2026-10-01', '下次结息日': '无息借款', '应交利息(元)': 0.0, '经手人': '张会计', '备注': '修缮款临时头寸垫付'}
    ]
    st.session_state.borrow_ledger = pd.DataFrame(test_borrow)

if 'audit_logs' not in st.session_state:
    st.session_state.audit_logs = pd.DataFrame(columns=['时间', '账号', '责任人/操作员', '操作类型', '详细内容'])
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'volunteer_registered' not in st.session_state:
    st.session_state.volunteer_registered = False

# 管理员预设账户数据库
if 'user_db' not in st.session_state:
    st.session_state.user_db = {
        "volunteer": {"password": "ht123", "role": "volunteer", "title": "值班义工", "name": "待挂单登记", "phone": "待挂单登记"},
        "finance": {"password": "ht456", "role": "finance", "title": "财务工作人员", "name": "张会计", "phone": "13911112222"},
        "haotianguan": {"password": "ht789", "role": "temple_head", "title": "当家/监院住持", "name": "李住持", "phone": "13566668888"}
    }

def log_action(username, operator_name, action_type, detail):
    new_log = {'时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '账号': username, '责任人/操作员': operator_name, '操作类型': action_type, '详细内容': detail}
    st.session_state.audit_logs = pd.concat([st.session_state.audit_logs, pd.DataFrame([new_log])], ignore_index=True)

def to_excel_stream(dataframe):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        dataframe.to_excel(writer, index=False, sheet_name="昊天观账目数据")
    return output.getvalue()

# --- 5. 纯净极简登录界面（无姓名、手机号输入框） ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; margin-top: 80px;'>昊天观财务管理系统</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #FFF; text-shadow: 1px 1px 3px black;'>玄门清净账目 · 内控审计空间</p>", unsafe_allow_html=True)
    
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
                
                if input_user == "volunteer":
                    st.session_state.volunteer_registered = False  # 义工需要二阶段挂单
                else:
                    st.session_state.volunteer_registered = True   # 住持财务由管理员设置好，直接跳过
                    
                log_action(input_user, target_user["name"], "账号密码登录", "密码验证无误")
                st.rerun()
            else:
                st.error("❌ 账号或密码不匹配，请重新输入。")
    st.stop()

# --- 5.5 义工二次实名挂单登记大厅 ---
if st.session_state.current_user["role"] == "volunteer" and not st.session_state.volunteer_registered:
    st.markdown("<h2 style='text-align: center; margin-top: 80px;'>⛩️ 功德流转 · 值班义工挂单登记</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.form("volunteer_reg_form"):
            st.markdown("💡 *根据岗位分离原则，值班义工请在此登记今日当值法名与手机，以便入账时自动留痕审计。*")
            v_name = st.text_input("✨ 请输入真实姓名 / 法名", placeholder="例如：张居士 / 妙音居士")
            v_phone = st.text_input("📱 请输入联系手机号", placeholder="11位手机号码")
            
            if st.form_submit_button("🔥 登记录入，开门交班"):
                if not v_name or len(v_phone) != 11:
                    st.error("❌ 请完整且正确地填写姓名和11位手机号！")
                else:
                    st.session_state.current_user["name"] = v_name
                    st.session_state.current_user["phone"] = v_phone
                    st.session_state.volunteer_registered = True
                    log_action("volunteer", v_name, "义工二次挂单", f"实名绑定电话：{v_phone}")
                    st.success("🎉 登记成功！正在为您打开账簿大盘...")
                    st.rerun()
    st.stop()


# --- 6. 核心系统内部控制后台 ---
current_user = st.session_state.current_user
current_role = current_user["role"]

# 侧边栏常驻法相岗位信息
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
# 权限大类 1：超级控制台修改空间 (admin)
# ==========================================
if current_role == "admin":
    st.markdown("## 🛠️ 超级控制台修改空间")
    t1, t2, t3 = st.tabs(["📊 全局流水物理修正", "🎨 网页视觉资产配置", "👥 审计追溯明细"])
    
    with t1:
        st.markdown("### 🔒 数据库大盘底层物理修正区")
        # 铁律1：设置显式开关按钮，按下后才允许修改
        if 'allow_edit_ledger' not in st.session_state:
            st.session_state.allow_edit_ledger = False
            
        col_btn1, col_btn2 = st.columns([1, 4])
        with col_btn1:
            if st.button("🔑 启动底层数据修正", type="primary"):
                st.session_state.allow_edit_ledger = True
            if st.button("🔒 锁定关闭修正功能"):
                st.session_state.allow_edit_ledger = False
                
        if st.session_state.allow_edit_ledger:
            st.warning("⚠️ 警告：当前处于高级修正模式，点击单元格可直接修改，或在底栏增减行。")
            edited_ledger = st.data_editor(st.session_state.ledger, num_rows="dynamic", use_container_width=True)
            if st.button("💾 保存物理强制更动内容"):
                st.session_state.ledger = edited_ledger
                log_action("admin", "超级管理员", "物理强更数据库", "修改了账目流水底层数据")
                st.success("✨ 底层物理数据已强制重写落盘！")
                st.rerun()
        else:
            st.info("🔒 修正模式已锁定。下方仅做底盘数据纯读展示，无法涂改。")
            st.dataframe(st.session_state.ledger, use_container_width=True)
            
    with t2:
        st.markdown("### 🖼️ 登录界面背景图像自主设置")
        uploaded_bg = st.file_uploader("📥 导入本地图片重新设置登录背景", type=["png", "jpg", "jpeg"])
        if uploaded_bg is not None:
            st.image(uploaded_bg, caption="当前导入的原始图像预览", use_container_width=True)
            if st.button("💾 确认永久保存背景", type="primary"):
                bytes_data = uploaded_bg.read()
                b64_str = base64.b64encode(bytes_data).decode()
                final_bg_url = f"data:image/png;base64,{b64_str}"
                st.session_state.bg_img_url = final_bg_url
                save_visual_config(final_bg_url, st.session_state.op_theme_color)
                st.success("✨ 图像设置成功！")
                st.rerun()
        if st.button("🔄 恢复系统默认背景"):
            st.session_state.bg_img_url = DEFAULT_BG
            save_visual_config(DEFAULT_BG, st.session_state.op_theme_color)
            st.success("已重置。")
            st.rerun()
    with t3:
        st.dataframe(st.session_state.audit_logs, use_container_width=True)
    st.stop()


# ==========================================
# 权限大类 2：普通业务账户区域（财务、义工、当家主持）
# ==========================================
# 重新划分四大看盘：单独分离“借贷负债中心”
tabs = st.tabs(["📝 凭证分类账登记中心", "🔍 历史凭证解译与检索", "📊 观内结余资产看板", "🪵 观内借贷债务追踪大厅"])

# 1. 凭证记账大厅
with tabs[0]:
    st.markdown("### 📝 凭证分类账手工记账登记")
    with st.form("ledger_input_form", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        with col_a:
            f_date = st.date_input("1. 选择变动日期", datetime.now())
            f_type = st.radio("2. 资金性质", ["收入", "支出"])
            f_cate1 = st.selectbox("3. 一级科目", ["捐赠性收入(非经营)", "宗教活动收入", "功德箱收入", "场所日常维护", "场所建设与修缮", "教职人员单费与劳务"])
            f_cate2 = st.selectbox("4. 二级明细科目", ["信众随喜功德款", "专项法会功德款", "修缮专项捐款", "水电开支", "法器香烛采购", "日常维修与施工支出", "其他"])
        with col_b:
            f_tax = st.selectbox("5. 税收属性", ["免税资产", "应税收入项目", "不涉及税项"])
            f_amount = st.number_input("6. 变动金额 (元)", min_value=0.0, step=100.0)
            f_person = st.text_input("7. 功德主/经手人姓名", placeholder="请输入缘主或报销负责人")
            f_file = st.file_uploader("8. 上传凭证/残卷小票附件", type=["jpg", "png", "pdf"])
        f_memo = st.text_area("9. 详细用途明细说明", placeholder="请简明输入资金具体用途及备注...")
        
        if st.form_submit_button("🔥 确认提交并生成凭证"):
            file_name = f_file.name if f_file else "未上传凭证"
            new_row = {
                '日期': f_date.strftime('%Y-%m-%d'), '类型': f_type, '一级科目': f_cate1, '二级科目': f_cate2,
                '税收属性': f_tax, '金额': f_amount, '经手人/功德主': f_person, '票据凭证': file_name,
                '操作人姓名': current_user['name'], '操作人手机': current_user['phone'], '备注': f_memo
            }
            st.session_state.ledger = pd.concat([st.session_state.ledger, pd.DataFrame([new_row])], ignore_index=True)
            log_action(current_user['username'], current_user['name'], "账目登记", f"记账完成：金额 {f_amount} 元")
            st.success("🎉 账目登记录入成功！已自动汇入检索中心大盘。")

# 2. 查询与检索大厅
with tabs[1]:
    st.markdown("### 🔍 历史凭证多维度智能检索中心")
    if st.session_state.ledger.empty:
        st.info("🍃 暂无流水账簿数据。")
    else:
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            search_type = st.selectbox("按资金性质快速过滤", ["全部流水", "收入明细", "支出明细"])
        with col_s2:
            search_kw = st.text_input("搜寻模糊关键字 (支持功德主/明细科目/备注栏)")
            
        df_filtered = st.session_state.ledger.copy()
        if search_type == "收入明细":
            df_filtered = df_filtered[df_filtered['类型'] == "收入"]
        elif search_type == "支出明细":
            df_filtered = df_filtered[df_filtered['类型'] == "支出"]
            
        if search_kw:
            df_filtered = df_filtered[
                df_filtered['一级科目'].str.contains(search_kw) | 
                df_filtered['备注'].str.contains(search_kw) | 
                df_filtered['经手人/功德主'].str.contains(search_kw)
            ]
            
        st.dataframe(df_filtered, use_container_width=True)
        
        # 导出 Excel 报表
        if current_role in ["finance", "temple_head"]:
            excel_data = to_excel_stream(df_filtered)
            st.download_button(
                label="📥 导出当前筛选账目为标准规范 Excel 报表",
                data=excel_data,
                file_name=f"haotianguan_report_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        else:
            st.info("🔒 报表无损导出功能仅限【财务】与【当家主持】可点按。值班义工仅供看盘审计。")

# 3. 资产统计大厅
with tabs[2]:
    st.markdown("### 📊 观内各期结余资产看板")
    if current_role in ["finance", "temple_head"]:
        inc_total = st.session_state.ledger[st.session_state.ledger['类型'] == "收入"]['金额'].sum()
        exp_total = st.session_state.ledger[st.session_state.ledger['类型'] == "支出"]['金额'].sum()
        net_total = inc_total - exp_total
        
        cm1, cm2, cm3 = st.columns(3)
        with cm1: st.metric("🪙 累计法喜总收入", f"￥ {inc_total:,.2f}")
        with cm2: st.metric("💸 累计支出/修缮开支", f"￥ {exp_total:,.2f}")
        with cm3: st.metric("⚖️ 昊天观净法财结余", f"￥ {net_total:,.2f}")
    else:
        st.warning("🔒 核心结余资产数据属于本观机密，值班义工账号无权查看。")

# 4. 铁律2：全新独立划分的借贷债务大厅（主持和财务人员专享）
with tabs[3]:
    st.markdown("### 🪵 观内借贷债务风控追踪大厅")
    if current_role in ["finance", "temple_head"]:
        
        # 4.1 风控利息看板核心计算
        st.session_state.borrow_ledger['尚欠金额'] = st.session_state.borrow_ledger['借款总额'] - st.session_state.borrow_ledger['已还金额']
        total_debt = st.session_state.borrow_ledger['尚欠金额'].sum()
        
        # 提取有息且未还清的最近一笔负债作为风控指标
        active_debts = st.session_state.borrow_ledger[st.session_state.borrow_ledger['尚欠金额'] > 0]
        
        next_principal_date = "无待付项目"
        next_interest_date = "无待付项目"
        next_interest_amount = 0.0
        
        if not active_debts.empty:
            # 简单按还款时间升序排列获取最近一笔
            recent_debt = active_debts.sort_values(by='本金还款时限').iloc[0]
            next_principal_date = recent_debt['本金还款时限']
            next_interest_date = recent_debt['下次结息日']
            next_interest_amount = recent_debt['应交利息(元)']

        # 头部风控巨幕指标
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("🚨 借贷总共欠款总额", f"￥ {total_debt:,.2f}")
        with m2:
            st.metric("⏳ 最近一笔本金到期交还日", f"{next_principal_date}")
        with m3:
            st.metric("📅 下期应交利息时间", f"{next_interest_date}")
        with m4:
            st.metric("🪙 下期应交利息金额", f"￥ {next_interest_amount:,.2f}" if next_interest_amount > 0 else "免息/无待付")
            
        st.markdown("---")
        st.markdown("#### 📝 存续负债台账细目（仅支持修改已还金额进度）")
        
        # 铁律2：仅允许修改已还金额进度，配合刷新按钮
        # 使用数据编辑器，但通过 column_config 彻底锁死其他列，让主持/财务只能点击已还金额进行刷新
        edited_borrow = st.data_editor(
            st.session_state.borrow_ledger,
            use_container_width=True,
            num_rows="fixed", # 固定行，不允许他们自行添加或删减债务
            column_config={
                "借款单号": st.column_config.TextColumn("借款单号", disabled=True),
                "借款日期": st.column_config.TextColumn("借款日期", disabled=True),
                "债权人/借款方": st.column_config.TextColumn("债权人/借款方", disabled=True),
                "借款总额": st.column_config.NumberColumn("借款总额 (元)", disabled=True),
                "已还金额": st.column_config.NumberColumn("已还金额 (输入新进度)", min_value=0.0, required=True),
                "本金还款时限": st.column_config.TextColumn("本金还款时限", disabled=True),
                "下次结息日": st.column_config.TextColumn("下次结息日", disabled=True),
                "应交利息(元)": st.column_config.NumberColumn("应交利息(元)", disabled=True),
                "经手人": st.column_config.TextColumn("经手人", disabled=True),
                "备注": st.column_config.TextColumn("备注", disabled=True),
                "尚欠金额": st.column_config.NumberColumn("尚欠金额", disabled=True),
            }
        )
        
        # 刷新/同步进度按钮
        if st.button("🔄 刷新并同步还款进度看板", type="primary", use_container_width=True):
            # 重新计算尚欠金额防止溢出
            edited_borrow['尚欠金额'] = edited_borrow['借款总额'] - edited_borrow['已还金额']
            st.session_state.borrow_ledger = edited_borrow
            log_action(current_user['username'], current_user['name'], "刷新还款进度", "同步了债务还款进度大盘")
            st.success("🎉 还款进度刷新成功！上方风控欠款指标已自动重计算。")
            st.rerun()
            
    else:
        st.warning("🔒 债务负债往来大盘属本观机密，值班义工账号无权查阅。")
