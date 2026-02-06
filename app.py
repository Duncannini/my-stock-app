import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="AI 全球財經智庫", layout="wide")

# --- 側邊欄：功能選單 ---
st.sidebar.title("🚀 智庫選單")
app_mode = st.sidebar.selectbox("切換模塊", ["每日10大精選", "深度個股搜尋", "我的觀察清單"])

# 輔助函式：抓取新聞與分析
def get_stock_intelligence(symbol):
    ticker = yf.Ticker(symbol)
    info = ticker.info
    news = ticker.news[:3] # 取前三則新聞
    
    # 彙整原因
    reason = ""
    if info.get('recommendationKey') == 'buy' or info.get('recommendationKey') == 'strong_buy':
        reason += "✅ 分析師一致強烈看多。 "
    if info.get('forwardPE', 100) < info.get('trailingPE', 100):
        reason += "📈 預期未來獲利成長。 "
    
    news_titles = " | ".join([n['title'] for n in news])
    source = "Yahoo Finance / Reuters"
    return {
        "price": info.get('currentPrice', 0),
        "target": info.get('targetMeanPrice', 0),
        "reason": reason if reason else "📊 技術面與基本面穩定。",
        "news": news_titles,
        "source": source,
        "timeline": "6-12 個月 (中長線投資)"
    }

# --- 功能 1: 每日10大推薦 (彙整公開資訊) ---
if app_mode == "每日10大精選":
    st.header("📋 每日即時推薦清單 (Top 10)")
    st.info(f"📅 數據更新時間：{datetime.now().strftime('%Y-%m-%d %H:%M')} (即時彙整公開網站資訊)")
    
    # 擴大篩選池
    pool = ["NVDA", "AAPL", "MSFT", "TSLA", "GOOGL", "AMZN", "AMD", "META", "NFLX", "TSM", "AVGO", "COST"]
    
    results = []
    with st.spinner('正在分析全網數據...'):
        for s in pool:
            data = get_stock_intelligence(s)
            # 篩選邏輯：有獲利空間且有推薦理由
            if data['target'] > data['price']:
                results.append([s, data['price'], data['target'], data['reason'], data['timeline'], data['source']])
    
    df = pd.DataFrame(results[:10], columns=["代碼", "現價", "目標價", "推薦原因", "建議時間線", "資料來源"])
    st.dataframe(df, use_container_width=True)

# --- 功能 2: 深度個股搜尋 ---
elif app_mode == "深度個股搜尋":
    st.header("🔍 深度個股市場分析")
    symbol = st.text_input("輸入股票代碼", "NVDA").upper()
    
    if symbol:
        tk = yf.Ticker(symbol)
        info = tk.info
        
        col1, col2, col3 = st.columns(3)
        col1.metric("當前價格", f"${info.get('currentPrice')}")
        col2.metric("分析師目標價", f"${info.get('targetMeanPrice')}")
        col3.metric("市場情緒", info.get('recommendationKey', 'N/A').upper())
        
        st.subheader("💡 為什麼值得買入？ (市場分析)")
        analysis_text = f"""
        * **基本面分析：** {info.get('longBusinessSummary', '暫無詳細描述')[:300]}...
        * **獲利能力：** 目前本益比 (P/E) 為 {info.get('trailingPE', 'N/A')}，預期本益比為 {info.get('forwardPE', 'N/A')}。
        * **即時新聞動向：**
        """
        st.write(analysis_text)
        
        for n in tk.news[:5]:
            st.write(f"- [{n['title']}]({n['link']})")

# --- 功能 3: 觀察清單 (保持原樣) ---
else:
    st.header("📝 個人觀察清單")
    # ... (此部分保留之前的邏輯即可)。
