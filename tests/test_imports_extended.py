import unittest
from src.exchange import ExchangeHandler
from src.whale_alert import WhaleTracker
from src.ai_generator import AIGenerator
from src.backtester import Backtester
from src.bot import LiveBot
from src.news_scraper import NewsScraper
from src.ml_predictor import MLPredictor
from src.auto_optimizer import AutoOptimizer

class TestImports(unittest.TestCase):
    def test_imports(self):
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()
