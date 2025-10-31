from typing import Literal
from numpy import long
import pandas as pd
import yfinance as yf
import json
from datetime import datetime

type Time = Literal['1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '4h', '1d', '5d', '1wk', '1mo', '3mo']

def set_timezone(dt_index: pd.DatetimeIndex, target_tz: str = "Etc/GMT-1") -> pd.DatetimeIndex:
    if dt_index.tz and dt_index.tz.tzname != target_tz:
        dt_index = dt_index.tz_convert(target_tz)

    return dt_index


def fetch_data(symbols: list[str], interval: Time, period: Time | None, test: bool = False) -> dict[str, pd.DataFrame]:
    end = datetime(2025,10,30)
    if test:
        data = yf.download(
            symbols, 
            start='2025-10-07',
            end=end,
            interval=interval,
            group_by='ticker',
            auto_adjust=True,
            threads=True,  # Parallel
        )
    else:
        data = yf.download(
            symbols, 
            start=datetime(2025, 9, 1),
            end=end,
            interval=interval,
            group_by='ticker',
            auto_adjust=True,
            threads=True,  # Parallel
        )

    result = {}

    if data is None or data.empty:
        return result

    tickers = data.columns.get_level_values('Ticker')
    valid_symbols = [symbol for symbol in symbols if symbol in tickers]
    
    for symbol in valid_symbols:
        df = data[symbol].copy()

        df.index = set_timezone(pd.to_datetime(df.index), target_tz="Etc/GMT-1")

        df['Current_Price'] = df.loc[:, 'Close'].iloc[-1]
        df['Current_Volume'] = df.loc[:, 'Volume'].iloc[-1]
        df['Volatility'] = ((df['High'] - df['Low']) / df['Close'] * 100)
        df['Change'] = ((df['Close'] - df['Open']) / df['Open'] * 100)

        df = df.astype({
            'Current_Price': float,
            'Current_Volume': int,
            'Volatility': float,
            'Change': float,
            'Volume': int
        })

        df = df.iloc[:-4]
            
        result[symbol] = df
    
    return result

def analyze_volume(df: pd.DataFrame, lookback: int, recent: int) -> pd.Series:
    vol = df['Volume']
    current_volume = vol.iloc[-1]
    avg_all = vol.mean()

    avg_recent = vol.tail(recent).mean()
    avg_back = vol.iloc[-lookback:-recent].mean() if len(vol) >= lookback else avg_all

    ratio_global = current_volume / avg_all if avg_all > 0 else 0
    ratio_local = avg_recent / avg_back if avg_back > 0 else 0

    if avg_recent > avg_back * 1.5:
        trend = 'increasing'
    elif avg_recent < avg_back * 0.7:
        trend = 'decreasing'
    else:
        trend = 'stable'

    # global context
    is_unusual = current_volume > avg_all * 2

    return pd.Series({
        'current_volume': int(current_volume),
        'avg_volume_all': int(avg_all),
        'avg_volume_back': int(avg_back),
        'avg_volume_recent': int(avg_recent),
        'volume_ratio_global': ratio_global,
        'volume_ratio_local': ratio_local,
        'volume_trend': trend,
        'is_unusual': is_unusual
    })

def analyze_price(df: pd.DataFrame, lookback: int, recent: int) -> pd.Series:
    current_price = df['Close'].iloc[-1]
    price_change_now = df['Change'].iloc[-1]

    local_support = df['Low'].tail(lookback).min()
    local_resistance = df['High'].tail(lookback).max()

    global_support = df['Low'].min()
    global_resistance = df['High'].max()

    distance_from_local_support = ((current_price - local_support) / local_support) * 100
    distance_from_local_resistance = ((local_resistance - current_price) / local_resistance) * 100
    distance_from_global_support = ((current_price - global_support) / global_support) * 100
    distance_from_global_resistance = ((global_resistance - current_price) / global_resistance) * 100

    momentum_local = df['Change'].tail(recent).mean()
    momentum_global = df['Change'].mean()

    if momentum_local > 2:
        trend = 'bullish'
    elif momentum_local < -2:
        trend = 'bearish'
    else:
        trend = 'neutral'

    return pd.Series({
        'current_price': current_price,
        'price_change_now': price_change_now,

        'local_support': local_support,
        'local_resistance': local_resistance,
        'global_support': global_support,
        'global_resistance': global_resistance,

        'distance_from_local_support_pct': distance_from_local_support,
        'distance_from_local_resistance_pct': distance_from_local_resistance,
        'distance_from_global_support_pct': distance_from_global_support,
        'distance_from_global_resistance_pct': distance_from_global_resistance,

        'is_near_local_support': distance_from_local_support < 5,
        'is_near_local_resistance': distance_from_local_resistance < 5,
        'is_near_global_support': distance_from_global_support < 5,
        'is_near_global_resistance': distance_from_global_resistance < 5,

        'momentum_local': momentum_local,
        'momentum_global': momentum_global,
        'momentum_ratio': momentum_local / momentum_global if momentum_global != 0 else None,
        'momentum_trend': trend,
    })

def analyze_volatility(df: pd.DataFrame, lookback: int, recent: int) -> pd.Series:
    vol = df['Volatility']
    current_volatility = vol.iloc[-1]
    avg_vol_all = vol.mean()

    avg_vol_back = vol.iloc[-lookback:-recent].mean() if len(vol) >= lookback else avg_vol_all
    avg_vol_recent = vol.tail(recent).mean()

    if avg_vol_recent > avg_vol_back * 1.2:
        trend = 'increasing'
    elif avg_vol_recent < avg_vol_back * 0.8:
        trend = 'decreasing'
    else:
        trend = 'stable'

    return pd.Series({
        'current_volatility': current_volatility,
        'avg_volatility_all': avg_vol_all,
        'avg_volatility_back': avg_vol_back,
        'avg_volatility_recent': avg_vol_recent,
        'volatility_ratio_global': current_volatility / avg_vol_all if avg_vol_all > 0 else 0,
        'volatility_ratio_local': avg_vol_recent / avg_vol_back if avg_vol_back > 0 else 0,
        'volatility_trend': trend,
    })

def opportunity_score(df: pd.DataFrame, lookback: int = 20, recent: int = 5, local: bool = False) -> dict:
    volume_analysis = analyze_volume(df, lookback, recent)
    price_analysis = analyze_price(df, lookback, recent)
    volatility_analysis = analyze_volatility(df, lookback, recent)

    score = 0
    signals: list[str] = []

    if local:
        if volume_analysis['volume_ratio_local'] > 2:
            score += 30
            signals.append('extreme_volume_local')
        if volatility_analysis['volatility_ratio_local'] > 1.5:
            score += 10
            signals.append('volatility_spike_local')
    else:
        if volume_analysis['volume_ratio_global'] > 3:
            score += 30
            signals.append('extreme_volume_global')
        if volatility_analysis['volatility_ratio_global'] > 2:
            score += 10
            signals.append('high_volatility_global')

    # --- Price signals (always local) ---
    if price_analysis['is_near_local_support'] == True and price_analysis['momentum_local'] > 0:
        score += 20
        signals.append('bounce_off_support')

    if price_analysis['momentum_trend'] == 'bullish':
        score += 10
        signals.append('bullish_trend')
    elif price_analysis['momentum_trend'] == 'bearish':
        score -= 10
        signals.append('bearish_trend')

    # --- Volatility trend (always local context) ---
    if volatility_analysis['volatility_trend'] == 'increasing':
        score += 10
        signals.append('volatility_rising')

    # --- Combo signals ---
    if local and 'extreme_volume_local' in signals and 'bounce_off_support' in signals:
        score += 10
        signals.append('high_conviction_local')

    score = max(0, min(score, 100))
    rating = (
        'strong_buy' if score >= 70 else
        'buy' if score >= 50 else
        'watch' if score >= 30 else
        'pass'
    )

    return {
        'score': score,
        'signals': signals,
        'rating': rating
    }


def multi_timeframe_opportunity(symbol: str) -> dict:
    # Short-term (1h)
    short_df = fetch_data([symbol], '1h', '1wk', test=True)[symbol]
    short_score = opportunity_score(short_df, lookback=24, recent=4, local=True)

    # Long-term (1d)
    long_df = fetch_data([symbol], '1d', '1mo')[symbol]
    long_score = opportunity_score(long_df, lookback=15, recent=3, local=False)

    # Combine with weighting
    combined_score = short_score['score'] * 0.6 + long_score['score'] * 0.4

    rating = (
        'strong_buy' if combined_score >= 70 else
        'buy' if combined_score >= 50 else
        'watch' if combined_score >= 30 else
        'pass'
    )

    return {
        'symbol': symbol,
        'combined_score': round(combined_score, 1),
        'rating': rating,
        'short_term': short_score,
        'long_term': long_score,
    }

if __name__ == "__main__":
    print(json.dumps(multi_timeframe_opportunity('MSAI'), indent=4))
    # data = fetch_data(['MSAI'], '1d', '1mo')['MSAI']
    # print(opportunity_score(data, lookback=10, recent=2))
    # print(analyze_volume(data, lookback=10, recent=2))
    # print(data.loc[:, ['Open', 'Close', 'High', 'Low', 'Volatility', 'Volume', 'Change']])
    # print(analyze_volatility(data, lookback=10, recent=2))
