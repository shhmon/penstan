from datetime import datetime, timedelta
from eodhd import APIClient

def fetch_data_alpaca(
    symbol: str,
    start: datetime,
    interval = '1h',
    end = None,
):
    end = end if end else datetime.now()

    api = APIClient('68dc63ea6bf400.23436974')
    
    resp = api.get_intraday_historical_data(
        symbol=symbol,
        interval=interval,
        from_unix_time=start.timestamp(),
        to_unix_time=end.timestamp(),
    )

    return resp
