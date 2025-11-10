import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
from massive import RESTClient

def fetch_data_polygon(
    symbol: str, 
    from_date: datetime,
    to_date = None,
    timespan = 'hour',
    multiplier = 1,
) -> dict[str, pd.DataFrame]:
    api_key = 'hzd_L29WkBpCYrvkjCHbS2o1ReRGebGY'
    client = RESTClient(api_key)

        # Handle default to_date
    if to_date is None:
        to_date = datetime.now()
    
    # If datetime is naive (no timezone), assume it's Stockholm time
    stockholm_tz = ZoneInfo("Europe/Stockholm")
    if from_date.tzinfo is None:
        from_date = from_date.replace(tzinfo=stockholm_tz)
    if to_date.tzinfo is None:
        to_date = to_date.replace(tzinfo=stockholm_tz)
    
    
    # Fetch aggregates (bars) for the symbol
    aggs = []
    for agg in client.list_aggs(
        ticker=symbol,
        multiplier=multiplier,
        timespan=timespan,
        from_=int(from_date.timestamp()),
        to=int(to_date.timestamp()),
        adjusted=True,
        limit=50000
    ): aggs.append(agg)
    
    # Convert to DataFrame
    df = pd.DataFrame([{
        'Open': a.open,
        'High': a.high,
        'Low': a.low,
        'Close': a.close,
        'Volume': a.volume,
        'timestamp': a.timestamp
    } for a in aggs])

    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
    df.set_index('timestamp', inplace=True)
    df.index = df.index.tz_convert("Europe/Stockholm")
    
    # Add calculated fields
    df['Volatility'] = ((df['High'] - df['Low']) / df['Close'] * 100)
    df['Change'] = ((df['Close'] - df['Open']) / df['Open'] * 100)
    
    # Type conversions
    df = df.astype({
        'Open': float,
        'High': float,
        'Low': float,
        'Close': float,
        'Volatility': float,
        'Change': float,
        'Volume': int
    })
    
    return df
