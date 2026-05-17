import os
import json
import openai
from datetime import datetime

class HiveMind:
    """
    A Multi-Agent Consensus Swarm for trading.
    Simulates a Hedge Fund Committee consisting of:
    1. Technical Quant
    2. On-Chain Sleuth
    3. Macro Sentiment Analyst
    4. Chief Risk Officer (CRO)
    """
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if self.api_key:
            openai.api_key = self.api_key

    def _simulate_debate(self, market_summary, whale_summary, news_summary, current_position, balance):
        system_prompt = """
        You are the 'Hive-Mind' Chief Risk Officer (CRO) of an elite crypto hedge fund.
        You must consult your three expert analysts and make a final trading decision.

        Input Data:
        - Market Data: Provided by the system.
        - Whale/On-Chain Data: Provided by the system.
        - News Sentiment: Provided by the system.
        - Current Position: LONG, SHORT, or FLAT.
        - Account Balance: USDT available.

        Your output MUST be valid JSON in exactly this format:
        {
            "quant_analysis": "Summary of technical situation.",
            "onchain_analysis": "Summary of whale/flow situation.",
            "macro_analysis": "Summary of news/sentiment.",
            "cro_decision": "Detailed explanation of the final risk-adjusted decision.",
            "action": "BUY", "SELL", or "HOLD",
            "trade_fraction": 0.0 to 1.0 (how much of the balance/position to use)
        }
        """

        user_prompt = f"""
        Current Position: {current_position}
        Available Balance: ${balance:.2f}

        Market Data Summary:
        {market_summary}

        Whale/On-Chain Data Summary:
        {whale_summary}

        News & Sentiment Summary:
        {news_summary}

        Simulate the debate and provide the final JSON output.
        """

        try:
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            content = response.choices[0].message.content.strip()

            # Clean up potential markdown formatting
            if content.startswith("```json"):
                content = content[7:-3].strip()
            elif content.startswith("```"):
                content = content[3:-3].strip()

            return json.loads(content)
        except Exception as e:
            print(f"[{datetime.now()}] Hive-Mind LLM error: {e}")
            return None

    def evaluate(self, df_recent, whales, news_sentiment, current_position, balance):
        """
        Takes raw data, formats it for the agents, and returns the consensus decision.
        """
        if not self.api_key:
            return {
                "error": "No OpenAI API key. Hive-Mind offline.",
                "action": "HOLD",
                "trade_fraction": 0.0
            }

        # 1. Prepare Market Summary
        if df_recent.empty:
            market_summary = "No market data available."
        else:
            last = df_recent.iloc[-1]
            first = df_recent.iloc[0]
            price_change = ((last['close'] - first['close']) / first['close']) * 100
            market_summary = f"Period change: {price_change:.2f}%. Current price: {last['close']:.2f}. Volatility is present."

        # 2. Prepare Whale Summary
        if whales:
            total_vol = sum(w.get('amount_usd', 0) for w in whales)
            whale_summary = f"Detected {len(whales)} large transactions totaling ${total_vol:,.2f} in the last hour."
        else:
            whale_summary = "No significant whale activity detected recently."

        # 3. Prepare News Summary
        news_summary = f"Aggregated Market Sentiment Score: {news_sentiment:.2f} (Scale: -1.0 to 1.0)."

        # 4. Get Consensus
        decision = self._simulate_debate(market_summary, whale_summary, news_summary, current_position, balance)

        if not decision:
            return {
                "error": "Failed to parse Hive-Mind consensus.",
                "action": "HOLD",
                "trade_fraction": 0.0
            }

        return decision
