import pandas as pd
import numpy as np

def normalize(series):
    # convert to float and replace inf/-inf with NaN
    series = series.astype(float).replace([np.inf, -np.inf], np.nan)
    
    s = series.dropna()
    
    if s.empty or s.max() == s.min():  # avoid division by zero
        return pd.Series(0, index=series.index)
    
    return (series - s.min()) / (s.max() - s.min())


def normalize_signed(series):
    # Convert to float and replace inf/-inf with NaN
    series = series.astype(float).replace([np.inf, -np.inf], np.nan)
    
    s = series.dropna()
    
    if s.empty or s.std() == 0:  # avoid division by zero
        return pd.Series(0, index=series.index)
    
    max_abs = max(abs(s.min()), abs(s.max()))
    return series / max_abs  # scales to [-1, 1]

def scatter_dot(df, ax, column, y, color=None, label=None):
    """Plot signal indicators as scatter points"""
    if column not in df.columns:
        return
    signal_positions = df.index[df[column].astype(bool)]
    if len(signal_positions) == 0:
        return
    signal_positions = [df.index.get_loc(dt) for dt in signal_positions]
    ax.scatter(signal_positions, [y]*len(signal_positions), 
               color=color, s=12, zorder=6, label=label or column, marker='|', linewidths=2)
