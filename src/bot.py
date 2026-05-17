import time
import importlib.util
import sys
import tempfile
import os
import pandas as pd
from datetime import datetime
import backtrader as bt
from src.exchange import ExchangeHandler
from src.whale_alert import WhaleTracker
from src.news_scraper import NewsScraper
from src.ml_predictor import MLPredictor
from src.auto_optimizer import AutoOptimizer
from src.hive_mind import HiveMind

class LiveBot:
    def __init__(self, symbol='BTC/USDT', trade_size=0.001, mode='hive_mind'):
        self.exchange = ExchangeHandler()
        self.whale_tracker = WhaleTracker()
        self.news_scraper = NewsScraper()
        self.ml_predictor = MLPredictor()
        self.optimizer = AutoOptimizer(self.exchange)
        self.hive_mind = HiveMind()

        self.symbol = symbol
        self.trade_size = trade_size

        # mode can be 'ai_strategy_only', 'ml_only', 'hybrid', or 'hive_mind'
        self.mode = mode

        self.is_running = False
        self.strategy_code = None
        self.active_strategy_class = None

        self.current_live_position = 'FLAT'
        self.latest_news_sentiment = 0.0
        self.latest_hive_mind_decision = None

    def load_strategy(self, strategy_code: str):
        self.strategy_code = strategy_code
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w") as temp_file:
            temp_file.write(strategy_code)
            temp_path = temp_file.name

        try:
            spec = importlib.util.spec_from_file_location("live_strategy", temp_path)
            dynamic_module = importlib.util.module_from_spec(spec)
            sys.modules["live_strategy"] = dynamic_module
            spec.loader.exec_module(dynamic_module)
            self.active_strategy_class = getattr(dynamic_module, "AIStrategy")
            print(f"[{datetime.now()}] Strategy successfully loaded for live trading.")
            self.current_live_position = 'FLAT'
            return True
        except Exception as e:
            print(f"[{datetime.now()}] Error loading live strategy: {e}")
            return False
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def auto_optimize(self):
        best = self.optimizer.optimize(symbol=self.symbol, timeframe='1h', limit=500)
        if best:
            self.load_strategy(best['code'])
            return True
        return False

    def start(self):
        if self.mode in ['ai_strategy_only', 'hybrid'] and not self.active_strategy_class:
            print("Attempting to auto-optimize a strategy before starting...")
            success = self.auto_optimize()
            if not success:
                print("Cannot start bot. Optimization failed and no strategy loaded.")
                return

        self.is_running = True
        print(f"[{datetime.now()}] Live Bot STARTED in {self.mode} mode. Trading {self.symbol}.")

        if self.mode in ['ml_only', 'hybrid']:
            print("Fetching historical data for ML training...")
            train_df = self.exchange.fetch_ohlcv(self.symbol, timeframe='1h', limit=500)
            if not train_df.empty:
                train_df['whale_volume'] = 0.0
                self.latest_news_sentiment = self.news_scraper.get_aggregated_sentiment()
                self.ml_predictor.train(train_df, self.latest_news_sentiment)

        while self.is_running:
            try:
                self._run_cycle()
                time.sleep(60)
            except KeyboardInterrupt:
                self.stop()
            except Exception as e:
                print(f"[{datetime.now()}] Unexpected error in bot loop: {e}")
                time.sleep(60)

    def stop(self):
        self.is_running = False
        print(f"[{datetime.now()}] Live Bot STOPPED.")

    def _run_cycle(self):
        print(f"\n[{datetime.now()}] Running cycle...")

        df = self.exchange.fetch_ohlcv(self.symbol, timeframe='1m', limit=100)
        if df.empty:
            print("No market data fetched. Skipping cycle.")
            return

        whales = self.whale_tracker.get_recent_transactions()
        df['whale_volume'] = 0.0
        if whales:
            total_whale_vol = sum(tx.get('amount_usd', 0) for tx in whales)
            df.iloc[-1, df.columns.get_loc('whale_volume')] = total_whale_vol

        self.latest_news_sentiment = self.news_scraper.get_aggregated_sentiment()

        balance_info = self.exchange.get_balance()
        usdt_balance = balance_info.get('USDT', {}).get('free', 0.0) if "error" not in balance_info else 0.0

        final_decision = 'FLAT'
        dynamic_trade_size = self.trade_size

        if self.mode == 'hive_mind':
            print("Consulting the Hive-Mind Hedge Fund Committee...")
            decision = self.hive_mind.evaluate(df, whales, self.latest_news_sentiment, self.current_live_position, usdt_balance)
            self.latest_hive_mind_decision = decision

            if decision and "error" not in decision:
                print(f"  -> Quant: {decision.get('quant_analysis')}")
                print(f"  -> OnChain: {decision.get('onchain_analysis')}")
                print(f"  -> Macro: {decision.get('macro_analysis')}")
                print(f"  -> CRO Decision: {decision.get('cro_decision')}")

                action = decision.get("action", "HOLD")
                fraction = decision.get("trade_fraction", 0.0)

                if action == "BUY":
                    final_decision = 'LONG'
                elif action == "SELL":
                    final_decision = 'SHORT'
                elif action == "HOLD":
                    final_decision = self.current_live_position

            else:
                print(f"  -> Hive-Mind Error/Hold: {decision}")
                final_decision = self.current_live_position

        else:
            # Legacy modes (ML, AI, Hybrid)
            ml_pred, ml_prob = 0, 0.0
            if self.ml_predictor.is_trained:
                ml_pred, ml_prob = self.ml_predictor.predict(df, self.latest_news_sentiment)

            strategy_target_state = 'FLAT'
            if self.active_strategy_class:
                cerebro = bt.Cerebro()
                cerebro.addstrategy(self.active_strategy_class)

                class WhalePandasData(bt.feeds.PandasData):
                    lines = ('whale_volume',)
                    params = (('whale_volume', -1),)

                data = WhalePandasData(dataname=df)
                cerebro.adddata(data)

                try:
                    results = cerebro.run()
                    strat = results[0]
                    target_pos_size = strat.broker.getposition(data).size

                    if target_pos_size > 0:
                        strategy_target_state = 'LONG'
                    elif target_pos_size < 0:
                        strategy_target_state = 'SHORT'
                except Exception as e:
                    pass

            if self.mode == 'ai_strategy_only':
                final_decision = strategy_target_state
            elif self.mode == 'ml_only':
                if ml_prob > 0.65:
                    final_decision = 'LONG'
                elif ml_prob < 0.35:
                    final_decision = 'SHORT'
            elif self.mode == 'hybrid':
                if strategy_target_state == 'LONG' and ml_prob > 0.55:
                    final_decision = 'LONG'
                elif strategy_target_state == 'SHORT' and ml_prob < 0.45:
                    final_decision = 'SHORT'
                elif strategy_target_state == 'FLAT':
                    final_decision = 'FLAT'
                else:
                    final_decision = self.current_live_position

        self._execute_trade(final_decision, dynamic_trade_size)

    def _execute_trade(self, target_state, size):
        if target_state == 'LONG' and self.current_live_position != 'LONG':
            print(f"[{datetime.now()}] Decision: BUY. Executing LIVE market order for {size}...")
            res = self.exchange.create_market_buy_order(self.symbol, size)
            if "error" not in str(res).lower():
                self.current_live_position = 'LONG'

        elif target_state == 'SHORT' and self.current_live_position != 'SHORT':
            print(f"[{datetime.now()}] Decision: SELL. Executing LIVE market order for {size}...")
            res = self.exchange.create_market_sell_order(self.symbol, size)
            if "error" not in str(res).lower():
                self.current_live_position = 'SHORT'

        elif target_state == 'FLAT' and self.current_live_position != 'FLAT':
            print(f"[{datetime.now()}] Decision: CLOSE. Executing LIVE market order...")
            if self.current_live_position == 'LONG':
                res = self.exchange.create_market_sell_order(self.symbol, size)
            else:
                res = self.exchange.create_market_buy_order(self.symbol, size)
            if "error" not in str(res).lower():
                self.current_live_position = 'FLAT'
