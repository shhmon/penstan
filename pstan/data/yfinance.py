from typing import Literal
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import pytz

Interval = Literal['1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '4h', '1d', '5d', '1wk', '1mo', '3mo']
    
def tz_aware(date):
    # Make timezone-aware for comparison
    if isinstance(date, datetime):
        if date.tzinfo is None:
            stockholm_tz = pytz.timezone('Europe/Stockholm')
            date = stockholm_tz.localize(date)
        else:
            date = start.astimezone(pytz.timezone('Europe/Stockholm'))
            
    return date
        
def fetch_data_yfinance(
    symbol: str,
    interval: Interval,
    period = timedelta(days=7),
    start = None,
    end = None,
    prepost = False,
):
    start = start if start else datetime.now() - period
    end = end if end else datetime.now()
    buffer_start = start - timedelta(days=1) # yfinance quirk
    
    data = yf.download(
        symbol,
        start=buffer_start,
        end=end,
        interval=interval,
        auto_adjust=True,
        progress=False, # Suppress progress bar
        prepost=prepost,
        multi_level_index=False
    )
    
    if data is None or data.empty:
        return pd.DataFrame()
    
    # Convert timezone to Europe/Stockholm
    #if data.index.tz is None:
        #data.index = data.index.tz_localize('UTC')
        
    data.index = data.index.tz_convert('Europe/Stockholm')

    start = tz_aware(start)
    end = tz_aware(end)

    data = data[data.index >= start]
    data = data[data.index <= end]

    return data

def print_meta(symbol: str, df: pd.DataFrame):
    rnd, w = 4, 40

    ticker = yf.Ticker(symbol)
    price = round(df['Close'].iloc[-1].item(), rnd)
    eps = ticker.info['epsTrailingTwelveMonths']
    pe = round(price/eps, rnd)

    fill = (w // 2) - (len(symbol) // 2)

    print('=' * w)
    print('-' * fill + symbol + '-' * fill)
    print('=' * w)
    print(f'''
        {price=},
        {eps=},
        {pe=},
        {ticker.calendar=},
        {ticker.analyst_price_targets=},
    ''')
    print('-' * w)
