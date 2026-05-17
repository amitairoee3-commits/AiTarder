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

class LiveBot:
    def __init__(self, symbol='BTC/USDT', trade_size=0.001):
        self.exchange = ExchangeHandler()
        self.whale_tracker = WhaleTracker()
        self.symbol = symbol
        self.trade_size = trade_size
        self.is_running = False
        self.strategy_code = None
        self.active_strategy_class = None

        # Track our actual live position state so we don't spam orders
        # State can be 'FLAT', 'LONG', or 'SHORT'
        self.current_live_position = 'FLAT'

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
            self.current_live_position = 'FLAT' # Reset position tracking when new strategy loads
            return True
        except Exception as e:
            print(f"[{datetime.now()}] Error loading live strategy: {e}")
            return False
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def start(self):
        if not self.active_strategy_class:
            print("Cannot start bot without an active strategy loaded.")
            return

        self.is_running = True
        print(f"[{datetime.now()}] Live Bot STARTED. Trading {self.symbol}.")

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
        print(f"[{datetime.now()}] Running cycle...")

        # 1. Fetch Latest Market Data
        df = self.exchange.fetch_ohlcv(self.symbol, timeframe='1m', limit=100)
        if df.empty:
            print("No market data fetched. Skipping cycle.")
            return

        # 2. Fetch Whale Data and merge into Pandas DataFrame
        # We append a 'whale_volume' column so the AI strategy can use it
        whales = self.whale_tracker.get_recent_transactions()
        df['whale_volume'] = 0.0
        if whales:
            print(f"[{datetime.now()}] Detected {len(whales)} recent large on-chain transactions.")
            # For simplicity, we just aggregate total whale volume in the last minute
            total_whale_vol = sum(tx.get('amount_usd', 0) for tx in whales)
            # Assign it to the latest bar
            df.iloc[-1, df.columns.get_loc('whale_volume')] = total_whale_vol

        # 3. Evaluate AI Strategy on Live Data using Backtrader Cerebro
        cerebro = bt.Cerebro()
        cerebro.addstrategy(self.active_strategy_class)

        # We need to extend PandasData to recognize the new whale_volume column
        class WhalePandasData(bt.feeds.PandasData):
            lines = ('whale_volume',)
            params = (('whale_volume', -1),)

        data = WhalePandasData(dataname=df)
        cerebro.adddata(data)

        try:
            results = cerebro.run()
            strat = results[0]

            # Determine target position size from backtrader state
            target_pos_size = strat.broker.getposition(data).size

            target_state = 'FLAT'
            if target_pos_size > 0:
                target_state = 'LONG'
            elif target_pos_size < 0:
                target_state = 'SHORT'

            # Execute ONLY if our target state differs from our current actual live state
            if target_state == 'LONG' and self.current_live_position != 'LONG':
                print(f"[{datetime.now()}] AI Strategy Signal: BUY. Executing LIVE market order...")
                res = self.exchange.create_market_buy_order(self.symbol, self.trade_size)
                print(f"Order Result: {res}")
                if "error" not in str(res).lower():
                    self.current_live_position = 'LONG'

            elif target_state == 'SHORT' and self.current_live_position != 'SHORT':
                print(f"[{datetime.now()}] AI Strategy Signal: SELL. Executing LIVE market order...")
                res = self.exchange.create_market_sell_order(self.symbol, self.trade_size)
                print(f"Order Result: {res}")
                if "error" not in str(res).lower():
                    self.current_live_position = 'SHORT'

            elif target_state == 'FLAT' and self.current_live_position != 'FLAT':
                print(f"[{datetime.now()}] AI Strategy Signal: CLOSE. Executing LIVE market order...")
                if self.current_live_position == 'LONG':
                    res = self.exchange.create_market_sell_order(self.symbol, self.trade_size)
                else:
                    res = self.exchange.create_market_buy_order(self.symbol, self.trade_size)
                print(f"Order Result: {res}")
                if "error" not in str(res).lower():
                    self.current_live_position = 'FLAT'
            else:
                print(f"[{datetime.now()}] AI Strategy Signal: HOLD (Already {self.current_live_position}).")

        except Exception as e:
            print(f"[{datetime.now()}] Error executing AI strategy in cycle: {e}")
