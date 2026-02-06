import streamlit as st
import yfinance as yf
import pandas as pd
import feedparser # 需要在 requirements.txt 加入這個
from datetime import datetime

st.set_page_config(page_title="全網情報彙整終端", layout="wide")

# --- 側邊欄：功能選單 ---
st.sidebar.title("🌐 全網情報系統")
app_mode = st.sidebar.selectbox("切換模塊", ["每日10大精選", "深度全網搜尋", "我的觀察清單"])

# 1. 新增：全網新聞彙整函式 (從 Google News 抓取)
def get_global_news(symbol):
    try:
        # 抓取 Google News RSS 中關於該股票的新聞
        rss_url = f"https://news.google.com/rss/search?q={symbol}+stock+when:7d&hl=en-US&gl=US&ceid=US:en"
        feed = feedparser.parse(rss_url)
        news_list = []
        for entry in feed.entries[:5]: # 取前5則
            news_list.append({"title": entry.title, "link": entry.link, "source": entry.source.get('title', 'Global News')})
        return news_list
    except:
        return []

# 2. 核心分析函式
def get_comprehensive_analysis(symbol):
    try:
        tk = yf.Ticker(symbol)
        info = tk.info
        current = info.get('currentPrice') or info.get('regularMarketPrice') or 0
        target = info.get('targetMeanPrice') or current
        
        # 判斷邏輯：綜合目標價與機構評級
        rec = info.get('recommendationKey', 'none').lower()
        news = get_global_news(symbol)
        
        status = "⏳ 觀望"
        if target > current * 1.15 and "buy" in rec:
            status = "💎 值得買入"
            
        return {
            "symbol": symbol,
            "price": current,
            "target": target,
            "status": status,
            "news": news
        }
    except:
        return None

# --- 功能 1: 每日10大精選 ---
if app_mode == "每日10大精選":
    st.header("📋 全網推薦Top 10 (彙整多方數據)")
    pool = ["NVDA", "AAPL", "MSFT", "TSLA", "GOOGL", "AMZN", "AMD", "META", "AVGO", "COST"]
    
    results = []
    with st.spinner('正在掃描全球財經媒體與機構數據...'):
        for s in pool:
            data = get_comprehensive_analysis(s)
            if data:
                results.append([data['symbol'], data['price'], data['target'], data['status'], "Google News / Yahoo / Analyst consensus"])
    
    df = pd.DataFrame(results, columns=["代碼", "現價", "目標價", "系統評斷", "情報來源"])
    st.table(df)

# --- 功能 2: 深度全網搜尋 ---
elif app_mode == "深度全網搜尋":
    symbol = st.text_input("輸入股票代碼", "NVDA").upper()
    if symbol:
        data = get_comprehensive_analysis(symbol)
        if data:
            st.subheader(f"🔍 {symbol} 跨平台情報彙整")
            c1, c2 = st.columns(2)
            c1.metric("即時市價", f"${data['price']}")
            c1.metric("分析師平均目標價", f"${data['target']}")
            
            st.write("### 🌍 全球最新報導 (彙整自各家媒體)")
            if data['news']:
                for n in data['news']:
                    st.write(f"- **[{n['source']}]** [{n['title']}]({n['link']})")
            else:
                st.write("目前無相關全球即時報導。")
