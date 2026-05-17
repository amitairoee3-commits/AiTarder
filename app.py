import streamlit as st
import pandas as pd
import threading
import time

from src.exchange import ExchangeHandler
from src.whale_alert import WhaleTracker
from src.ai_generator import AIGenerator
from src.backtester import Backtester
from src.bot import LiveBot

st.set_page_config(page_title="AiTrader", layout="wide")
st.title("🤖 AiTrader - Autonomous Crypto Trading Bot")

# Initialize Session State
if "strategy_code" not in st.session_state:
    st.session_state.strategy_code = ""
if "live_bot" not in st.session_state:
    st.session_state.live_bot = LiveBot(symbol='BTC/USDT')
if "bot_thread" not in st.session_state:
    st.session_state.bot_thread = None

# Sidebar
st.sidebar.header("Navigation")
page = st.sidebar.radio("Go to", ["Dashboard (Live)", "Strategy Lab", "Whale Tracker"])

exchange = ExchangeHandler()
whale_tracker = WhaleTracker()
ai_gen = AIGenerator()
backtester = Backtester()

if page == "Dashboard (Live)":
    st.header("📈 Live Trading Dashboard")

    # Balance
    balance = exchange.get_balance()
    if "error" in balance:
        st.warning("Could not fetch Bybit balance. Check API keys.")
    else:
        usdt_bal = balance.get('USDT', {}).get('free', 0.0)
        st.metric("Available USDT Balance", f"${usdt_bal:.2f}")

    # Bot Status
    st.subheader("Bot Controls")
    is_running = st.session_state.live_bot.is_running
    status_text = "🟢 RUNNING" if is_running else "🔴 STOPPED"
    st.write(f"**Status:** {status_text}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Start Bot"):
            if not st.session_state.strategy_code:
                st.error("No strategy loaded! Go to Strategy Lab first.")
            elif not is_running:
                st.session_state.live_bot.load_strategy(st.session_state.strategy_code)
                # Run bot in a background thread so it doesn't block Streamlit UI
                st.session_state.bot_thread = threading.Thread(target=st.session_state.live_bot.start, daemon=True)
                st.session_state.bot_thread.start()
                st.success("Bot started successfully in the background!")
                time.sleep(1)
                st.rerun()

    with col2:
        if st.button("Stop Bot"):
            if is_running:
                st.session_state.live_bot.stop()
                st.warning("Bot stopping...")
                time.sleep(1)
                st.rerun()

elif page == "Strategy Lab":
    st.header("🧪 Strategy Lab")
    st.markdown("Use natural language to tell the AI what trading strategy to build. It will generate the code and backtest it.")

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

elif page == "Whale Tracker":
    st.header("🐋 Whale Transaction Tracker")
    st.markdown("Live feed of massive on-chain transactions moving the markets.")

    if st.button("Refresh Alerts"):
        with st.spinner("Fetching whale alerts..."):
            txs = whale_tracker.get_recent_transactions()
            if not txs:
                st.info("No recent whale transactions found or API key missing.")
            else:
                for tx in txs:
                    symbol = tx.get('blockchain', 'Unknown').upper()
                    amount_usd = tx.get('amount_usd', 0)
                    st.write(f"🚨 **{symbol}** move: **${amount_usd:,.2f}**")
