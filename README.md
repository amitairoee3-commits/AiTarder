# Celsor (AiTrader)

**Important Notice:** The transition to a full multi-user SaaS architecture (Next.js, FastAPI, Celery) requires extensive engineering, security audits, database configuration, and Stripe billing integration that is beyond the scope of a single autonomous setup script.

The current version in this repository is the **Single-User Autonomous ML Bot**.

## Features
- **Machine Learning (Scikit-Learn):** Predicts price direction.
- **Natural Language Strategy (OpenAI):** Translates text to executable Backtrader code.
- **Market Pulse:** Scrapes live news (RSS) and whale transactions (Whale Alert API).
- **Live Trading:** Safely executes Bybit market orders via `ccxt` using your local `.env` keys.

## Setup
1. `pip install -r requirements.txt`
2. Configure `.env` based on `.env.example`.
3. `streamlit run app.py`

*Note for Future Development: To convert this to a full SaaS platform ("Celsor"), the core engine (`src/`) must be decoupled from the Streamlit UI and wrapped in a secure multi-tenant API, which is a massive multi-week undertaking.*
