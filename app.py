import streamlit as st
import pandas as pd
import threading
import time
import json

from src.exchange import ExchangeHandler
from src.whale_alert import WhaleTracker
from src.ai_generator import AIGenerator
from src.backtester import Backtester
from src.bot import LiveBot
from src.news_scraper import NewsScraper

st.set_page_config(page_title="Celsor Hive-Mind", layout="wide")
st.title("🧠 Celsor - Multi-Agent Hive-Mind Trading")

# Initialize Session State
if "strategy_code" not in st.session_state:
    st.session_state.strategy_code = ""
if "live_bot" not in st.session_state:
    st.session_state.live_bot = LiveBot(symbol='BTC/USDT')
if "bot_thread" not in st.session_state:
    st.session_state.bot_thread = None

# Sidebar
st.sidebar.header("Navigation")
page = st.sidebar.radio("Go to", ["Hive-Mind Dashboard (Live)", "Strategy Lab", "Market Pulse (Whales & News)"])

exchange = ExchangeHandler()
whale_tracker = WhaleTracker()
ai_gen = AIGenerator()
backtester = Backtester()
news_scraper = NewsScraper()

if page == "Hive-Mind Dashboard (Live)":
    st.header("📈 Live Trading Dashboard")

    # Balance
    balance = exchange.get_balance()
    if "error" in balance:
        st.warning("Could not fetch Bybit balance. Check API keys.")
    else:
        usdt_bal = balance.get('USDT', {}).get('free', 0.0)
        st.metric("Available USDT Balance", f"${usdt_bal:.2f}")

    # Bot Status
    st.subheader("Autonomous Bot Controls")
    is_running = st.session_state.live_bot.is_running
    status_text = "🟢 RUNNING" if is_running else "🔴 STOPPED"
    st.write(f"**Status:** {status_text}")

    col_mode, col_btn1, col_btn2 = st.columns([2, 1, 1])

    with col_mode:
        mode = st.selectbox("Operating Mode", ['hive_mind', 'hybrid', 'ai_strategy_only', 'ml_only'], index=0, disabled=is_running)
        if not is_running:
            st.session_state.live_bot.mode = mode

    with col_btn1:
        if st.button("Start Bot"):
            if not is_running:
                st.session_state.bot_thread = threading.Thread(target=st.session_state.live_bot.start, daemon=True)
                st.session_state.bot_thread.start()
                st.success("Bot started!")
                time.sleep(1)
                st.rerun()

    with col_btn2:
        if st.button("Stop Bot"):
            if is_running:
                st.session_state.live_bot.stop()
                st.warning("Bot stopping...")
                time.sleep(1)
                st.rerun()

    st.divider()

    if mode == 'hive_mind':
        st.subheader("🏛️ Hedge Fund Committee (Live Feed)")
        if st.button("Refresh Committee Log"):
            st.rerun()

        decision = st.session_state.live_bot.latest_hive_mind_decision
        if decision and "error" not in decision:
            st.markdown(f"### Current Action: **{decision.get('action')}** (Size: {decision.get('trade_fraction')})")

            col_q, col_o, col_m = st.columns(3)
            with col_q:
                st.info(f"**👨‍💻 Technical Quant:**\n{decision.get('quant_analysis')}")
            with col_o:
                st.warning(f"**🕵️ On-Chain Sleuth:**\n{decision.get('onchain_analysis')}")
            with col_m:
                st.success(f"**📰 Macro Analyst:**\n{decision.get('macro_analysis')}")

            st.error(f"**⚖️ Chief Risk Officer (Final Decision):**\n{decision.get('cro_decision')}")
        else:
            st.write("Waiting for the committee's first cycle... (Check terminal for logs)")

elif page == "Strategy Lab":
    st.header("🧪 Strategy Lab")
    st.markdown("Use natural language to build a strategy. The AI understands basic OHLCV, indicators, and `whale_volume`.")

    prompt = st.text_area("Describe your strategy:", "Buy BTC when the 50-day moving average crosses above the 200-day moving average.")

    if st.button("Generate Strategy"):
        with st.spinner("AI is thinking..."):
            code = ai_gen.generate_strategy(prompt)
            st.session_state.strategy_code = code
            st.success("Strategy generated!")

    if st.session_state.strategy_code:
        st.subheader("Generated Python Code (Backtrader)")
        st.code(st.session_state.strategy_code, language="python")

        if st.button("Run Backtest"):
            with st.spinner("Fetching historical data and running backtest..."):
                df = exchange.fetch_ohlcv('BTC/USDT', '1d', 365)
                if df.empty:
                    st.error("Could not fetch historical data for backtesting.")
                else:
                    results = backtester.run_backtest(st.session_state.strategy_code, df)
                    if "error" in results:
                        st.error(f"Backtest failed: {results['error']}")
                    else:
                        st.subheader("Backtest Results")
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Net Profit (PNL)", f"${results['pnl']:.2f}")
                        col2.metric("Win Rate", f"{results['win_rate']:.2f}%")
                        col3.metric("Max Drawdown", f"{results['max_drawdown']:.2f}%")
                        st.write(f"Total Trades: {results['total_trades']}")

elif page == "Market Pulse (Whales & News)":
    st.header("🌐 Market Pulse")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📰 Live Crypto News & Sentiment")
        if st.button("Refresh News"):
            with st.spinner("Scraping news..."):
                news = news_scraper.fetch_recent_news()
                agg_sentiment = news_scraper.get_aggregated_sentiment()

                st.metric("Aggregated Market Sentiment", f"{agg_sentiment:.2f}",
                          delta="Bullish" if agg_sentiment > 0 else "Bearish")

                for n in news[:5]:
                    color = "green" if n['sentiment'] > 0 else "red" if n['sentiment'] < 0 else "gray"
                    st.markdown(f"**[{n['sentiment']:.2f}]** [{n['title']}]({n['link']})")

    with col2:
        st.subheader("🐋 Live Whale Transactions")
        if st.button("Refresh Whales"):
            with st.spinner("Fetching whale alerts..."):
                txs = whale_tracker.get_recent_transactions()
                if not txs:
                    st.info("No recent whale transactions found or API key missing.")
                else:
                    for tx in txs:
                        symbol = tx.get('blockchain', 'Unknown').upper()
                        amount_usd = tx.get('amount_usd', 0)
                        st.write(f"🚨 **{symbol}** move: **${amount_usd:,.2f}**")
