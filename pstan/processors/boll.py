import pandas as pd
from pstan.processors import Processor

class Boll(Processor):
    def __init__(
        self, 
        window = 16,
        squeeze_threshold = 0.7
    ):
        self.window = window
        self.squeeze_threshold = squeeze_threshold

    def bollinger_bands(self, series: pd.Series, length = 20, *, num_stds = (2, 0, -2)) -> pd.DataFrame:
        # Ref: https://stackoverflow.com/a/74283044/
        rolling = series.rolling(length)
        bband0 = rolling.mean()
        bband_std = rolling.std(ddof=0)

        return tuple((bband0 + (bband_std * num_std)) for num_std in num_stds)
    
    def process(self, df: pd.DataFrame):
        df = df.copy()

        df['Boll_h'], df['Boll_m'], df['Boll_l'] = self.bollinger_bands(df['Close'], length=self.window)

        df['Boll_w'] = df['Boll_h'] - df['Boll_l']
        df['Boll_w_avg'] = df['Boll_w'].rolling(self.window).mean()
        df['Boll_squeeze'] = (df['Boll_w'] < df['Boll_w_avg'] * self.squeeze_threshold)
        df['Boll_breakout_h'] = (df['Close'] > df['Boll_h'])
        df['Boll_breakout_l'] = (df['Close'] < df['Boll_l'])
        df['Boll_pct'] = (df['Close'] - df['Boll_l']) / (df['Boll_h'] - df['Boll_l'])

        return df

    @staticmethod
    def plot(df: pd.DataFrame, ax):
        df.plot(y='Close', ax=ax, color='white', linewidth=1.5, label='Close')
        df.plot(y='Boll_h', ax=ax, alpha=0.6, color='skyblue', label='BB Upper')
        df.plot(y='Boll_m', ax=ax, alpha=0.4, color='gray', linestyle='--', linewidth=0.8)
        df.plot(y='Boll_l', ax=ax, alpha=0.6, color='skyblue', label='BB Lower')
        df.plot(y='Boll_w', kind='bar', ax=ax, alpha=0.1, width=1, color='skyblue')
        df[df['Boll_squeeze']].plot(y='Boll_w', kind='bar', ax=ax, alpha=0.3, width=1, color='limegreen', label='Squeeze')
        ax.set_title('Price, Bollinger Bands & Signals', fontweight='bold')
        ax.set_ylabel('Price')
