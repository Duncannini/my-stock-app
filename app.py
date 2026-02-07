import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import requests
from bs4 import BeautifulSoup
import feedparser
from datetime import datetime

# --- CONFIG & TRANSLATION ---
LANG_MAP = {
    "🇹🇼 國語": {
        "title": "AI 全球投資決策終端",
        "menu_home": "🏠 首頁推薦",
        "menu_search": "🔍 個股搜尋",
        "menu_list": "📝 觀察名單",
        "menu_set": "⚙️ 設定",
        "recommend_btn": "開始 AI 掃描推薦",
        "search_placeholder": "輸入代碼 (如 NVDA)",
        "buy_signal": "💎 建議買入",
        "hold_signal": "⏳ 建議觀望",
        "risk_title": "⚠️ 風險提示",
        "logic_title": "💡 推薦邏輯",
        "timeline_title": "🕒 投資週期",
        "fundamental": "基本面",
        "technical": "技術面",
        "sentiment": "新聞情緒",
        "score": "綜合評分",
        "lang_btn": "切換語言 (Switch Language)"
    },
    "🇺🇸 English": {
        "title": "AI Global Investment Terminal",
        "menu_home": "🏠 Home",
        "menu_search": "🔍 Search",
        "menu_list": "📝 Watchlist",
        "menu_set": "⚙️ Settings",
        "recommend_btn": "Start AI Scan",
        "search_placeholder": "Enter Ticker (e.g. NVDA)",
        "buy_signal": "💎 BUY",
        "hold_signal": "⏳ WAIT",
        "risk_title": "⚠️ Risk Factor",
        "logic_title": "💡 Logic",
        "timeline_title": "🕒 Timeline",
        "fundamental": "Fundamental",
        "technical": "Technical",
        "sentiment": "Sentiment",
        "score": "Total Score",
        "lang_btn": "切換語言 (Switch Language)"
    }
}

# --- DATA FETCHER MODULE ---
class DataFetcher:
    @staticmethod
    @st.cache_data(ttl=3600)
    def get_stock_all(symbol):
        try:
            tk = yf.Ticker(symbol)
            info = tk.info
            hist = tk.history(period="1y")
            # 抓取 Google News
            news_feed = feedparser.parse(f"https://news.google.com/rss/search?q={symbol}+stock&hl=zh-TW&gl=TW&ceid=TW:zh-tw")
            return {"info": info, "hist": hist, "news": news_feed.entries[:3]}
        except:
            return None

# --- ANALYZER MODULE ---
class Analyzer:
    @staticmethod
    def analyze(data):
        info = data['info']
        hist = data['hist']
        
        # 1. 基本面評分 (0-40)
        f_score = 0
        if (info.get('forwardPE', 100) or 100) < (info.get('trailingPE', 100) or 101): f_score += 20
        if (info.get('revenueGrowth', 0) or 0) > 0.1: f_score += 20
        
        # 2. 技術面評分 (0-40)
        t_score = 0
        rsi = ta.rsi(hist['Close'], length=14).iloc[-1]
        sma200 = hist['Close'].rolling(200).mean().iloc[-1]
        if 30 < rsi < 70: t_score += 20
        if hist['Close'].iloc[-1] > sma200: t_score += 20
        
        # 3. 情緒評分 (0-20)
        s_score = 15 if info.get('recommendationKey') in ['buy', 'strong_buy'] else 10
        
        total = f_score + t_score + s_score
        return {"total": total, "f": f_score, "t": t_score, "s": s_score, "rsi": rsi}

# --- UI MODULE ---
def init_session():
    if 'lang' not in st.session_state: st.session_state.lang = "🇹🇼 國語"
    if 'watchlist' not in st.session_state: st.session_state.watchlist = ["NVDA", "AAPL", "MSFT"]

def render_ui():
    init_session()
    L = LANG_MAP[st.session_state.lang]
    
    st.sidebar.title(L['title'])
    if st.sidebar.button(L['lang_btn']):
        st.session_state.lang = "🇺🇸 English" if st.session_state.lang == "🇹🇼 國語" else "🇹🇼 國語"
        st.rerun()

    mode = st.sidebar.radio("Menu", [L['menu_home'], L['menu_search'], L['menu_list'], L['menu_set']])

    # --- HOME PAGE ---
    if mode == L['menu_home']:
        st.header(L['menu_home'])
        if st.button(L['recommend_btn']):
            pool = ["AAPL", "NVDA", "TSLA", "GOOGL", "MSFT", "AMZN", "META", "AVGO", "COST", "AMD", "NFLX", "TSM"]
            recs = []
            for s in pool:
                d = DataFetcher.get_stock_all(s)
                if d:
                    res = Analyzer.analyze(d)
                    if res['total'] >= 70:
                        recs.append({"Symbol": s, "Score": res['total'], "Price": d['info'].get('currentPrice')})
            
            for item in recs[:10]:
                with st.expander(f"{item['Symbol']} - {L['score']}: {item['Score']}"):
                    st.write(f"**{L['logic_title']}:** 營收成長強勁且位於長線支撐位。")
                    st.write(f"**{L['risk_title']}:** 市場波動與通膨預期。")
                    st.write(f"**{L['timeline_title']}:** 3-6 Months")

    # --- SEARCH PAGE ---
    elif mode == L['menu_search']:
        st.header(L['menu_search'])
        symbol = st.text_input(L['search_placeholder']).upper()
        if symbol:
            d = DataFetcher.get_stock_all(symbol)
            if d:
                res = Analyzer.analyze(d)
                col1, col2 = st.columns(2)
                col1.metric(L['score'], res['total'])
                col1.progress(res['total'] / 100)
                
                st.subheader(f"📊 {L['fundamental']} & {L['technical']}")
                st.write(f"RSI: {res['rsi']:.2f} | P/E: {d['info'].get('forwardPE')}")
                st.line_chart(d['hist']['Close'])
                
                st.subheader(f"📰 {L['sentiment']}")
                for n in d['news']:
                    st.write(f"- [{n.title}]({n.link})")
            else:
                st.error("Invalid Ticker")

    # --- WATCHLIST PAGE ---
    elif mode == L['menu_list']:
        st.header(L['menu_list'])
        new_s = st.text_input("Add Ticker").upper()
        if st.button("Add"): 
            st.session_state.watchlist.append(new_s)
            st.rerun()
        
        for s in st.session_state.watchlist:
            d = DataFetcher.get_stock_all(s)
            if d:
                st.write(f"**{s}** | Price: {d['info'].get('currentPrice')} | [Delete]")

render_ui()
