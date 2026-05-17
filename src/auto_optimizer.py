import pandas as pd
from src.ai_generator import AIGenerator
from src.backtester import Backtester
import time
from datetime import datetime

class AutoOptimizer:
    def __init__(self, exchange_handler):
        self.ai = AIGenerator()
        self.backtester = Backtester()
        self.exchange = exchange_handler

        # A list of base strategy prompts the AI will try to optimize
        self.strategy_prompts = [
            "A strategy that buys when the 10-period SMA crosses above the 50-period SMA and sells when it crosses below.",
            "A strategy that buys when the RSI is below 30 and whale_volume is greater than 0, and sells when RSI is above 70.",
            "A momentum strategy that buys when current close is higher than the close 5 periods ago, and sells otherwise."
        ]

    def optimize(self, symbol='BTC/USDT', timeframe='1h', limit=500):
        """
        Fetches recent data, generates multiple strategies via AI,
        backtests them all, and returns the code of the most profitable one.
        """
        print(f"[{datetime.now()}] Starting autonomous strategy optimization...")

        df = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        if df.empty:
            print("Failed to fetch data for optimization.")
            return None

        # Mock whale data for backtesting since real historical whale data requires paid API tier
        if 'whale_volume' not in df.columns:
            df['whale_volume'] = 0.0

        best_pnl = -float('inf')
        best_code = None
        best_metrics = None

        for prompt in self.strategy_prompts:
            print(f"Testing prompt: {prompt[:50]}...")
            code = self.ai.generate_strategy(prompt)

            if code.startswith("# Error"):
                print("Failed to generate strategy code.")
                continue

            results = self.backtester.run_backtest(code, df)

            if "error" in results:
                print(f"Backtest failed: {results['error']}")
                continue

            pnl = results.get('pnl', 0)
            print(f"Result PNL: ${pnl:.2f}")

            if pnl > best_pnl:
                best_pnl = pnl
                best_code = code
                best_metrics = results

            # Sleep slightly to respect OpenAI rate limits
            time.sleep(2)

        if best_code:
            print(f"[{datetime.now()}] Optimization complete. Best PNL: ${best_pnl:.2f}")
            return {
                "code": best_code,
                "metrics": best_metrics
            }
        else:
            print("Optimization failed to find a valid strategy.")
            return None
