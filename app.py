import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="AI 全球財經智庫", layout="wide")

# --- 側邊欄：功能選單 ---
st.sidebar.title("🚀 智庫選單")
app_mode = st.sidebar.selectbox("切換模塊", ["每日10大精選", "深度個股搜尋", "我的觀察清單"])

# 輔助函式：安全抓取數據（避免 KeyError）
def get_stock_intelligence(symbol):
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # 使用 .get() 確保找不到 key 時回傳預設值，不會報錯
        current = info.get('currentPrice') or info.get('regularMarketPrice') or 0
        target = info.get('targetMeanPrice') or current
        rec_key = info.get('recommendationKey', 'N/A')
        
        # 彙整原因邏輯
        reasons = []
        if rec_key in ['buy', 'strong_buy']: reasons.append("✅ 分析師共識看多")
        if (info.get('forwardPE', 0) or 0) < (info.get('trailingPE', 0) or 1): reasons.append("📈 預期獲利成長")
        
        reason_text = " | ".join(reasons) if reasons else "📊 走勢待觀察"
        
        return {
            "price": current,
            "target": target,
            "reason": reason_text,
            "timeline": "6-12 個月",
            "source": "Yahoo Finance"
        }
    except Exception:
        return None

# --- 功能 1: 每日10大精選 ---
if app_mode == "每日10大精選":
    st.header("📋 每日即時推薦清單 (Top 10)")
    st.info(f"📅 數據更新時間：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    pool = ["NVDA", "AAPL", "MSFT", "TSLA", "GOOGL", "AMZN", "AMD", "META", "NFLX", "TSM", "AVGO", "COST"]
    
    results = []
    with st.spinner('正在分析全網數據...'):
        for s in pool:
            data = get_stock_intelligence(s)
            if data and data['price'] > 0:
                results.append([s, data['price'], data['target'], data['reason'], data['timeline'], data['source']])
    
    # 排序：找出獲利空間最大的
    results.sort(key=lambda x: (x[2]-x[1])/x[1] if x[1]>0 else 0, reverse=True)
    
    df = pd.DataFrame(results[:10], columns=["代碼", "現價", "目標價", "推薦原因", "建議時間線", "資料來源"])
    st.dataframe(df, use_container_width=True)

# --- 功能 2: 深度個股搜尋 ---
elif app_mode == "深度個股搜尋":
    st.header("🔍 深度個股市場分析")
    symbol = st.text_input("輸入股票代碼", "NVDA").upper()
    
    if symbol:
        try:
            tk = yf.Ticker(symbol)
            info = tk.info
            
            # 頂部儀表板
            c1, c2, c3 = st.columns(3)
            curr = info.get('currentPrice') or info.get('regularMarketPrice', 'N/A')
            targ = info.get('targetMeanPrice', 'N/A')
            c1.metric("當前價格", f"${curr}")
            c2.metric("分析師目標價", f"${targ}")
            c3.metric("評級", info.get('recommendationKey', 'N/A').upper())
            
            st.subheader("💡 市場分析與建議")
            st.write(f"**公司簡介：** {info.get('longBusinessSummary', '暫無資料')[:400]}...")
            
            # 顯示新聞
            st.write("---")
            st.write("📰 **最新相關新聞：**")
            news = tk.news
            if news:
                for n in news[:5]:
                    st.write(f"- [{n['title']}]({n['link']})")
            else:
                st.write("暫無即時新聞。")
                
        except Exception as e:
            st.error(f"搜尋出錯：請確認代碼 {symbol} 是否正確。")

# --- 功能 3: 觀察清單 ---
else:
    st.header("📝 個人觀察清單")
    if 'watchlist' not in st.session_state:
        st.session_state.watchlist = ["AAPL", "NVDA"]
    
    new_s = st.text_input("新增股票代碼").upper()
    if st.button("新增") and new_s:
        if new_s not in st.session_state.watchlist:
            st.session_state.watchlist.append(new_s)
            st.rerun()

    for s in st.session_state.watchlist:
        st.write(f"**{s}**")
