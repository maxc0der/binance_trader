import pandas as pd
from binance.client import Client
from binance.um_futures import UMFutures
from depth__class import DepthClass


try:
    client = Client('lECjMwD4en6x7vn6UHnjWqnMVcgMpUHdcXIIyaCY3tW7fIQPHLBjLi8zOjDJgDa9',
                    'cHN92hfrm3JfTiU22Xz4e2Vp4tT0uLAZcNXEy0z7akVozWLJEyraUbTXStFGbbv1')
    futures_client = UMFutures('lECjMwD4en6x7vn6UHnjWqnMVcgMpUHdcXIIyaCY3tW7fIQPHLBjLi8zOjDJgDa9',
                        'cHN92hfrm3JfTiU22Xz4e2Vp4tT0uLAZcNXEy0z7akVozWLJEyraUbTXStFGbbv1')
except Exception as e:
    print(e)


def get_tickers():
    tickers = set()
    data = client.get_all_tickers()
    for x in data:
        if 'USDT' == x['symbol'][-4:]:
            tickers.add(x['symbol'])
    return tickers


def get_depth_data(ticker, limit=100):
    try:
        source_data = client.get_order_book(symbol=ticker, limit=limit)
        return DepthClass(source_data)
    except Exception as e:
        print('Error in get_depth_data: ', str(e))
        return False


def get_recent_trades(ticker, limit=300):
    data = client.get_recent_trades(symbol=ticker, limit=limit)
    bounds = [float(min(data, key=lambda x: float(x['price']))['price']), float(max(data, key=lambda x: float(x['price']))['price'])]
    last_price = data[-1]['price']
    response = {'data': data, 'bounds': bounds, 'last_price': last_price}
    return response


def get_candles(ticker, interval=Client.KLINE_INTERVAL_1MINUTE, limit=100):
    return client.get_historical_klines(ticker, interval, limit=limit)


def get_futures_price(ticker):
    return float(futures_client.historical_trades(symbol=ticker, limit=1)[0]['price'])


def get_candles_df(ticker, interval=Client.KLINE_INTERVAL_5MINUTE, from_time="6 hour ago UTC"):
    candles = client.get_historical_klines(ticker, interval, from_time)
    data = pd.DataFrame(candles)
    col_names = ['Open Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close Time', 'Quote Asset Volume', 'Num Trades',
                 'Taker buy base asset vol', 'Taker buy quote asset vol', 'Ignore']
    data.columns = col_names
    data['Open Time'] = pd.to_datetime(data['Open Time']/1000 + 3*3600, unit='s')
    data['Close Time'] = pd.to_datetime(data['Close Time']/1000 + 3*3600, unit='s')
    numeric_cols = ['Open', 'High', 'Low', 'Close', 'Volume', 'Quote Asset Volume', 'Num Trades',
                    'Taker buy base asset vol', 'Taker buy quote asset vol']
    data[numeric_cols] = data[numeric_cols].apply(pd.to_numeric, axis=1)
    return data


