from pstan.data.yfinance import fetch_data_yfinance, print_meta, Interval 
from pstan.processors.base import Base
from pstan.processors.boll import Boll
from pstan.processors.macd import MACD
from pstan.processors.pressure import Pressure
from pstan.processors.rsi import RSI
from pstan.processors.volume import Volume
from pstan.processors.atr import ATR
from pstan.processors.signals import Signals
from pstan.utils.pipe import pipe
from importlib import reload
from datetime import datetime, timezone, timedelta
import pandas as pd
import matplotlib.pyplot as plt

from pstan.utils.plot import dark_theme_plt

# MSAI CMBM DFLI BYND ASST GPUS DVLT CSAI DTCK RLMD
# CHR FEMY NVVE EGHT NFE ETHZ QH ACRS CCLD IINN WORX OSRH

dark_theme_plt()

def get_metrics(symbol: str):
    window = 16
    intervals: list[Interval] = ['5m', '15m', '30m'] #, , '1h'] 


    fig, axes = plt.subplots(5, 2, figsize=(16, 25), sharex=True) 
    axes = axes.flatten()

    for interval in intervals:
        print(f"\n=== Interval: {interval} ===")
        df = fetch_data_yfinance(
            symbol=symbol,
            period=timedelta(days=14),
            interval=interval,
            prepost=False
        )

        df, p = pipe(
            pd.DataFrame(df), 
            base = Base(window=window),
            vol = Volume(window=window),
            rsi = RSI(window=window),
            macd = MACD(),
            boll = Boll(window=window*2),
            atr = ATR(window=window*2, break_threshold=1.6),
            bsp = Pressure(window=window),
            signals = Signals(window=window)
        )
        print(df.index.dtype)

        p.boll.plot(df, axes[0])
        p.base.plot(df, axes[1])
        p.atr.plot(df, axes[2])
        p.vol.plot_ratio(df, axes[3])
        p.rsi.plot(df, axes[4])
        p.bsp.plot(df, axes[5])
        p.macd.plot(df, axes[6])
        p.vol.plot_momentum(df, axes[7])
        p.vol.plot_obv(df, axes[8])
        p.vol.plot(df, axes[9])

        p.signals.plot(df, axes[0])
        p.signals.print(df)

    for ax in axes:
        # X-axis formatting
        xticks = ax.get_xticks()
        if len(xticks) > 25:
            ax.set_xticks(xticks[::2])
        
        labels = []
        for i in ax.get_xticks():
            if 0 <= int(i) < len(df):
                dt = pd.to_datetime(df.index[int(i)])
                labels.append(dt.strftime('%b %-d %H:%M'))
            else:
                labels.append('')
        ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=7)
        
        # Legend
        handles, labels = ax.get_legend_handles_labels()
        if handles:
            ax.legend(handles, labels, fontsize=7, loc='best')
        
        # Grid
        ax.grid(True, alpha=0.2, linestyle='--', linewidth=0.5)
        ax.tick_params(axis='both', labelsize=8)

    plt.tight_layout()
    plt.show()

