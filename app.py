import streamlit as st
import pandas as pd
import datetime
import os
import plotly.express as px

# --------------------------------------------------
# 1. 基本設定與終極隱藏樣式
# --------------------------------------------------
st.set_page_config(
    page_title="我的個人智慧記帳 App", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 💡 終極隱形魔術布：全面將右下角所有官方徽章、懸浮圖示與頁頭頁尾隱藏
hide_streamlit_style = """
            <style>
            /* 隱藏頂部標題列與頁尾 */
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            
            /* 全面隱藏右下角所有官方標誌與懸浮圖示 */
            .stAppDeployButton {display: none !important;}
            [data-testid="stStatusWidget"] {display: none !important;}
            [data-testid="stToolbar"] {display: none !important;}
            div[class*="viewerBadge"] {display: none !important;}
            div[class*="styles_viewerBadge"] {display: none !important;}
            [data-testid="stActionButtonIcon"] {display: none !important;}
            #stDecoration {display: none !important;}
            iframe[title*="streamlit"] {display: none !important;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

DB_FILE = "records.csv"

# 若資料庫檔不存在，自動建立預設欄位
if not os.path.exists(DB_FILE):
    df_init = pd.DataFrame(columns=[
        "日期", "類型", "金額", "項目名稱", "類別", "屬性", "固定重複", "週期"
    ])
    df_init.to_csv(DB_FILE, index=False)

# 讀取資料
df = pd.read_csv(DB_FILE)

# 初始化記憶變數 (Session State)
if 'custom_categories' not in st.session_state:
    st.session_state['custom_categories'] = ["餐費", "交通費", "娛樂", "日常用品", "固定支出", "薪水收入"]

if 'user_quick_buttons' not in st.session_state:
    st.session_state['user_quick_buttons'] = [
        {"名稱": "冰拿鐵", "金額": 65, "類別": "餐費"},
        {"名稱": "午餐便當", "金額": 120, "類別": "餐費"}
    ]

# --------------------------------------------------
# 2. 主畫面標題與【預算總控工具箱】
# --------------------------------------------------
st.title("💰 我的個人智慧記帳 App")

# 💡 直接放置在主畫面的「預算總控工具箱」（再也不怕選單按鈕消失）
with st.expander("⚙️ 點擊展開/收合：設定每月預算", expanded=False):
    st.write("🔧 **預算管理：**")
    budget = st.number_input("設定每月總預算 (元)", min_value=1000, value=10000, step=1000, key="set_budget_input")
    warning_limit = st.number_input("設定預算警戒線 (元)", min_value=100, value=2000, step=500, key="set_warning_limit_input")

# 💡 自動理財分析小幫手
if not df.empty:
    df_want = df[(df["類型"] == "支出") & (df["屬性"] == "想要 Want")]
    want_total = df_want["金額"].sum() if not df_want.empty else 0
    
    if want_total > 3000:
        st.warning(f"💡 **理財管家提醒**：你目前在「非必要花費（想要）」已經累積了 ${want_total:,} 元，記得適度克制一下喔！")
    elif want_total > 0:
        st.info(f"✨ **理財管家鼓勵**：目前「非必要花費」只有 ${want_total:,} 元，控制得很棒，繼續保持！")

# --------------------------------------------------
# 3. 本日概況與剩餘預算
# --------------------------------------------------
today_str = str(datetime.date.today())
today_records = df[df["日期"] == today_str] if not df.empty else pd.DataFrame()

today_income = today_records[today_records["類型"] == "收入"]["金額"].sum() if not today_records.empty else 0
today_expense = today_records[today_records["類型"] == "支出"]["金額"].sum() if not today_records.empty else 0

st.subheader("📊 本日概況")
col1, col2 = st.columns(2)
col1.metric(label="🟢 本日總收入", value=f"$ {today_income}")
col2.metric(label="🔴 本日總消費", value=f"$ {today_expense}")

total_all_spent = df[df["類型"] == "支出"]["金額"].sum() if not df.empty else 0
remaining = budget - total_all_spent

st.metric(label="本月剩餘預算", value=f"${remaining:,} 元", delta=f"總預算 ${budget:,} 元")

if remaining < warning_limit:
    st.error(f"⚠️ 警告：剩餘預算不足 {warning_limit:,} 元，請控制開銷！")
else:
    st.success("✨ 太棒了！目前的預算控管得非常好！")

# 💡 自動計算最高消費類別與占比
if not df.empty:
    df_exp_only = df[df["類型"] == "支出"]
    if not df_exp_only.empty:
        top_cat = df_exp_only.groupby("類別")["金額"].sum().idxmax()
        top_cat_amount = df_exp_only.groupby("類別")["金額"].sum().max()
        total_expense_all = df_exp_only["金額"].sum()
        percentage = (top_cat_amount / total_expense_all) * 100 if total_expense_all > 0 else 0
        st.caption(f"🔥 **消費警訊**：目前花最多錢的類別是【**{top_cat}**】，共 ${top_cat_amount:,} 元（佔總支出 **{percentage:.1f}%**）")

st.divider()

# --------------------------------------------------
# 4. 📝 智慧快閃記帳與新增資料區
# --------------------------------------------------
st.subheader("📝 新增記帳資料")

st.write("⚡ **智慧快閃記帳（近月常用與自訂）：**")

auto_quick_items = []
if not df.empty:
    df_temp = df.copy()
    df_temp['日期_dt'] = pd.to_datetime(df_temp['日期']).dt.date
    thirty_days_ago = datetime.date.today() - datetime.timedelta(days=30)
    recent_df = df_temp[df_temp['日期_dt'] >= thirty_days_ago]
    
    if not recent_df.empty:
        item_counts = recent_df['項目名稱'].value_counts()
        frequent_items = item_counts[item_counts >= 5].index.tolist()
        
        for item_name_str in frequent_items:
            sample_row = recent_df[recent_df['項目名稱'] == item_name_str].iloc[0]
            auto_quick_items.append({
                "名稱": item_name_str,
                "金額": int(sample_row['金額']),
                "類別": str(sample_row['類別'])
            })

all_quick_options = []
seen_names = set()

for item in st.session_state['user_quick_buttons'] + auto_quick_items:
    if item['名稱'] not in seen_names:
        all_quick_options.append(item)
        seen_names.add(item['名稱'])

if len(all_quick_options) > 4:
    option_labels = ["-- 請選擇常用項目快速代入 --"] + [f"{i['名稱']} (${i['金額']} - {i['類別']})" for i in all_quick_options]
    selected_quick = st.selectbox("🎯 快速選擇常用消費", option_labels, key="select_quick_dropdown")
    
    if selected_quick != "-- 請選擇常用項目快速代入 --":
        matched_item = next(i for i in all_quick_options if f"{i['名稱']} (${i['金額']} - {i['類別']})" == selected_quick)
        st.session_state["main_item_name"] = matched_item["名稱"]
        st.session_state["main_amount"] = matched_item["金額"]
        st.session_state["main_category_select"] = matched_item["類別"]
        st.success(f"已自動帶入：{matched_item['名稱']} ${matched_item['金額']}")
else:
    q_cols = st.columns(max(len(all_quick_options), 1))
    for idx, item in enumerate(all_quick_options):
        if q_cols[idx].button(f"{item['名稱']} ${item['金額']}", key=f"btn_quick_{idx}"):
            st.session_state["main_item_name"] = item["名稱"]
            st.session_state["main_amount"] = item["金額"]
            st.session_state["main_category_select"] = item["類別"]
            st.rerun()

with st.expander("➕ 手動新增專屬快閃按鈕"):
    q_name = st.text_input("項目名稱", placeholder="例如：健身房", key="input_q_name")
    q_amount = st.number_input("預設金額", min_value=0, value=150, key="input_q_amount")
    q_cat = st.selectbox("所屬類別", st.session_state['custom_categories'], key="select_q_cat")
    
    if st.button("新增這個快閃項目", key="btn_add_user_quick"):
        if q_name:
            st.session_state['user_quick_buttons'].append({"名稱": q_name, "金額": q_amount, "類別": q_cat})
            st.success(f"🎉 成功加入快閃清單：【{q_name}】！")
            st.rerun()

st.write("---")

record_type = st.radio("收支類型", ["支出", "收入"], horizontal=True, key="main_record_type")
amount = st.number_input("金額", min_value=0, value=100, key="main_amount")
item_name = st.text_input("項目名稱", value="晚餐", key="main_item_name")
date = st.date_input("日期", datetime.date.today(), key="main_date")

cat_col1, cat_col2 = st.columns([2, 1])

with cat_col1:
    category = st.selectbox("類別", st.session_state['custom_categories'], key="main_category_select")

with cat_col2:
    new_cat_input = st.text_input("➕ 自訂新類別", placeholder="例如：寵物", key="quick_add_cat_input")
    if st.button("新增類別", key="btn_quick_add_cat"):
        if new_cat_input and new_cat_input not in st.session_state['custom_categories']:
            st.session_state['custom_categories'].append(new_cat_input)
            st.success(f"已新增【{new_cat_input}】！")
            st.rerun()

need_or_want = st.radio("屬性", ["需要 Need", "想要 Want"], horizontal=True, key="main_need_want")

is_recurring = st.checkbox("固定重複發生", key="main_is_recurring")
period = "無"
if is_recurring:
    period = st.selectbox("重複週期", ["每月", "每週"], key="main_period")

if st.button("確認記帳", type="primary", key="btn_main_add"):
    new_data = pd.DataFrame([{
        "日期": str(date),
        "類型": record_type,
        "金額": amount,
        "項目名稱": item_name,
        "類別": category,
        "屬性": need_or_want,
        "固定重複": "是" if is_recurring else "否",
        "週期": period
    }])
    new_data.to_csv(DB_FILE, mode='a', header=False, index=False)
    st.success(f"🎉 已成功記錄：{item_name} ${amount} 元！")
    st.rerun()

st.divider()

# --------------------------------------------------
# 5. 五大功能分頁籤 (Tabs)
# --------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "⚖️ 需要 vs 想要", 
    "🍕 類別消費圓餅圖", 
    "📊 金額統計長條圖", 
    "🔍 時間與關鍵字搜尋", 
    "⚙️ 表格與重置"
])

with tab1:
    st.write("📊 **需要 vs 想要消費比例分析：**")
    if not df.empty:
        df_exp = df[df["類型"] == "支出"]
        if not df_exp.empty:
            fig_nw = px.pie(df_exp, names="屬性", values="金額", title="需要 vs 想要支出占比", hole=0.4)
            st.plotly_chart(fig_nw, use_container_width=True)
        else:
            st.info("尚無支出紀錄可供分析。")
    else:
        st.info("尚無資料。")

with tab2:
    st.write("🍕 **消費類別圓餅圖分析：**")
    if not df.empty:
        df_exp = df[df["類型"] == "支出"]
        if not df_exp.empty:
            fig_cat = px.pie(df_exp, names="類別", values="金額", title="各類別支出占比")
            st.plotly_chart(fig_cat, use_container_width=True)
        else:
            st.info("尚無支出紀錄。")
    else:
        st.info("尚無資料。")

with tab3:
    st.write("📊 **消費金額統計長條圖：**")
    if not df.empty:
        df_exp = df[df["類型"] == "支出"]
        if not df_exp.empty:
            fig_bar = px.bar(df_exp, x="項目名稱", y="金額", color="類別", title="各項目支出金額比較")
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("尚無支出紀錄。")
    else:
        st.info("尚無資料。")

with tab4:
    st.write("🔍 **時間與關鍵字進階搜尋：**")
    search_col1, search_col2 = st.columns([1, 2])
    
    with search_col1:
        search_type = st.radio("選擇搜尋方式", ["月份篩選", "自訂時間區間（最長 5 年）"], key="search_type_radio")
    
    with search_col2:
        if search_type == "月份篩選":
            selected_month = st.date_input("選擇想要查看的月份", datetime.date.today(), key="month_picker")
            start_date = selected_month.replace(day=1)
            if selected_month.month == 12:
                end_date = selected_month.replace(year=selected_month.year + 1, month=1, day=1) - datetime.timedelta(days=1)
            else:
                end_date = selected_month.replace(month=selected_month.month + 1, day=1) - datetime.timedelta(days=1)
        else:
            min_possible_date = datetime.date.today() - datetime.timedelta(days=365*5)
            date_range = st.date_input(
                "選擇時間區間（最長 5 年）",
                value=[datetime.date.today() - datetime.timedelta(days=30), datetime.date.today()],
                min_value=min_possible_date,
                max_value=datetime.date.today(),
                key="date_range_picker"
            )
            if len(date_range) == 2:
                start_date, end_date = date_range[0], date_range[1]
            else:
                start_date = date_range[0]
                end_date = date_range[0]

    search_term = st.text_input("關鍵字過濾（例如：晚餐、餐費）", key="search_term_input_tab4")
    
    if not df.empty:
        df_temp = df.copy()
        df_temp['日期_dt'] = pd.to_datetime(df_temp['日期']).dt.date
        filtered_df = df_temp[(df_temp['日期_dt'] >= start_date) & (df_temp['日期_dt'] <= end_date)]
        
        if search_term:
            filtered_df = filtered_df[
                filtered_df['項目名稱'].astype(str).str.contains(search_term, case=False, na=False) | 
                filtered_df['類別'].astype(str).str.contains(search_term, case=False, na=False)
            ]
        
        display_df = filtered_df.drop(columns=['日期_dt'])
        st.write(f"📅 搜尋區間：**{start_date} ~ {end_date}**（共找到 {len(display_df)} 筆紀錄）：")
        st.dataframe(display_df, use_container_width=True)
        
        range_spent = display_df[display_df["類型"] == "支出"]["金額"].sum() if not display_df.empty else 0
        st.info(f"💰 此區間總支出累計：**${range_spent:,}** 元")
    else:
        st.info("目前小本子裡還沒有資料喔！")

with tab5:
    st.write("⚙️ **線上編輯帳本與備份管理：**")
    if not df.empty:
        edited_df = st.data_editor(df, num_rows="dynamic", key="data_editor_tab5")
        if st.button("💾 儲存修改後的表格", key="btn_save_edited_df"):
            edited_df.to_csv(DB_FILE, index=False)
            st.success("🎉 表格已成功儲存！")
            st.rerun()
            
        csv_data = edited_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 下載備份 CSV 檔案",
            data=csv_data,
            file_name=f"accounting_backup_{datetime.date.today()}.csv",
            mime="text/csv",
            key="btn_download_csv_tab5"
        )
    else:
        st.info("目前沒有資料可以修改。")
        
    st.divider()

    uploaded_file = st.file_uploader("📤 匯入備份帳本 (CSV 檔案)", type=["csv"], key="uploader_csv")
    if uploaded_file is not None:
        if st.button("確認覆蓋匯入", key="btn_confirm_upload"):
            new_upload_df = pd.read_csv(uploaded_file)
            new_upload_df.to_csv(DB_FILE, index=False)
            st.success("🎉 已成功匯入並更新帳本！")
            st.rerun()

    # --------------------------------------------------
    # 🚨 一鍵清空/重置資料庫按鈕
    # --------------------------------------------------
    st.write("---")
    st.write("🔴 **重置帳本資料：**")
    if st.button("🗑️ 一鍵清空所有記帳紀錄", type="primary", key="btn_reset_all_data"):
        empty_df = pd.DataFrame(columns=[
            "日期", "類型", "金額", "項目名稱", "類別", "屬性", "固定重複", "週期"
        ])
        empty_df.to_csv(DB_FILE, index=False)
        st.success("🎉 所有紀錄已順利清空！帳本已重新開始！")
        st.rerun()
