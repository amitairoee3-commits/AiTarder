import backtrader as bt
import pandas as pd
import importlib.util
import sys
import tempfile
import os

class WhalePandasData(bt.feeds.PandasData):
    lines = ('whale_volume',)
    params = (('whale_volume', -1),)

class Backtester:
    def __init__(self):
        pass

    def run_backtest(self, strategy_code: str, dataframe: pd.DataFrame):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w") as temp_file:
            temp_file.write(strategy_code)
            temp_path = temp_file.name

        try:
            spec = importlib.util.spec_from_file_location("dynamic_strategy", temp_path)
            dynamic_module = importlib.util.module_from_spec(spec)
            sys.modules["dynamic_strategy"] = dynamic_module
            spec.loader.exec_module(dynamic_module)

            AIStrategy = getattr(dynamic_module, "AIStrategy")

            cerebro = bt.Cerebro()
            cerebro.addstrategy(AIStrategy)

            # Ensure whale_volume exists in dataframe for backtesting compatibility
            if 'whale_volume' not in dataframe.columns:
                dataframe['whale_volume'] = 0.0

            data = WhalePandasData(dataname=dataframe)
            cerebro.adddata(data)

            start_cash = 10000.0
            cerebro.broker.setcash(start_cash)

            cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
            cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trade_analyzer")

            results = cerebro.run()
            strat = results[0]

            final_value = cerebro.broker.getvalue()
            pnl = final_value - start_cash

            drawdown_metrics = strat.analyzers.drawdown.get_analysis()
            max_drawdown = drawdown_metrics.get('max', {}).get('drawdown', 0)

            trades_metrics = strat.analyzers.trade_analyzer.get_analysis()
            total_trades = trades_metrics.get('total', {}).get('total', 0)
            won_trades = trades_metrics.get('won', {}).get('total', 0)

            win_rate = (won_trades / total_trades * 100) if total_trades > 0 else 0

            return {
                "start_cash": start_cash,
                "final_value": final_value,
                "pnl": pnl,
                "max_drawdown": max_drawdown,
                "total_trades": total_trades,
                "win_rate": win_rate
            }

        except Exception as e:
            return {"error": str(e)}
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
