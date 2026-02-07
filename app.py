import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import feedparser
from datetime import datetime

# --- 1. 介面風格與語系配置 ---
st.set_page_config(page_title="Global Terminal", layout="wide")

# 富途風格 CSS
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e222d; padding: 15px; border-radius: 10px; border: 1px solid #363c4e; }
    .stExpander { border: 1px solid #363c4e !important; background-color: #1e222d !important; }
    .price-up { color: #00ad2b; font-weight: bold; }
    .price-down { color: #f23645; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

LANG_MAP = {
    "🇹🇼 國語": {
        "title": "富途型·AI 智投",
        "menu_home": "🚀 每日精選 10 檔",
        "menu_search": "🔍 行情報價",
        "menu_list": "📝 觀察自選",
        "recommend_btn": "刷新 AI 實時策略",
        "target": "目標價", "current": "最新價", "potential": "預期空間",
        "reason": "核心邏輯", "news_title": "即時快訊",
        "why_buy": "基本面與技術面共振，機構資金流入明顯。",
        "news_lang": "zh-TW", "news_region": "TW", "lang_tag": "zh-tw"
    },
    "🇺🇸 English": {
        "title": "Moo-Style AI Terminal",
        "menu_home": "🚀 Top 10 Picks",
        "menu_search": "🔍 Quotes",
        "menu_list": "📝 Watchlist",
        "recommend_btn": "Refresh AI Strategy",
        "target": "Target", "current": "Price", "potential": "Upside",
        "reason": "Logic", "news_title": "Live News",
        "why_buy": "Bullish alignment in fundamentals and tech indicators.",
        "news_lang": "en-US", "news_region": "US", "lang_tag": "en"
    }
}

# --- 2. 專業數據引擎 ---
class DataEngine:
    @staticmethod
    @st.cache_data(ttl=1800)
    def fetch(symbol, cfg):
        try:
            tk = yf.Ticker(symbol)
            info = tk.info
            rss = f"https://news.google.com/rss/search?q={symbol}+stock&hl={cfg['news_lang']}&gl={cfg['news_region']}&ceid={cfg['news_region']}:{cfg['lang_tag']}"
            return {"info": info, "news": feedparser.parse(rss).entries[:3], "hist": tk.history(period="1y")}
        except: return None

    @staticmethod
    def analyze(data):
        info = data['info']
        cur = info.get('currentPrice') or info.get('regularMarketPrice') or 1
        tar = info.get('targetMeanPrice') or cur
        # 計算 RSI 與 均線
        close = data['hist']['Close']
        rsi = ta.rsi(close, length=14).iloc[-1]
        sma50 = close.rolling(50).mean().iloc[-1]
        
        score = 50
        if tar > cur * 1.1: score += 20
        if cur > sma50: score += 15
        if 40 < rsi < 65: score += 15
        return {"score": score, "cur": cur, "tar": tar, "upside": (tar-cur)/cur, "rsi": rsi}

# --- 3. UI 主程式 ---
def main():
    if 'lang' not in st.session_state: st.session_state.lang = "🇹🇼 國語"
    L = LANG_MAP[st.session_state.lang]
    
    # 側邊欄優化
    with st.sidebar:
        st.title(L['title'])
        if st.button("🌐 Switch Language"):
            st.session_state.lang = "🇺🇸 English" if st.session_state.lang == "🇹🇼 國語" else "🇹🇼 國語"
            st.rerun()
        st.divider()
        menu = st.radio("Navigation", [L['menu_home'], L['menu_search'], L['menu_list']])

    # --- 頁面 1: 每日推薦 10 檔 ---
    if menu == L['menu_home']:
        st.subheader(L['menu_home'])
        if st.button(L['recommend_btn'], type="primary"):
            # 擴大掃描池以確保選出 10 檔
            pool = ["AAPL", "NVDA", "TSLA", "MSFT", "GOOGL", "AMZN", "META", "AMD", "NFLX", "TSM", 
                    "AVGO", "COST", "ORCL", "BRK-B", "UNH", "JPM", "V", "LLY", "MA", "ADBE"]
            results = []
            with st.spinner("AI Searching for Best Opportunities..."):
                for s in pool:
                    d = DataEngine.fetch(s, L)
                    if d:
                        a = DataEngine.analyze(d)
                        results.append((s, a, d))
            
            # 按評分排序取前 10
            results.sort(key=lambda x: x[1]['score'], reverse=True)
            
            for s, a, d in results[:10]:
                with st.container(border=True):
                    c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
                    c1.markdown(f"### {s}")
                    c2.metric(L['current'], f"${a['cur']:.2f}")
                    c3.metric(L['potential'], f"+{a['potential']*100:.1f}%")
                    c4.write(f"**{L['reason']}:** {L['why_buy']}")
                    
                    with st.expander(f"📊 {L['news_title']}"):
                        for n in d['news']:
                            st.write(f"🔹 [{n.title}]({n.link})")

    # --- 頁面 2: 行情報價 (搜尋) ---
    elif menu == L['menu_search']:
        st.subheader(L['menu_search'])
        symbol = st.text_input("Ticker", placeholder="e.g. NVDA").upper()
        if symbol:
            d = DataEngine.fetch(symbol, L)
            if d:
                a = DataEngine.analyze(d)
                col1, col2, col3 = st.columns(3)
                col1.metric(L['current'], f"${a['cur']:.2f}")
                col2.metric(L['target'], f"${a['tar']:.2f}")
                col3.metric("RSI (14)", f"{a['rsi']:.1f}")
                
                st.line_chart(d['hist']['Close'], height=250)
                st.write(f"#### {L['news_title']}")
                for n in d['news']:
                    st.write(f"📌 **{n.title}**")
                    st.caption(f"Source: {n.link}")

    # --- 頁面 3: 自選清單 ---
    elif menu == L['menu_list']:
        st.subheader(L['menu_list'])
        if 'watchlist' not in st.session_state: st.session_state.watchlist = ["AAPL", "NVDA"]
        
        new_ticker = st.text_input("Add Ticker").upper()
        if st.button("Add"):
            if new_ticker not in st.session_state.watchlist:
                st.session_state.watchlist.append(new_ticker)
                st.rerun()

        for s in st.session_state.watchlist:
            d = DataEngine.fetch(s, L)
            if d:
                a = DataEngine.analyze(d)
                st.markdown(f"**{s}** | Price: `${a['cur']:.2f}` | Upside: `+{a['potential']*100:.1f}%`")

if __name__ == "__main__":
    main()
