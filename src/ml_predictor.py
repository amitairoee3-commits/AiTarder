import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib
import os

class MLPredictor:
    def __init__(self, model_path='models/rf_model.pkl'):
        self.model_path = model_path
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False

        # Ensure models directory exists
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)

        # Try loading existing model
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.model_path.replace('.pkl', '_scaler.pkl'))
                self.is_trained = True
                print("Loaded pre-trained ML model.")
            except Exception as e:
                print(f"Could not load ML model: {e}")

    def prepare_features(self, df: pd.DataFrame, news_sentiment: float):
        """
        Engineers features for the ML model based on OHLCV, whale volume, and news sentiment.
        """
        # Create a copy to avoid SettingWithCopyWarning
        data = df.copy()

        # Feature engineering
        data['returns'] = data['close'].pct_change()
        data['volatility'] = data['returns'].rolling(window=10).std()
        data['sma_10'] = data['close'].rolling(window=10).mean()
        data['sma_50'] = data['close'].rolling(window=50).mean()

        # In a real environment, historical news sentiment would be matched to timestamps.
        # For this autonomous setup, we proxy recent sentiment into a column.
        data['sentiment'] = news_sentiment

        # Target variable: 1 if next period's close is higher than current close, else 0
        data['target'] = (data['close'].shift(-1) > data['close']).astype(int)

        data.dropna(inplace=True)

        features = ['open', 'high', 'low', 'close', 'volume', 'whale_volume',
                   'returns', 'volatility', 'sma_10', 'sma_50', 'sentiment']

        return data[features], data['target']

    def train(self, historical_df: pd.DataFrame, current_sentiment: float):
        """
        Trains the Random Forest model on historical data.
        """
        print("Training ML model...")
        X, y = self.prepare_features(historical_df, current_sentiment)

        if len(X) < 50:
            print("Not enough data to train ML model.")
            return False

        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Train model
        self.model.fit(X_scaled, y)
        self.is_trained = True

        # Save model
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.scaler, self.model_path.replace('.pkl', '_scaler.pkl'))

        print("ML model training complete and saved.")
        return True

    def predict(self, current_bar: pd.DataFrame, current_sentiment: float):
        """
        Predicts if the next bar will be higher (1) or lower (0).
        current_bar must contain at least 50 historical periods to calculate SMAs.
        """
        if not self.is_trained:
            return 0 # Neutral/hold if not trained

        X, _ = self.prepare_features(current_bar, current_sentiment)
        if len(X) == 0:
            return 0

        # Predict on the latest feature row
        latest_features = X.iloc[-1:]
        scaled_features = self.scaler.transform(latest_features)

        prediction = self.model.predict(scaled_features)[0]
        probability = self.model.predict_proba(scaled_features)[0][1] # Prob of class 1

        return prediction, probability
