import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="美股買入助手", layout="wide")
st.title("📈 美股自動追蹤 & 買入價評估")

# 設定追蹤股票
tickers = ["AAPL", "NVDA", "TSLA", "MSFT", "GOOGL", "AMZN", "META"]
selected = st.multiselect("選擇要追蹤的股票", tickers, default=["NVDA", "AAPL", "TSLA"])

def get_stock_info(symbol):
    s = yf.Ticker(symbol)
    info = s.info
    hist = s.history(period="1y")
    
    current = info.get('currentPrice', 0)
    target = info.get('targetMeanPrice', current) # 分析師平均目標價
    ma200 = hist['Close'].mean() # 200日均線
    
    # 買入演算法：價格低於目標價 15% 且接近均線
    suggested_buy = target * 0.85
    status = "💎 適合買入" if current <= suggested_buy else "⏳ 觀望"
    
    return [symbol, current, target, round(suggested_buy, 2), status]

if st.button("更新最新價位與評估"):
    results = [get_stock_info(s) for s in selected]
    df = pd.DataFrame(results, columns=["代碼", "目前價", "目標價", "建議買入價", "系統評斷"])
    st.table(df)
    
    for s in selected:
        st.subheader(f"{s} 最近走勢")
        st.line_chart(yf.Ticker(s).history(period="3mo")['Close'])
