import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import feedparser
from datetime import datetime

# --- 1. 語系與翻譯配置 (全方位覆蓋) ---
LANG_MAP = {
    "🇹🇼 國語": {
        "title": "AI 投資決策終端",
        "menu_home": "🏠 每日推薦",
        "menu_avoid": "💀 避雷標的",
        "menu_search": "🔍 個股搜尋",
        "menu_list": "📝 觀察名單",
        "recommend_btn": "開始 AI 深度掃描",
        "buy_zone": "建議買入區點",
        "target_price": "目標價",
        "current_price": "當前價",
        "potential": "預期漲幅",
        "reason_title": "💡 推薦原因",
        "risk_title": "⚠️ 風險評估",
        "avoid_reason": "❌ 不推薦理由",
        "news_title": "📰 全網即時新聞",
        "why_buy_text": "分析師評級為買入，且股價低於估值潛力高。",
        "why_avoid_text": "RSI指標顯示嚴重超買，價格可能回檔。",
        "news_lang": "zh-TW", "news_region": "TW", "lang_tag": "zh-tw"
    },
    "🇺🇸 English": {
        "title": "AI Investment Terminal",
        "menu_home": "🏠 Recommendations",
        "menu_avoid": "💀 Avoid List",
        "menu_search": "🔍 Search",
        "menu_list": "📝 Watchlist",
        "recommend_btn": "Start AI Deep Scan",
        "buy_zone": "Buy Zone",
        "target_price": "Target Price",
        "current_price": "Current Price",
        "potential": "Potential Upside",
        "reason_title": "💡 Why Buy?",
        "risk_title": "⚠️ Risks",
        "avoid_reason": "❌ Why Avoid?",
        "news_title": "📰 Global Real-time News",
        "why_buy_text": "Analyst consensus is BUY, with significant upside potential below valuation.",
        "why_avoid_text": "RSI indicator shows overbought conditions, risk of correction is high.",
        "news_lang": "en-US", "news_region": "US", "lang_tag": "en"
    }
}

# --- 2. 核心數據模組 ---
class DataEngine:
    @staticmethod
    @st.cache_data(ttl=3600)
    def fetch_data(symbol, lang_cfg):
        try:
            tk = yf.Ticker(symbol)
            info = tk.info
            # 修正：根據語系切換 Google News 參數
            rss_url = f"https://news.google.com/rss/search?q={symbol}+stock&hl={lang_cfg['news_lang']}&gl={lang_cfg['news_region']}&ceid={lang_cfg['news_region']}:{lang_cfg['lang_tag']}"
            news = feedparser.parse(rss_url).entries[:5]
            hist = tk.history(period="1y")
            return {"info": info, "news": news, "hist": hist}
        except Exception:
            return None

# --- 3. 分析引擎 ---
class Analyst:
    @staticmethod
    def get_score(data):
        info = data['info']
        hist = data['hist']
        cur = info.get('currentPrice') or info.get('regularMarketPrice') or 0
        tar = info.get('targetMeanPrice') or cur
        
        score = 50
        upside = (tar - cur) / cur if cur > 0 else 0
        if upside > 0.15: score += 20
        if info.get('recommendationKey') in ['buy', 'strong_buy']: score += 20
        
        rsi = ta.rsi(hist['Close'], length=14).iloc[-1]
        if rsi < 30: score += 10
        elif rsi > 70: score -= 30
        
        return {"score": score, "cur": cur, "tar": tar, "upside": upside, "rsi": rsi}

# --- 4. UI 渲染 ---
def main():
    if 'lang' not in st.session_state: st.session_state.lang = "🇹🇼 國語"
    L = LANG_MAP[st.session_state.lang]
    
    st.sidebar.title(L['title'])
    if st.sidebar.button("🌐 Switch Language / 切換語言"):
        st.session_state.lang = "🇺🇸 English" if st.session_state.lang == "🇹🇼 國語" else "🇹🇼 國語"
        st.rerun()

    menu = st.sidebar.radio("Navigation", [L['menu_home'], L['menu_avoid'], L['menu_search'], L['menu_list']])
    stock_pool = ["AAPL", "NVDA", "TSLA", "MSFT", "GOOGL", "AMZN", "META", "AMD", "NFLX", "TSM"]

    # --- 頁面 1: 推薦清單 ---
    if menu == L['menu_home']:
        st.header(L['menu_home'])
        if st.button(L['recommend_btn']):
            recs = []
            with st.spinner("Analyzing..."):
                for s in stock_pool:
                    d = DataEngine.fetch_data(s, L)
                    if d:
                        a = Analyst.get_score(d)
                        if a['score'] >= 75: recs.append((s, a, d))
            
            for s, a, d in recs:
                with st.expander(f"{s} - {L['current_price']}: ${a['cur']:.2f}"):
                    st.write(f"**{L['target_price']}:** ${a['tar']:.2f} ({L['potential']}: +{a['upside']*100:.1f}%)")
                    st.write(f"**{L['reason_title']}:** {L['why_buy_text']}")
                    st.write(f"**{L['news_title']}:**")
                    for n in d['news'][:3]:
                        st.write(f"- [{n.title}]({n.link})")

    # --- 頁面 2: 避雷清單 ---
    elif menu == L['menu_avoid']:
        st.header(L['menu_avoid'])
        bad_picks = []
        with st.spinner("Scanning high-risk stocks..."):
            for s in stock_pool:
                d = DataEngine.fetch_data(s, L)
                if d:
                    a = Analyst.get_score(d)
                    if a['rsi'] > 75 or a['score'] < 40: bad_picks.append((s, a, d))
        
        for s, a, d in bad_picks:
            st.error(f"⚠️ {s} - {L['avoid_reason']}")
            st.write(f"**{L['reason_title']}:** {L['why_avoid_text']} (RSI: {a['rsi']:.1f})")
            st.write(f"**{L['current_price']}/{L['target_price']}:** ${a['cur']:.2f} / ${a['tar']:.2f}")
            st.write("---")

    # --- 頁面 3: 搜尋 ---
    elif menu == L['menu_search']:
        st.header(L['menu_search'])
        query = st.text_input("Ticker").upper()
        if query:
            d = DataEngine.fetch_data(query, L)
            if d:
                a = Analyst.get_score(d)
                c1, c2, c3 = st.columns(3)
                c1.metric(L['current_price'], f"${a['cur']:.2f}")
                c2.metric(L['target_price'], f"${a['tar']:.2f}")
                c3.metric("RSI", f"{a['rsi']:.1f}")
                st.line_chart(d['hist']['Close'])
                st.write(f"### {L['news_title']}")
                for n in d['news']: st.write(f"- [{n.title}]({n.link})")

if __name__ == "__main__":
    main()
