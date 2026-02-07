import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import feedparser
import requests
from datetime import datetime, timedelta

# ==========================================
# 1. Config 模組 (設定與多國語系)
# ==========================================
class Config:
    DEFAULT_LANG = "🇹🇼 國語"
    STOCKS_POOL = ["AAPL", "NVDA", "TSLA", "MSFT", "GOOGL", "AMZN", "META", "AMD", "NFLX", "TSM", 
                   "AVGO", "COST", "ORCL", "BRK-B", "UNH", "JPM", "V", "LLY", "MA", "ADBE"]
    
    TRANSLATIONS = {
        "🇹🇼 國語": {
            "nav_home": "🏠 首頁推薦", "nav_search": "🔍 個股搜尋", "nav_list": "📝 觀察名單", "nav_set": "⚙️ 設定",
            "btn_scan": "執行每日智慧掃描", "current_price": "當前價", "target_price": "機構目標價",
            "potential": "預期空間", "score": "綜合評分", "risk": "風險評估", "logic": "推薦邏輯",
            "period": "建議持有期", "f_analysis": "基本面概況", "t_analysis": "技術面趨勢",
            "sentiment": "新聞情緒", "why_buy": "核心購入原因", "risk_warning": "理性投資，風險自擔。",
            "buy_signal": "強力買入", "hold_signal": "中性觀望", "sell_signal": "避開風險",
            "news_lang": "zh-TW", "news_region": "TW", "lang_tag": "zh-tw"
        },
        "🇺🇸 English": {
            "nav_home": "🏠 Recommendations", "nav_search": "🔍 Stock Search", "nav_list": "📝 Watchlist", "nav_set": "⚙️ Settings",
            "btn_scan": "Run Daily Smart Scan", "current_price": "Current Price", "target_price": "Target Price",
            "potential": "Potential Upside", "score": "Overall Score", "risk": "Risk Factor", "logic": "Logic",
            "period": "Holding Period", "f_analysis": "Fundamental Analysis", "t_analysis": "Technical Trend",
            "sentiment": "Sentiment", "why_buy": "Core Thesis", "risk_warning": "Invest rationally, risk at your own.",
            "buy_signal": "Strong Buy", "hold_signal": "Neutral", "sell_signal": "High Risk",
            "news_lang": "en-US", "news_region": "US", "lang_tag": "en"
        }
    }

# ==========================================
# 2. Data Fetcher 模組 (資料抓取)
# ==========================================
class DataFetcher:
    @staticmethod
    @st.cache_data(ttl=3600)
    def get_full_data(symbol, lang_cfg):
        try:
            tk = yf.Ticker(symbol)
            info = tk.info
            hist = tk.history(period="1y")
            # 抓取新聞 (根據語系)
            rss_url = f"https://news.google.com/rss/search?q={symbol}+stock&hl={lang_cfg['news_lang']}&gl={lang_cfg['news_region']}&ceid={lang_cfg['news_region']}:{lang_cfg['lang_tag']}"
            news = feedparser.parse(rss_url).entries[:5]
            return {"info": info, "hist": hist, "news": news}
        except Exception as e:
            return None

# ==========================================
# 3. Analyzer 模組 (投研分析邏輯)
# ==========================================
class InvestmentAnalyzer:
    @staticmethod
    def analyze(data):
        info = data['info']
        hist = data['hist']
        
        # --- 基本面 (35%) ---
        f_score = 0
        eps_growth = info.get('earningsQuarterlyGrowth', 0) or 0
        rev_growth = info.get('revenueGrowth', 0) or 0
        roe = info.get('returnOnEquity', 0) or 0
        if eps_growth > 0.1: f_score += 10
        if rev_growth > 0.1: f_score += 10
        if roe > 0.15: f_score += 15
        
        # --- 技術面 (30%) ---
        t_score = 0
        cur_price = info.get('currentPrice') or info.get('regularMarketPrice') or 1
        ma50 = hist['Close'].rolling(50).mean().iloc[-1]
        ma200 = hist['Close'].rolling(200).mean().iloc[-1]
        rsi = ta.rsi(hist['Close'], length=14).iloc[-1]
        
        if cur_price > ma50 > ma200: t_score += 20  # 多頭排列
        if 40 < rsi < 65: t_score += 10           # 非過熱區
        
        # --- 新聞與機構 (35%) ---
        s_score = 15 # 預設基準
        tar_price = info.get('targetMeanPrice') or cur_price
        upside = (tar_price - cur_price) / cur_price if cur_price > 0 else 0
        if upside > 0.15: s_score += 15
        
        total_score = f_score + t_score + s_score
        
        # 建立摘要
        analysis_report = {
            "score": total_score,
            "upside": upside,
            "rsi": rsi,
            "cur": cur_price,
            "tar": tar_price,
            "status": "Buy" if total_score > 70 else "Hold"
        }
        return analysis_report

# ==========================================
# 4. UI 模組 (Streamlit 介面)
# ==========================================
def render_ui():
    st.set_page_config(page_title="Alpha Insight Terminal", layout="wide")
    
    # 初始化 Session
    if 'lang' not in st.session_state: st.session_state.lang = Config.DEFAULT_LANG
    if 'watchlist' not in st.session_state: st.session_state.watchlist = []
    
    L = Config.TRANSLATIONS[st.session_state.lang]

    # 側邊欄導航
    with st.sidebar:
        st.title("Alpha Insight")
        if st.button("🌐 Switch Language / 切換語言"):
            st.session_state.lang = "🇺🇸 English" if st.session_state.lang == "🇹🇼 國語" else "🇹🇼 國語"
            st.rerun()
        
        menu = st.radio("MENU", [L['nav_home'], L['nav_search'], L['nav_list'], L['nav_set']])
        st.info(L['risk_warning'])

    # --- 首頁推薦 ---
    if menu == L['nav_home']:
        st.header(f"🚀 {L['nav_home']}")
        if st.button(L['btn_scan'], type="primary"):
            recommendations = []
            with st.spinner("Processing Global Market Data..."):
                for s in Config.STOCKS_POOL:
                    d = DataFetcher.get_full_data(s, L)
                    if d:
                        res = InvestmentAnalyzer.analyze(d)
                        if res['status'] == "Buy":
                            recommendations.append((s, res, d))
            
            recommendations.sort(key=lambda x: x[1]['score'], reverse=True)
            
            for s, r, d in recommendations[:10]:
                with st.container(border=True):
                    col1, col2, col3 = st.columns([1, 2, 2])
                    with col1:
                        st.metric(s, f"${r['cur']:.2f}")
                        st.caption(f"{L['score']}: {r['score']}")
                    with col2:
                        st.write(f"**{L['why_buy']}:** {L['why_buy'] if st.session_state.lang=='🇺🇸 English' else '盈餘成長強勁且位處均線支撐，具備3-6個月上行潛力。'}")
                        st.write(f"**{L['period']}:** 3 - 6 Months")
                    with col3:
                        st.write(f"**{L['potential']}:** :green[+{r['upside']*100:.1f}%]")
                        st.write(f"**{L['risk']}:** {L['risk'] if st.session_state.lang=='🇺🇸 English' else '系統性市場風險、通膨數據波動。'}")
                    
                    with st.expander(f"📖 {L['news_title']}"):
                        for n in d['news'][:3]:
                            st.write(f"🔹 [{n.title}]({n.link})")

    # --- 個股搜尋 ---
    elif menu == L['nav_search']:
        st.header(L['nav_search'])
        query = st.text_input("Ticker (e.g. NVDA, TSLA)").upper()
        if query:
            d = DataFetcher.get_full_data(query, L)
            if d:
                r = InvestmentAnalyzer.analyze(d)
                c1, c2, c3 = st.columns(3)
                c1.metric(L['current_price'], f"${r['cur']}")
                c2.metric(L['target_price'], f"${r['tar']}")
                c3.metric(L['score'], f"{r['score']}/100")
                
                st.line_chart(d['hist']['Close'])
                
                st.subheader(f"📑 {L['f_analysis']}")
                st.json({k: d['info'].get(k) for k in ['revenueGrowth', 'earningsQuarterlyGrowth', 'returnOnEquity', 'grossMargins']})
                
                st.subheader(f"🗞️ {L['news_title']}")
                for n in d['news']: st.write(f"- [{n.title}]({n.link})")
            else:
                st.error("Data fetch failed. Please check ticker.")

    # --- 觀察名單 ---
    elif menu == L['nav_list']:
        st.header(L['nav_list'])
        new_s = st.text_input("Add Ticker").upper()
        if st.button("Add to Watchlist"):
            if new_s not in st.session_state.watchlist:
                st.session_state.watchlist.append(new_s)
                st.rerun()
        
        for s in st.session_state.watchlist:
            col_a, col_b = st.columns([4, 1])
            col_a.write(f"**{s}**")
            if col_b.button("Delete", key=s):
                st.session_state.watchlist.remove(s)
                st.rerun()

if __name__ == "__main__":
    render_ui()
