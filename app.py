import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import feedparser

# --- 1. 介面風格與語系配置 ---
st.set_page_config(page_title="Global Terminal", layout="wide")

# 富途風格 CSS 加強
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem; font-weight: 700; color: #00ad2b; }
    .stExpander { border: 1px solid #363c4e !important; }
    </style>
    """, unsafe_allow_html=True)

LANG_MAP = {
    "🇹🇼 國語": {
        "title": "富途型·AI 智投",
        "menu_home": "🚀 每日精選 10 檔",
        "menu_search": "🔍 行情報價",
        "menu_list": "📝 觀察自選",
        "recommend_btn": "刷新 AI 實時策略",
        "target_price": "目標價", 
        "current_price": "最新價", 
        "potential": "預期空間",
        "reason_title": "核心邏輯", 
        "news_title": "即時快訊",
        "why_buy": "基本面與技術面共振，機構資金流入明顯。",
        "news_lang": "zh-TW", "news_region": "TW", "lang_tag": "zh-tw"
    },
    "🇺🇸 English": {
        "title": "Moo-Style AI Terminal",
        "menu_home": "🚀 Top 10 Picks",
        "menu_search": "🔍 Quotes",
        "menu_list": "📝 Watchlist",
        "recommend_btn": "Refresh AI Strategy",
        "target_price": "Target", 
        "current_price": "Price", 
        "potential": "Upside",
        "reason_title": "Logic", 
        "news_title": "Live News",
        "why_buy": "Bullish alignment in fundamentals and tech indicators.",
        "news_lang": "en-US", "news_region": "US", "lang_tag": "en"
    }
}

# --- 2. 數據與分析模組 ---
class DataEngine:
    @staticmethod
    @st.cache_data(ttl=1800)
    def fetch(symbol, cfg):
        try:
            tk = yf.Ticker(symbol)
            info = tk.info
            # 確保獲取當前價格
            cur = info.get('currentPrice') or info.get('regularMarketPrice') or 0
            if cur == 0: return None # 避免無效股票
            
            rss = f"https://news.google.com/rss/search?q={symbol}+stock&hl={cfg['news_lang']}&gl={cfg['news_region']}&ceid={cfg['news_region']}:{cfg['lang_tag']}"
            news = feedparser.parse(rss).entries[:3]
            hist = tk.history(period="1y")
            
            # 計算技術指標
            if len(hist) > 20:
                rsi = ta.rsi(hist['Close'], length=14).iloc[-1]
                sma50 = hist['Close'].rolling(50).mean().iloc[-1]
            else:
                rsi, sma50 = 50, cur

            tar = info.get('targetMeanPrice') or cur
            upside = (tar - cur) / cur if cur > 0 else 0
            
            # 評分邏輯
            score = 50
            if upside > 0.1: score += 20
            if cur > sma50: score += 15
            if 30 < rsi < 65: score += 15
            
            return {
                "symbol": symbol, "info": info, "news": news, "hist": hist,
                "cur": cur, "tar": tar, "upside": upside, "rsi": rsi, "score": score
            }
        except: return None

# --- 3. UI 主程式 ---
def main():
    if 'lang' not in st.session_state: st.session_state.lang = "🇹🇼 國語"
    L = LANG_MAP[st.session_state.lang]
    
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
            pool = ["AAPL", "NVDA", "TSLA", "MSFT", "GOOGL", "AMZN", "META", "AMD", "NFLX", "TSM", 
                    "AVGO", "COST", "ORCL", "BRK-B", "UNH", "JPM", "V", "LLY", "MA", "ADBE"]
            results = []
            with st.spinner("AI Searching..."):
                for s in pool:
                    res = DataEngine.fetch(s, L)
                    if res: results.append(res)
            
            results.sort(key=lambda x: x['score'], reverse=True)
            
            for r in results[:10]:
                with st.container(border=True):
                    c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
                    c1.markdown(f"### {r['symbol']}")
                    # 修正：這裡使用 L['current_price'] 與 L['potential'] 確保與字典一致
                    c2.metric(L['current_price'], f"${r['cur']:.2f}")
                    c3.metric(L['potential'], f"+{r['upside']*100:.1f}%")
                    c4.write(f"**{L['reason_title']}:** {L['why_buy']}")
                    
                    with st.expander(f"📊 {L['news_title']}"):
                        for n in r['news']:
                            st.write(f"🔹 [{n.title}]({n.link})")

    # --- 頁面 2: 行情報價 (搜尋) ---
    elif menu == L['menu_search']:
        st.subheader(L['menu_search'])
        symbol = st.text_input("Ticker", placeholder="e.g. NVDA").upper()
        if symbol:
            r = DataEngine.fetch(symbol, L)
            if r:
                col1, col2, col3 = st.columns(3)
                col1.metric(L['current_price'], f"${r['cur']:.2f}")
                col2.metric(L['target_price'], f"${r['tar']:.2f}")
                col3.metric("RSI (14)", f"{r['rsi']:.1f}")
                
                st.line_chart(r['hist']['Close'], height=250)
                st.write(f"#### {L['news_title']}")
                for n in r['news']: st.write(f"📌 [{n.title}]({n.link})")
            else:
                st.warning("Symbol not found or data unavailable.")

if __name__ == "__main__":
    main()
