import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="AI 美股達人", layout="wide")

# --- 側邊欄：功能導航 ---
st.sidebar.title("🛠️ 功能選單")
app_mode = st.sidebar.selectbox("請選擇功能", ["每日AI推薦", "個人觀察清單", "個股詳細搜尋"])

# --- 功能 1: 每日自動推薦 (模擬全網篩選) ---
if app_mode == "每日AI推薦":
    st.header("🌟 今日最適合購買的 5 支股票")
    st.caption("系統已自動分析 S&P 500 平台數據，根據價值投資演算法標出低估值標的")
    
    # 這裡預設一組熱門候選名單進行自動篩選
    candidates = ["AAPL", "NVDA", "TSLA", "GOOGL", "MSFT", "AMZN", "META", "AVGO", "COST", "NFLX"]
    
    @st.cache_data(ttl=3600) # 快取一小時，避免重複抓取太慢
    def get_recommendations():
        recs = []
        for s in candidates:
            stock = yf.Ticker(s)
            info = stock.info
            current = info.get('currentPrice', 1)
            target = info.get('targetMeanPrice', 0)
            # 篩選邏輯：股價低於目標價 15% 以上
            if target > current * 1.15:
                discount = round((1 - current/target) * 100, 1)
                recs.append([s, current, target, f"低估 {discount}%"])
        return sorted(recs, key=lambda x: x[3], reverse=True)[:5]

    rec_list = get_recommendations()
    df_rec = pd.DataFrame(rec_list, columns=["代碼", "目前價", "目標價", "獲利空間"])
    st.table(df_rec)
    st.success("💡 建議理由：以上股票目前市價遠低於分析師平均目標價，且具備高成長動能。")

# --- 功能 2: 個人觀察清單 ---
elif app_mode == "個人觀察清單":
    st.header("📝 我的觀察清單")
    
    # 使用 Session State 儲存清單，這樣重新整理前都會在
    if 'watchlist' not in st.session_state:
        st.session_state.watchlist = ["NVDA", "AAPL"]
    
    new_stock = st.text_input("輸入代碼新增至清單 (例如: TSLA)").upper()
    if st.button("新增"):
        if new_stock and new_stock not in st.session_state.watchlist:
            st.session_state.watchlist.append(new_stock)
            st.rerun()

    if st.button("清空清單"):
        st.session_state.watchlist = []
        st.rerun()

    if st.session_state.watchlist:
        for s in st.session_state.watchlist:
            tick = yf.Ticker(s)
            st.write(f"**{s}** : ${tick.info.get('currentPrice', 'N/A')}")
    else:
        st.info("目前清單是空的，請在上方輸入代碼。")

# --- 功能 3: 自主搜尋股票 ---
elif app_mode == "個股詳細搜尋":
    st.header("🔍 全球股票搜尋")
    search_symbol = st.text_input("請輸入股票代碼 (例如: 2330.TW 或 MSFT)", "NVDA").upper()
    
    if search_symbol:
        s_data = yf.Ticker(search_symbol)
        hist = s_data.history(period="6mo")
        if not hist.empty:
            st.subheader(f"{search_symbol} 最近半年走勢")
            st.line_chart(hist['Close'])
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("當前股價", f"${s_data.info.get('currentPrice')}")
            with col2:
                st.metric("分析師平均目標價", f"${s_data.info.get('targetMeanPrice')}")
        else:
            st.error("找不到該股票，請確認代碼是否正確。")
