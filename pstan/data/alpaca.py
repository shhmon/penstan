from datetime import datetime, timedelta
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

def fetch_data_alpaca(
    symbol: str,
    start,
    end = None,
    timeframe: TimeFrame = TimeFrame.Hour,
):
    end = end if end else (datetime.now() - timedelta(minutes=15))

    client = StockHistoricalDataClient(
        'AKBCHOMBGL2MLSBHSOEMZDNVOF',
        'FfnxR5fUUXn3qjqg8bKeQSaHK4KLkqekPDdEQUypfRS8'
    )

    print(client)
    return
    
    request_params = StockBarsRequest(
      symbol_or_symbols=symbol,
      timeframe=timeframe,
      start=start,
      end=end,
    )

    df = client.get_stock_bars(request_params).df
    df = df.droplevel(0)  # Remove symbol level
    df.index = df.index.tz_convert('Europe/Stockholm')
    
    return df
