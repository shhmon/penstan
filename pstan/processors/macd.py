import pandas as pd
import numpy as np
from pstan.processors import Processor

class MACD(Processor):
    def __init__(
        self, 
        window = 16
    ):
        self.window = window

    def process(self, df: pd.DataFrame):
        df = df.copy()

        ema_s = df['Close'].ewm(span=self.window // 2, adjust=False).mean()
        ema_l = df['Close'].ewm(span=self.window * 2, adjust=False).mean()
        df['MACD'] = ema_s - ema_l 
        df['MACD_signal'] = df['MACD'].ewm(span=self.window, adjust=False).mean()
        df['hist_difference'] = df['MACD'] - df['MACD_signal']
        ema_trend = df['Close'].ewm(span=self.window * 10, adjust=False).mean()
        trendDirection = np.where(df['Close'] > ema_trend, "up", "down")

        df['MACD_buy_signal'] = (
            (df['hist_difference'].shift(1) < 0) & (df['hist_difference'] > 0) &
            (df['MACD'] < 0) & (df['MACD_signal'] < 0) &
            (trendDirection == "up")
        ).astype(int)

        return df

    @staticmethod
    def plot(df: pd.DataFrame, ax):
        buy_points = df[df['MACD_signal'] == 1]
        ax.plot(df.index, df["MACD"], color="#1E90FF", linewidth=1.2, label="MACD")
        ax.plot(df.index, df["MACD_signal"], color="#FFB347", linewidth=1.2, label="Signal")
        ax.axhline(0, color="#888888", linestyle="--", linewidth=1)
        for _, row in buy_points.iterrows():
            ax.annotate('↑', (row.index, row['MACD']),
                         color='#00FF88', fontsize=12, ha='center')

        ax.legend(loc="upper left", fontsize=9)
        ax.set_ylabel("MACD")
        ax.grid(True, linestyle="--", alpha=0.3)
