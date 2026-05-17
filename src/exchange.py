import ccxt
import os
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ExchangeHandler:
    def __init__(self):
        self.api_key = os.getenv("BYBIT_API_KEY")
        self.api_secret = os.getenv("BYBIT_API_SECRET")

        # Initialize Bybit with ccxt
        self.exchange = ccxt.bybit({
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'enableRateLimit': True,
        })

        # We will use sandbox mode if keys aren't set, or live if they are
        # But per user request "the real thing", we default to live
        if not self.api_key or not self.api_secret:
            print("WARNING: Bybit API keys not found in .env. Market data will work, but trading will fail.")

    def get_balance(self):
        """Fetch the account balance."""
        try:
            balance = self.exchange.fetch_balance()
            return balance
        except Exception as e:
            return {"error": str(e)}

    def fetch_ohlcv(self, symbol, timeframe='1h', limit=100):
        """
        Fetch historical Open, High, Low, Close, Volume data.
        Returns a Pandas DataFrame.
        """
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            return df
        except Exception as e:
            print(f"Error fetching OHLCV for {symbol}: {e}")
            return pd.DataFrame()

    def create_market_buy_order(self, symbol, amount):
        """Execute a market BUY order."""
        try:
            order = self.exchange.create_market_buy_order(symbol, amount)
            return order
        except Exception as e:
            return {"error": str(e)}

    def create_market_sell_order(self, symbol, amount):
        """Execute a market SELL order."""
        try:
            order = self.exchange.create_market_sell_order(symbol, amount)
            return order
        except Exception as e:
            return {"error": str(e)}
