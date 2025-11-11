import pandas as pd
from pstan.processors import Processor
from pstan.utils.plot import scatter_dot

class Signals(Processor):
    def __init__(
        self, 
        window = 16,
    ):
        self.window = window
    
    def process(self, df: pd.DataFrame):
        df = df.copy()

        #df['Signal'] = \
        #    (df['ATR_break']) & (df['MACD_buy_signal'].rolling(self.window).max() == 1) | \
        #    (df['MACD_buy_signal']) & (df['ATR_break'].rolling(self.window).max() == 1)

            #(df['OBV'] > 0)  & \
        df['Signal'] = \
            (df['ATR_break'].rolling(self.window).max() == 1) & \
            (df['Volume_ratio_slow'] > 3) & \
            (df['Buy_sell_ratio'] > 1) & \
            (df['RSI'] > 60) & \
            ((df['MACD']).rolling(self.window*2).max() == 1) & \
            (df['MACD'].diff() > 0) & \
            (df['Volume_momentum_norm'] > 2) & \
            (df['Boll_breakout_h'].rolling(self.window).max() == 1) & \
            (pd.Series(df['Boll_w'].rolling(window=self.window).mean()).diff() > 0)


        return df

    def print(self, df):
        for idx, row in df[df['Signal'] == 1].iterrows():
            print(f" - {idx} | Close: {row['Close']}")

    @staticmethod
    def plot(df: pd.DataFrame, ax):
        h = max(df['Close'].max(), df['Boll_h'].max())
        scatter_dot(df, ax, column='Signal', y=h*0.9, color='limegreen', label='Combined Signal', marker='^')
