import pandas as pd
import numpy as np
from pstan.processors import Processor

class Pressure(Processor):
    def __init__(self, window = 16):
        self.window = window

    def process(self, df: pd.DataFrame):
        df = df.copy()

        # --- Buying vs Selling Pressure ---
        df['Buying_pressure'] = np.where(
            df['Is_regular_hours'] & (df['Range'] > 0),  # Only when range exists
            df['Volume'] * ((df['Close'] - df['Low']) / df['Range']),
            0  # Use 0 instead of NaN for aggregation
        )
        df['Selling_pressure'] = np.where(
            df['Is_regular_hours'] & (df['Range'] > 0),  # Only when range exists
            df['Volume'] * ((df['High'] - df['Close']) / df['Range']),
            0  # Use 0 instead of NaN for aggregation
        )
        
        # Calculate ratio with safe division
        buying_sum = df['Buying_pressure'].rolling(self.window).sum()
        selling_sum = df['Selling_pressure'].rolling(self.window).sum()
        df['Buy_sell_ratio'] = np.where(
            selling_sum > 0,
            buying_sum / selling_sum,
            np.nan
        )

        return df

    @staticmethod
    def plot(df: pd.DataFrame, ax):
        df.plot(y='Buy_sell_ratio', ax=ax, color='greenyellow', alpha=0.8, linewidth=1.5, label='Buy/Sell Ratio')
        ax.axhline(y=1, color='gray', linestyle='--', linewidth=1, label='Equilibrium')
        ax.axhline(y=1.5, color='lightgreen', linestyle='--', linewidth=0.8, alpha=0.5)
        ax.fill_between(range(len(df)), 1, df['Buy_sell_ratio'], 
                         where=(df['Buy_sell_ratio'] >= 1), alpha=0.2, color='lightgreen', interpolate=True)
        ax.fill_between(range(len(df)), 1, df['Buy_sell_ratio'], 
                         where=(df['Buy_sell_ratio'] < 1), alpha=0.2, color='red', interpolate=True)
        ax.set_title('Buying vs Selling Pressure')
        ax.set_ylabel('Ratio')
