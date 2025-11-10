import pandas as pd
from pstan.processors import Processor

class ATR(Processor):
    def __init__(
        self, 
        window = 16,
        compression_threshold = 0.8,
        break_threshold = 1.9
    ):
        self.window = window
        self.compression_threshold = compression_threshold 
        self.break_threshold = break_threshold

    def true_range(self, df: pd.DataFrame) -> pd.Series:
        high_low = df['High'] - df['Low']
        high_close = (df['High'] - df['Close'].shift()).abs()
        low_close = (df['Low'] - df['Close'].shift()).abs()

        return pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    
    def process(self, df: pd.DataFrame):
        df = df.copy()

        df['TR'] = self.true_range(df)
        df['ATR'] = df['TR'].rolling(window=self.window).mean()
        df['ATR_pct'] = df['ATR'] / df['Close']  # Normalized ATR
        df['ATR_trend'] = df['ATR'].diff()
        df['ATR_compression'] = (df['ATR'] < df['ATR'].rolling(self.window).mean() * self.compression_threshold)

        df['Break'] = (df['Gain'] > 0) & (df['Gain'] > (self.break_threshold * df['ATR'])) #| (df['Range'] > self.break_threshold * df['ATR'])

        return df

    @staticmethod
    def plot(df: pd.DataFrame, ax):
        break_points = df.index[df['Break'].astype(bool)]
        break_positions = [df.index.get_loc(dt) for dt in break_points]
        if len(break_positions) > 0:
            ax.scatter(break_positions, [0]*len(break_positions), 
                       color='orangered', s=20, zorder=5, label='Break', marker='x')
        df.plot(y='ATR', ax=ax, kind='bar', alpha=0.4, width=1, color='turquoise', label='ATR')
        df.plot(y='Gain', ax=ax, kind='bar', alpha=0.5, width=1, color='dodgerblue', label='Gain')
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax.set_title('ATR, Gain & Breakout Points')
        ax.set_ylabel('Value')
