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
    pass


