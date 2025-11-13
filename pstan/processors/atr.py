import pandas as pd
from pstan.processors import Processor
from pstan.processors.base import Base

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

        df['ATR_break'] = (df['Gain'] > 0) & (df['Gain'] > (self.break_threshold * df['ATR'])) #| (df['Range'] > self.break_threshold * df['ATR'])

        return df

    def plot(self, df: pd.DataFrame, ax):
        break_points = df.index[df['ATR_break'].astype(bool)]
        break_positions = [df.index.get_loc(dt) for dt in break_points]
        
        if len(break_positions) > 0:
            ax.scatter(break_positions, df.loc[break_points, 'ATR'] * self.break_threshold,
                       color='lightgreen', s=20, zorder=5, label='ATR Break', marker='x', linewidths=0.9)
        
        ax.plot(df.index, df['ATR'], alpha=0.7, color='slategray', label='ATR')
        ax.fill_between(range(len(df)), 0, df['ATR'], alpha=0.7, color='slategray', interpolate=True)
        
        colors = df['Gain'].apply(lambda x: 'yellowgreen' if x >= 0 else 'orangered')
        ax.bar(df.index, df['Gain'], alpha=0.7, width=1, color=colors, label='Gain', zorder=10)
        
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax.set_title('ATR, Gain & Breakout Points')
        ax.set_ylabel('Value')
        Base.plot_prepost(df, ax)
