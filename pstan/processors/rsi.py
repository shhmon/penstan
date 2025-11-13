import pandas as pd
from pstan.processors import Processor

class RSI(Processor):
    def __init__(
        self, 
        window = 16,
    ):
        self.window = window

    def calculate_rsi_ema(self, series: pd.Series, period=14):
        delta = series.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.ewm(alpha=1/period, min_periods=period).mean()
        avg_loss = loss.ewm(alpha=1/period, min_periods=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
    
        return rsi

    def calculate_rsi_rma(self, series: pd.Series, window=14):
        delta = series.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window).mean()
        avg_loss = loss.rolling(window).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
    
        return rsi
    
    def process(self, df: pd.DataFrame):
        df = df.copy()

        df['RSI'] = self.calculate_rsi_ema(df['Close'], self.window)
        df['RSI_fast'] = self.calculate_rsi_ema(df['Close'], self.window // 2)
        df['RSI_slow'] = self.calculate_rsi_ema(df['Close'], self.window * 2)

        return df

    @staticmethod
    def plot(df: pd.DataFrame, ax):
        df.plot(y='RSI', ax=ax, kind='line', color='mediumpurple', linewidth=1.5, label='RSI')
        df.plot(y='RSI_fast', ax=ax, kind='line', color='cornflowerblue', alpha=0.5, linewidth=1, label='RSI Fast')
        df.plot(y='RSI_slow', ax=ax, kind='line', color='plum', alpha=0.5, linewidth=1, label='RSI Slow')
        ax.axhline(y=70, color='orangered', linestyle='--', linewidth=1, label='Overbought')
        ax.axhline(y=30, color='lightgreen', linestyle='--', linewidth=1, label='Oversold')
        ax.axhline(y=50, color='lightgray', linestyle='-', linewidth=0.5, alpha=0.5)
        ax.set_ylim(0, 100)
        ax.set_title('RSI (Multi-timeframe)')
        ax.set_ylabel('RSI')
