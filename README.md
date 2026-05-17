# Celsor (AiTrader)

**Celsor** is an advanced Single-User Autonomous Crypto Trading Bot.

## Features
- **Machine Learning (Scikit-Learn):** Predicts price direction.
- **Natural Language Strategy (OpenAI):** Translates text to executable Backtrader code.
- **Market Pulse:** Scrapes live news (RSS) and whale transactions (Whale Alert API).
- **Hive-Mind:** A multi-agent Hedge Fund committee that makes risk-adjusted consensus decisions.
- **Live Trading:** Safely executes Bybit market orders via `ccxt` using your local `.env` keys.

## Setup
1. `pip install -r requirements.txt`
2. Your API keys are already configured in `.env`.
3. `streamlit run app.py`

*Note: The platform is currently designed for single-user secure local execution.*
