import pandas as pd
import numpy as np
from pstan.processors import Processor
from pstan.utils.process import normalize

class Base(Processor):
    def __init__(self, window = 16):
        self.window = window

    def efficiency_ratio(self, series, period = 12):
        change = abs(series.diff(period))
        volatility = series.diff().abs().rolling(period).sum()
        return change / volatility.replace(0, np.nan)

    def process(self, df: pd.DataFrame):
        df = df.copy()

        # Need to convert dates to string to easily align bar charts and lines
        df.index = df.index.astype(str)

        # Light smoothing to reduce yfinance noise (apply before other processing)
        df['Volume_raw'] = df['Volume'].copy()
        df['Volume'] = df['Volume'].rolling(window=2).mean()

        df['Volume_n'] = normalize(df['Volume'])
        df['Close_n'] = normalize(df['Close'])

        # --- Price Metrics ---
        df['Close_pct_change'] = df['Close'].pct_change().fillna(0)
        df['Close_roll'] = df['Close'].rolling(window=self.window).mean()
        df['Price_efficiency'] = self.efficiency_ratio(df['Close'], self.window)

        df['Close_roc_fast'] = df['Close'].pct_change(periods=self.window//2)
        df['Close_roc_slow'] = df['Close'].pct_change(periods=self.window*2)

        # --- Volume Metrics ---
        # Mark regular vs pre/post market hours (yfinance sets volume=0 for pre/post)
        df['Is_regular_hours'] = df['Volume_raw'] > 0
        df['Is_prepost'] = ~df['Is_regular_hours']
        df['Volume_valid'] = df['Volume'].replace(0, np.nan)

        # --- Candle Metrics ---
        df['Gain'] = df['Close'] - df['Open']
        df['Range'] = df['High'] - df['Low']
        df['Range_pct'] = df['Range'] / df['Close']
        df['Gain_close_ratio'] = df['Gain'] / df['Close']
        df['Typical_price'] = (df['High'] + df['Low'] + df['Close']) / 3
        
        # --- Support/Resistance ---
        df['Resistance'] = df['High'].rolling(window=self.window*2).max()
        df['Support'] = df['Low'].rolling(window=self.window*2).min()
        df['Distance_to_resistance'] = (df['Resistance'] - df['Close']) / df['Close']
        df['Distance_to_support'] = (df['Close'] - df['Support']) / df['Close']

        # --- Gap Metric ---
        df['Gap'] = df['Open'] - df['Close'].shift(1)
        df['Gap_pct'] = df['Gap'] / df['Close'].shift(1)
        df['Gap_up'] = df['Gap_pct'] > 0.01  # 1% gap up
        df['Big_gap_up'] = df['Gap_pct'] > 0.10  # 10%+ gap (captures pre/post moves)
        df['Big_gap_down'] = df['Gap_pct'] < -0.10

        # --- Money Flow ---
        df['Money_flow'] = df['Typical_price'] * df['Volume_valid'].fillna(0)
        df['Money_flow_ratio'] = df['Money_flow'] / df['Money_flow'].rolling(self.window).mean()

        # --- High of Day Breaks ---
        df['HOD'] = df['High'].expanding().max()  # High of day
        df['New_HOD'] = df['High'] >= df['HOD'].shift(1)  # Breaking into new HOD
        df['HOD_break'] = df['New_HOD'] & (df['Close'] > df['Open'])  # Green at HOD

        # --- Consecutive Green Candles & Momentum ---
        df['Green_streak'] = (df['Gain'] > 0).astype(int).groupby(
            (df['Gain'] <= 0).astype(int).cumsum()
        ).cumsum()
        df['Spike_momentum'] = df['Green_streak'] >= 3  # 3+ green bars = momentum

        return df

    @staticmethod
    def plot_prepost(df: pd.DataFrame, ax):
        for idx in df.index[df['Is_prepost']]:
            pos = df.index.get_loc(idx)
            ax.axvspan(pos-0.5, pos+0.5, alpha=0.05, color='gray', zorder=1)

    @staticmethod
    def plot(df: pd.DataFrame, ax):
        df.plot(y='Volume_n', ax=ax, kind='bar', alpha=0.4, width=1, color='steelblue', label='Volume')
        df.plot(y='Close_n', ax=ax, kind='line', color='white', linewidth=1, label='Close')
        ax.set_title('Normalized Close & Volume')
        ax.set_ylabel('Normalized (0-1)')
        Base.plot_prepost(df, ax)

