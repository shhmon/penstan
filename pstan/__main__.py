from datetime import timedelta
import matplotlib.pyplot as plt
import pandas as pd

from pstan.data.yfinance import fetch_data_yfinance
from pstan.processors.base import Base
from pstan.processors.boll import Boll
from pstan.processors.macd import MACD
from pstan.processors.pressure import Pressure
from pstan.processors.rsi import RSI
from pstan.processors.volume import Volume
from pstan.processors.atr import ATR

if __name__ == '__main__':
    df = fetch_data_yfinance(
        symbol='BYND',
        period=timedelta(days=60),
        interval='1h',
        prepost=True
    )

    window = 8

    df = Base(window=window).process(pd.DataFrame(df))
    df = Volume(window=window).process(df)
    df = RSI(window=window).process(df)
    df = MACD(window=window).process(df)
    df = Boll(window=window).process(df)
    df = ATR(window=window).process(df)
    df = Pressure(window=window).process(df)

    fig, (ax1, ax2, ax3, ax4, ax5, ax6, ax7) = plt.subplots(7, 1, figsize=(14, 20), sharex=True) 

    Boll.plot(df, ax1)
    Base.plot(df, ax2)
    ATR.plot(df, ax3)
    Volume.plot_ratio(df, ax4)
    RSI.plot(df, ax5)
    Pressure.plot(df, ax6)
    Volume.plot_obv(df, ax7)
    Volume.plot_momentum(df, ax7)


