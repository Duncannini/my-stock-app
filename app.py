import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import feedparser
from datetime import datetime

# --- 語系與翻譯配置 ---
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
        "news_lang": "zh-TW",
        "news_region": "TW",
        "lang_tag": "zh-tw"
    },
    "🇺🇸 English": {
        "title": "AI Investment Terminal",
        "menu_home": "🏠 Recommendations",
        "menu_avoid": "💀 Avoid List",
        "menu_search": "🔍 Stock Search",
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
        "news_lang": "en-US",
        "news_region": "US",
        "lang_tag": "en"
    }
}

# --- 核心數據模組 ---
class DataEngine:
    @staticmethod
    @st.cache_data(ttl=3600)
    def fetch_data(symbol, lang_cfg):
        try:
            tk = yf.Ticker(symbol)
            info = tk.info
            # 根據語系切換新聞源
            rss_url = f"https://news.google.com/rss/search?q={symbol}+stock&hl={lang_cfg['news_lang']}&gl={lang_cfg['news_region']}&ceid={lang_cfg['news_region']}:{lang_cfg['lang_tag']}"
            news = feedparser.parse(rss_url).entries[:5]
            hist = tk.history(period="1y")
            return {"info": info, "news": news, "hist": hist}
        except:
            return None

# --- 分析引擎 ---
class Analyst:
    @staticmethod
    def get_score(data):
        info = data['info']
        hist = data['hist']
        cur = info.get('currentPrice', 0) or info.get('regularMarketPrice', 0)
        tar = info.get('targetMeanPrice', cur)
        
        # 評分邏輯 (0-100)
        score = 50
        upside = (tar - cur) / cur if cur > 0 else 0
        if upside > 0.15: score += 20
        if info.get('recommendationKey') in ['buy', 'strong_buy']: score += 20
        
        # 技術面：RSI 判斷
        rsi = ta.rsi(hist['Close'], length=14).iloc[-1]
        if rsi < 30: score += 10 # 超賣區
        elif rsi > 70: score -= 30 # 超買過熱
        
        return {"score": score, "cur": cur, "tar": tar, "upside": upside, "rsi": rsi}

# --- UI 渲染 ---
def main():
    if 'lang' not in st.session_state: st.session_state.lang = "🇹🇼 國語"
    L = LANG_MAP[st.session_state.lang]
    
    st.sidebar.title(L['title'])
    if st.sidebar.button("🌐 Switch Language / 切換語言"):
        st.session_state.lang = "🇺🇸 English" if st.session_state.lang == "🇹🇼 國語" else "🇹🇼 國語"
        st.rerun()

    menu = st.sidebar.radio("Navigation", [L['menu_home'], L['menu_avoid'], L['menu_search'], L['menu_list']])

    # 模擬 S&P 500 熱門股池
    stock_pool = ["AAPL", "NVDA", "TSLA", "MSFT", "GOOGL", "AMZN", "META", "AMD", "NFLX", "TSM", "JPM", "V", "PG", "DIS"]

    # --- 頁面 1: 推薦清單 ---
    if menu == L['menu_home']:
        st.header(L['menu_home'])
        if st.button(L['recommend_btn']):
            recs = []
            for s in stock_pool:
                d = DataEngine.fetch_data(s, L)
                if d:
                    analysis = Analyst.get_score(d)
                    if analysis['score'] >= 75:
                        recs.append((s, analysis, d))
            
            for s, a, d in recs[:10]:
                with st.expander(f"{s} - {L['current_price']}: ${a['cur']} (Potential: +{a['upside']*100:.1f}%)"):
                    st.write(f"**{L['target_price']}:** ${a['tar']}")
                    st.write(f"**{L['reason_title']}:** 分析師一致評級為強力買入，且目前價格低於估值 {a['upside']*100:.1f}%。")
                    st.write(f"**{L['news_title']}:**")
                    for n in d['news'][:3]:
                        st.write(f"- [{n.title}]({n.link})")

    # --- 頁面 2: 避雷清單 (極不推薦) ---
    elif menu == L['menu_avoid']:
        st.header(L['menu_avoid'])
        bad_picks = []
        with st.spinner("Scanning for high-risk stocks..."):
            for s in stock_pool:
                d = DataEngine.fetch_data(s, L)
                if d:
                    analysis = Analyst.get_score(d)
                    # 邏輯：超買 (RSI > 75) 或 嚴重溢價
                    if analysis['rsi'] > 75 or analysis['score'] < 40:
                        bad_picks.append((s, analysis, d))
        
        for s, a, d in bad_picks[:10]:
            st.error(f"⚠️ {s} - {L['avoid_reason']}")
            st.write(f"- **現價/目標價:** ${a['cur']} / ${a['tar']}")
            st.write(f"- **理由:** 技術指標 RSI ({a['rsi']:.1f}) 顯示嚴重過熱，且目前價格已透支未來一年成長性。")
            st.write("---")

    # --- 頁面 3: 個股搜尋 ---
    elif menu == L['menu_search']:
        st.header(L['menu_search'])
        query = st.text_input("Ticker").upper()
        if query:
            d = DataEngine.fetch_data(query, L)
            if d:
                a = Analyst.get_score(d)
                col1, col2, col3 = st.columns(3)
                col1.metric(L['current_price'], a['cur'])
                col2.metric(L['target_price'], a['tar'])
                col3.metric("RSI", f"{a['rsi']:.1f}")
                st.line_chart(d['hist']['Close'])
                st.write(f"### {L['news_title']}")
                for n in d['news']: st.write(f"- [{n.title}]({n.link})")

if __name__ == "__main__":
    main()
