from typing import Literal
import numpy as np
import pandas as pd
import yfinance as yf
import json

type Time = Literal['1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '4h', '1d', '5d', '1wk', '1mo', '3mo']

def set_timezone(dt_index: pd.DatetimeIndex, target_tz: str = "Etc/GMT-1") -> pd.DatetimeIndex:
    if dt_index.tz and dt_index.tz.tzname != target_tz:
        dt_index = dt_index.tz_convert(target_tz)

    return dt_index


def fetch_data(symbols: list[str], interval: Time, period: Time | None, test: bool = False) -> dict[str, pd.DataFrame]:
    data = yf.download(
        symbols, 
        period=period,
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

        df = df.iloc[:-3]
            
        result[symbol] = df
    
    return result

def analyze_volume(df: pd.DataFrame, lookback: int, recent: int) -> pd.Series:
    vol = df['Volume']

    # EWMA smoothing
    vol_ewm = vol.ewm(span=lookback, adjust=False).mean()

    current_volume = vol.iloc[-1]
    avg_all = vol_ewm.mean()

    avg_recent = vol_ewm.tail(recent).mean()
    avg_back = vol_ewm.iloc[-(lookback+recent):-recent].mean() if len(vol_ewm) >= lookback + recent else avg_all

    ratio_global = current_volume / avg_all if avg_all > 0 else 0
    ratio_local = avg_recent / avg_back if avg_back > 0 else 0

    # Trend detection (local)
    if avg_recent > avg_back * 1.5:
        trend = 'increasing'
    elif avg_recent < avg_back * 0.7:
        trend = 'decreasing'
    else:
        trend = 'stable'

    # “Unusual” volume detection — global context
    is_spike = current_volume > avg_all * 5

    return pd.Series({
        'current_volume': int(current_volume),
        'avg_volume_all': int(avg_all),
        'avg_volume_back': int(avg_back),
        'avg_volume_recent': int(avg_recent),
        'volume_ratio_global': ratio_global,
        'volume_ratio_local': ratio_local,
        'volume_trend': trend,
        'is_spike': is_spike
    })

def analyze_price(df: pd.DataFrame, lookback: int, recent: int) -> pd.Series:
    current_price = df['Close'].iloc[-1]

    # Short-term support/resistance
    local_support = df['Low'].tail(lookback).min()
    local_resistance = df['High'].tail(lookback).max()

    # Long-term trend detection via rolling mean
    short_mean = pd.Series(df['Close'].rolling(window=recent, min_periods=recent//2).mean())
    long_mean = pd.Series(df['Close'].rolling(window=lookback, min_periods=lookback//2).mean())

    recent_mean = short_mean.tail(recent).mean()
    prior_mean = long_mean.iloc[-(lookback+recent):-recent].mean()
    momentum_ratio = (recent_mean / prior_mean - 1) if prior_mean != 0 else 0

    y = df['Close'][-recent:]
    x = np.arange(len(y), dtype=float)
    gradient = np.polyfit(x, y, 1)[0] / np.mean(y)

    trend = (
        'bullish' if momentum_ratio > 0.05 or gradient > 0.001 else
        'bearish' if momentum_ratio < -0.05 or gradient < -0.001 else
        'neutral'
    )

    distance_from_support = ((current_price - local_support) / local_support) * 100
    distance_from_resistance = ((local_resistance - current_price) / local_resistance) * 100

    return pd.Series({
        'current_price': current_price,
        'trend': trend,
        'momentum_ratio': momentum_ratio,
        'price_gradient': gradient,
        'local_support': local_support,
        'local_resistance': local_resistance,
        'distance_from_local_support_pct': distance_from_support,
        'distance_from_local_resistance_pct': distance_from_resistance,
        'is_near_local_support': distance_from_support < 5,
        'is_near_local_resistance': distance_from_resistance < 5
    })

def analyze_volatility(df: pd.DataFrame, lookback: int, recent: int) -> pd.Series:
    vol = df['Volatility']
    current_volatility = vol.iloc[-1]

    ema_vol = vol.ewm(span=lookback, adjust=False).mean()
    recent_avg = ema_vol.tail(recent).mean()
    prior_avg = ema_vol.iloc[-(lookback+recent):-recent].mean() if len(vol) >= lookback+recent else ema_vol.mean()

    ratio_global = current_volatility / vol.mean() if vol.mean() > 0 else 0
    ratio_local = recent_avg / prior_avg if prior_avg > 0 else 0

    trend = 'increasing' if recent_avg > prior_avg * 1.1 else 'decreasing' if recent_avg < prior_avg * 0.9 else 'stable'

    return pd.Series({
        'current_volatility': current_volatility,
        'volatility_ratio_global': ratio_global,
        'volatility_ratio_local': ratio_local,
        'volatility_trend': trend
    })

def opportunity_score(df: pd.DataFrame, lookback: int = 20, recent: int = 5, local: bool = False) -> dict:
    volume_analysis = analyze_volume(df, lookback, recent)
    price_analysis = analyze_price(df, lookback, recent)
    volatility_analysis = analyze_volatility(df, lookback, recent)

    score = 0
    signals: list[str] = []

    # Volume scoring
    if local:
        if volume_analysis['volume_ratio_local'] > 2:
            score += 30
            signals.append('extreme_volume_local')
        if volatility_analysis['volatility_ratio_local'] > 1.5:
            score += 10
            signals.append('volatility_spike_local')
    else:
        if volume_analysis['volume_ratio_global'] > 1.5 and volume_analysis['is_spike'] == False:
            score += 20
            signals.append('sustained_volume_global')
        elif volume_analysis['is_spike'] == True:
            signals.append('volume_spike_global')  # flag but don't score heavily

        if volatility_analysis['volatility_ratio_global'] > 2:
            score += 10
            signals.append('high_volatility_global')

            
    gradient = price_analysis['price_gradient']

    # Use gradient as a smoother directional confirmation
    if gradient > 0.002:
        score += 10
        signals.append('strong_upward_gradient')
    elif gradient < -0.002:
        score -= 10
        signals.append('downward_gradient')

    if price_analysis['is_near_local_support'] == True and price_analysis['momentum_ratio'] > 0:
        score += 20
        signals.append('bounce_off_support')

    if price_analysis['trend'] == 'bullish':
        score += 10
        signals.append('bullish_trend')
    elif price_analysis['trend'] == 'bearish':
        score -= 10
        signals.append('bearish_trend')

    # --- Volatility trend ---
    if volatility_analysis['volatility_trend'] == 'increasing':
        score += 10
        signals.append('volatility_rising')

    # --- Combo signals ---
    if local and 'extreme_volume_local' in signals and 'bounce_off_support' in signals:
        score += 10
        signals.append('high_conviction_local')

    # Clamp & rate
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
    short_score = opportunity_score(short_df, lookback=12, recent=2, local=True)

    # Long-term (1d)
    long_df = fetch_data([symbol], '1d', '1mo')[symbol]
    long_score = opportunity_score(long_df, lookback=15, recent=3, local=False)

    with pd.option_context('display.max_rows', None):
        print(long_df[['Close', 'Open', 'High', 'Low', 'Volatility', 'Volume', 'Change']])

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
    print(json.dumps(multi_timeframe_opportunity('GPUS'), indent=4))
    # data = fetch_data(['MSAI'], '1d', '1mo')['MSAI']
    # print(opportunity_score(data, lookback=10, recent=2))
    # print(analyze_volume(data, lookback=10, recent=2))
    # print(data.loc[:, ['Open', 'Close', 'High', 'Low', 'Volatility', 'Volume', 'Change']])
    # print(analyze_volatility(data, lookback=10, recent=2))
