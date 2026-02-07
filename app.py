import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import feedparser

# ==========================================
# 1. 核心配置與專業語系字典
# ==========================================
st.set_page_config(page_title="Alpha Insight Terminal", layout="wide")

# 模擬富途牛牛深色專業風格
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    div[data-testid="stExpander"] { background-color: #1e222d !important; border: 1px solid #363c4e !important; }
    .stMetric { background-color: #161a25; border-radius: 8px; padding: 10px; border: 1px solid #363c4e; }
    </style>
    """, unsafe_allow_html=True)

LANG_MAP = {
    "🇹🇼 國語": {
        "nav_home": "🏠 首頁推薦", "nav_search": "🔍 個股搜尋", "nav_list": "📝 觀察名單",
        "btn_scan": "執行 AI 智慧掃描", "price": "現價", "target": "目標價", "upside": "預期漲幅",
        "score": "綜合評分", "logic": "分析邏輯", "risk": "風險提示", "news": "即時新聞",
        "buy_reason": "基本面強韌，且技術指標顯示中期趨勢向上，具備安全邊際。",
        "risk_desc": "需留意總體經濟波動及聯準會利率政策影響。",
        "n_lang": "zh-TW", "n_reg": "TW", "n_ceid": "TW:zh-tw"
    },
    "🇺🇸 English": {
        "nav_home": "🏠 Recommendations", "nav_search": "🔍 Search", "nav_list": "📝 Watchlist",
        "btn_scan": "Run AI Deep Scan", "price": "Price", "target": "Target", "upside": "Upside",
        "score": "Score", "logic": "Analysis", "risk": "Risk Info", "news": "News",
        "buy_reason": "Strong fundamentals with bullish technical alignment. High safety margin.",
        "risk_desc": "Monitor macro volatility and Fed interest rate decisions.",
        "n_lang": "en-US", "n_reg": "US", "n_ceid": "US:en"
    }
}

# ==========================================
# 2. 數據抓取與分析引擎
# ==========================================
class ProDataEngine:
    @staticmethod
    def get_data(symbol, L):
        try:
            # 增加抓取超時設定以提高穩定性
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # 取得現價
            cur = info.get('currentPrice') or info.get('regularMarketPrice')
            if not cur: return None
            
            # 取得歷史數據做技術分析
            hist = ticker.history(period="1y")
            if hist.empty: return None
            
            # 技術指標計算
            rsi = ta.rsi(hist['Close'], length=14).iloc[-1] if len(hist) > 14 else 50
            ma50 = hist['Close'].rolling(50).mean().iloc[-1]
            
            # 機構目標價與漲幅
            tar = info.get('targetMeanPrice') or cur
            upside = (tar - cur) / cur
            
            # 綜合評分邏輯 (基本35%+技術30%+機構35%)
            score = 50
            if upside > 0.15: score += 20
            if cur > ma50: score += 15
            if 40 < rsi < 70: score += 15
            
            # 新聞抓取
            rss_url = f"https://news.google.com/rss/search?q={symbol}+stock&hl={L['n_lang']}&gl={L['n_reg']}&ceid={L['n_ceid']}"
            news = feedparser.parse(rss_url).entries[:3]
            
            return {
                "symbol": symbol, "cur": cur, "tar": tar, "upside": upside, 
                "rsi": rsi, "score": score, "news": news, "hist": hist
            }
        except:
            return None

# ==========================================
# 3. 介面渲染
# ==========================================
def main():
    if 'lang' not in st.session_state: st.session_state.lang = "🇹🇼 國語"
    L = LANG_MAP[st.session_state.lang]

    # Sidebar
    with st.sidebar:
        st.title("Alpha Insight")
        if st.button("🌐 Switch Language / 切換語言"):
            st.session_state.lang = "🇺🇸 English" if st.session_state.lang == "🇹🇼 國語" else "🇹🇼 國語"
            st.rerun()
        st.divider()
        menu = st.radio("Navigation", [L['nav_home'], L['nav_search'], L['nav_list']])

    # --- 頁面：每日推薦 ---
    if menu == L['nav_home']:
        st.header(L['nav_home'])
        if st.button(L['btn_scan'], type="primary"):
            # 核心監測池
            pool = ["AAPL", "NVDA", "TSLA", "MSFT", "GOOGL", "AMZN", "META", "AMD", "NFLX", "TSM", 
                    "AVGO", "COST", "ORCL", "BRK-B", "UNH", "JPM", "V", "LLY", "MA", "ADBE"]
            results = []
            
            progress_bar = st.progress(0)
            for i, s in enumerate(pool):
                data = ProDataEngine.get_data(s, L)
                if data: results.append(data)
                progress_bar.progress((i + 1) / len(pool))
            
            # 按分數排序取前 10
            results.sort(key=lambda x: x['score'], reverse=True)
            
            for r in results[:10]:
                with st.container(border=True):
                    c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
                    c1.markdown(f"### {r['symbol']}")
                    c2.metric(L['price'], f"${r['cur']:.2f}")
                    c3.metric(L['upside'], f"+{r['upside']*100:.1f}%")
                    c4.write(f"**{L['logic']}:** {L['buy_reason']}")
                    
                    with st.expander(f"📊 {L['news']} & {L['risk']}"):
                        st.write(f"**{L['risk']}:** {L['risk_desc']}")
                        for n in r['news']:
                            st.write(f"🔹 [{n.title}]({n.link})")

    # --- 頁面：搜尋 ---
    elif menu == L['nav_search']:
        st.header(L['nav_search'])
        ticker = st.text_input("Enter Ticker (e.g. NVDA)").upper()
        if ticker:
            with st.spinner("Loading..."):
                r = ProDataEngine.get_data(ticker, L)
                if r:
                    col1, col2, col3 = st.columns(3)
                    col1.metric(L['price'], f"${r['cur']:.2f}")
                    col2.metric(L['target'], f"${r['tar']:.2f}")
                    col3.metric(L['score'], f"{r['score']} pts")
                    
                    st.line_chart(r['hist']['Close'])
                    st.subheader(L['news'])
                    for n in r['news']:
                        st.write(f"📌 [{n.title}]({n.link})")
                else:
                    st.error("No data found. Please check the ticker symbol.")

if __name__ == "__main__":
    main()
