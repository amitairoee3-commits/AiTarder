import feedparser
from textblob import TextBlob
from datetime import datetime
import pandas as pd

class NewsScraper:
    def __init__(self):
        # We use Cointelegraph RSS feed as a primary source for Crypto news
        self.feed_url = "https://cointelegraph.com/rss"

    def fetch_recent_news(self):
        """
        Fetches the latest news from the RSS feed, parses headlines,
        and calculates a polarity sentiment score using TextBlob.
        """
        try:
            feed = feedparser.parse(self.feed_url)
            news_items = []

            for entry in feed.entries[:20]: # get latest 20
                title = entry.get('title', '')
                summary = entry.get('summary', '')

                # Analyze sentiment on the title
                blob = TextBlob(title)
                sentiment_score = blob.sentiment.polarity

                news_items.append({
                    'title': title,
                    'summary': summary,
                    'link': entry.get('link', ''),
                    'published': entry.get('published', datetime.now()),
                    'sentiment': sentiment_score
                })

            return news_items
        except Exception as e:
            print(f"Error fetching news: {e}")
            return []

    def get_aggregated_sentiment(self):
        """
        Returns a single aggregated sentiment score for the market
        based on the latest headlines. (-1.0 to 1.0)
        """
        news = self.fetch_recent_news()
        if not news:
            return 0.0

        total_sentiment = sum(item['sentiment'] for item in news)
        avg_sentiment = total_sentiment / len(news)
        return avg_sentiment

if __name__ == "__main__":
    import nltk
    nltk.download('punkt')
    scraper = NewsScraper()
    news = scraper.fetch_recent_news()
    for n in news[:3]:
        print(f"[{n['sentiment']:.2f}] {n['title']}")
    print(f"Aggregated Sentiment: {scraper.get_aggregated_sentiment():.2f}")
