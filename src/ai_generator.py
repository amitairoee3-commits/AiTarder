import os
import openai
from dotenv import load_dotenv

load_dotenv()

class AIGenerator:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if self.api_key:
            openai.api_key = self.api_key
        else:
            print("WARNING: OPENAI_API_KEY not found in .env. AI generation will be disabled.")

    def generate_strategy(self, prompt_text: str) -> str:
        """
        Takes natural language input from the user and returns executable
        Python code for a Backtrader Strategy.
        """
        if not self.api_key:
            return "# Error: OPENAI_API_KEY is missing. Please add it to your .env file."

        system_prompt = """
        You are an expert quantitative developer.
        Your task is to write a trading strategy in Python using the 'backtrader' library.
        Only output the raw Python code, do not use markdown blocks like ```python, just plain text.
        The class name MUST be `AIStrategy`.
        The strategy must extend `backtrader.Strategy`.
        Ensure you import backtrader as bt.
        Do not write data loading code, only the strategy class.
        IMPORTANT: The custom data feed you are using has an extra line called 'whale_volume'.
        You can access it in the strategy via `self.data.whale_volume`.
        """

        try:
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt_text}
                ],
                temperature=0.2
            )
            strategy_code = response.choices[0].message.content
            return strategy_code.strip()
        except Exception as e:
            return f"# Error generating strategy: {e}"
