import pandas as pd
import numpy as np
from pstan.processors import Processor

class Volume(Processor):
    def __init__(
        self, 
        window = 16,
    ):
        self.window = window

    def calc_volume_trend(self, series, window = 16) -> pd.Series:
        def trend_check(x):
            if len(x) < 2:
                return 0
            slope = np.polyfit(range(len(x)), x, 1)[0]
            return 1 if slope > 0 else 0

        return series.rolling(window).apply(trend_check, raw=False)
    
    def process(self, df: pd.DataFrame):
        df = df.copy()

        
        # Create volume metrics that handle missing pre/post data
        df['Volume_ewm_base'] = df['Volume_valid'].ewm(span=self.window, adjust=False).mean()
        df['Volume_ewm'] = df['Volume_ewm_base'].ffill()  # Forward fill for continuity

        df['Volume_ratio'] = np.where(
            df['Is_regular_hours'],
            df['Volume'] / df['Volume_ewm'],
            np.nan
        )
        df['Volume_pct_change'] = df['Volume'].pct_change().fillna(0)
        df['Volume_pct_change_regular'] = np.where(
            df['Is_regular_hours'],
            df['Volume_pct_change'],
            np.nan
        )

        # --- Volume Acceleration & Persistence ---
        df['Volume_acceleration'] = df['Volume_ratio'].diff()
        df['Volume_elevated_count'] = (df['Volume_ratio'] > 2.0).rolling(self.window).sum()

        # --- Volume Trend (is volume increasing?) ---
        df['Volume_trend'] = self.calc_volume_trend(df['Volume_ratio'], self.window)

        df['Volume_ratio_fast'] = df['Volume'] / df['Volume'].ewm(span=self.window//2).mean()
        df['Volume_ratio_slow'] = df['Volume'] / df['Volume'].ewm(span=self.window**2).mean()

        # z-score
        df['Volume_momentum_norm'] = (
            (df['Volume'] - df['Volume'].rolling(self.window).mean()) / 
            df['Volume'].rolling(self.window).std()
        )

        # Buying/Selling Pressure within candle
        df['Volume_sentiment'] = np.where(
            df['High'] != df['Low'],
            ((df['Close'] - df['Low']) - (df['High'] - df['Close'])) / 
            (df['High'] - df['Low']) * df['Volume'],
            0
        )

        df['Volume_confirmable'] = df['Is_regular_hours'] & (df['Volume_ratio'].notna())

        # --- On-Balance Volume (OBV) - only use when volume is valid ---
        df['OBV'] = (np.sign(df['Close'].diff()) * df['Volume_valid']).fillna(0).cumsum()
        df['OBV_change'] = df['OBV'].pct_change(periods=self.window).fillna(0)

        return df
    
    @staticmethod
    def plot(df: pd.DataFrame, ax):
        # Color ALL bars based on regular vs pre/post - don't filter anything
        ax.bar(range(len(df)), df['Volume'], width=1, color="white", alpha=0.4, label='Volume')
        ax.set_yscale('log')
        ax.set_title('Volume')
        ax.set_ylabel('Volume (log scale)')
        ax.set_xlim(-0.5, len(df)-0.5)
        
        # Add volume ratio on secondary axis - show it for all bars but only meaningful during regular hours
        ax2 = ax.twinx()
        ax2.plot(range(len(df)), df['Volume_ratio'], color='#1E90FF', linewidth=2, alpha=0.8, label='Vol Ratio')
        ax2.set_ylabel('Volume Ratio', color='#1E90FF')
        ax2.axhline(y=2, color='red', linestyle='--', linewidth=0.8, alpha=0.5, label='2x')
        ax2.axhline(y=3, color='darkred', linestyle='--', linewidth=0.8, alpha=0.5, label='3x')
        ax2.legend(fontsize=7, loc='upper right')

    @staticmethod
    def plot_ratio(df: pd.DataFrame, ax):
        df.plot(y='Volume_ratio', ax=ax, color='darkblue', linewidth=2, label='Volume Ratio')
        df.plot(y='Volume_ratio_fast', ax=ax, color='blue', alpha=0.7, linewidth=1.5, label='Vol Ratio Fast')
        df.plot(y='Volume_ratio_slow', ax=ax, color='mediumblue', alpha=0.7, linewidth=1.5, label='Vol Ratio Slow')
        ax.axhline(y=1, color='gray', linestyle='--', linewidth=0.8)
        ax.axhline(y=2, color='orange', linestyle='--', linewidth=0.8, alpha=0.5)
        ax.axhline(y=3, color='red', linestyle='--', linewidth=0.8, alpha=0.5)
        ax.set_title('Volume Ratios (Multi-timeframe)')
        ax.set_ylabel('Ratio')

    @staticmethod
    def plot_sentiment(df: pd.DataFrame, ax):
        df.plot(y='Volume_sentiment', ax=ax, kind='bar', alpha=0.6, width=1, 
                 color=df['Volume_sentiment'].apply(lambda x: 'green' if x > 0 else 'red'),
                 label='Volume Sentiment')
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax2 = ax.twinx()
        df.plot(y='Volume_acceleration', ax=ax2, color='blue', linewidth=1, alpha=0.7, label='Vol Acceleration')
        ax2.axhline(y=0, color='gray', linestyle='--', linewidth=0.5)
        ax.set_title('Volume Sentiment & Acceleration')
        ax.set_ylabel('Volume Sentiment')
        ax2.set_ylabel('Volume Acceleration', color='blue')

    @staticmethod
    def plot_momentum(df: pd.DataFrame, ax):
        df.plot(y='Volume_momentum_norm', ax=ax, kind='bar', color='teal', width=1, label='Vol Momentum Z-score')
        ax.axhline(y=2, color='red', linestyle='--', linewidth=1, alpha=0.7, label='2σ')
        ax.axhline(y=-2, color='green', linestyle='--', linewidth=1, alpha=0.7, label='-2σ')
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax.set_title('Volume Momentum (Z-score)')
        ax.set_ylabel('Standard Deviations')

    @staticmethod
    def plot_obv(df: pd.DataFrame, ax):
        df.plot(y='OBV', ax=ax, color='purple', linewidth=1.5, label='OBV')
        ax.set_title('On-Balance Volume (OBV)')
        ax.set_ylabel('Cumulative Volume')
        ax2 = ax.twinx()
        df.plot(y='OBV_change', ax=ax2, kind='bar', alpha=0.3, width=1, color='violet', label='OBV Change %')
        ax2.set_ylabel('OBV % Change', color='violet')
        ax2.axhline(y=0, color='gray', linestyle='-', linewidth=0.5)
