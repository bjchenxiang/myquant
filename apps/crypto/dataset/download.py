import ccxt
import time
import pandas as pd
import os
from datetime import datetime,timedelta


def ccxt_download(exchange_name, symbol, timeframe='1m', limit=3000):
    exchange = getattr(ccxt, exchange_name)()  # ccxt.binance()
    current_time = int(time.time()//60 * 60 * 1000)  # 毫秒
    # 获取请求开始的时间
    since_time = current_time - limit * 60 * 1000

    num = limit // 1000
    all_data = pd.DataFrame()
    for i in range(num):
        # 'BTC/USD' 比特币对美元的交易对，或者ETH/USD 以太坊对美元的交易对.
        data = exchange.fetch_ohlcv(
            symbol=symbol, timeframe=timeframe, limit=1000, since=since_time)
        df = pd.DataFrame(data)
        df = df.rename(columns={0: 'datetime', 1: 'open',
                                2: 'high', 3: 'low', 4: 'close', 5: 'volume'})
        # 时间转换成北京时间
        if not df.empty:
            df['datetime'] = df['datetime'] // 1000 * 1000
            df['datetime'] = pd.to_datetime(
                df['datetime'], unit='ms') + pd.Timedelta(hours=8)

            dt = [str(i.date()) +' ' + str(i.hour) + ':' + str(i.minute) + ':00' for i in df['datetime'].to_list()]
            df['datetime'] = pd.Series(dt)
            df['datetime'] = pd.to_datetime(df['datetime'], format='%Y-%m-%d %H:%M:%S')
            # 设置index
            df = df.set_index('datetime', drop=True)
            all_data = all_data.append(df)
        since_time += 1000 * 60 * 1000
        print('\r正在下载%d/%d' % (i+1, num), end='')
    limit = limit % 1000
    if limit > 0:
        data = exchange.fetch_ohlcv(
            symbol=symbol, limit=limit, timeframe=timeframe, since=since_time)
        df = pd.DataFrame(data)
        df = df.rename(columns={0: 'datetime', 1: 'open',
                                2: 'high', 3: 'low', 4: 'close', 5: 'volume'})
        # 时间转换成北京时间
        df['datetime'] = df['datetime'] // 1000 * 1000
        df['datetime'] = pd.to_datetime(
            df['datetime'], unit='ms') + pd.Timedelta(hours=8)     
        dt = [str(i.date()) +' ' + str(i.hour) + ':' + str(i.minute) + ':00' for i in df['datetime'].to_list()]
        df['datetime'] = pd.Series(dt)
        df['datetime'] = pd.to_datetime(df['datetime'], format='%Y-%m-%d %H:%M:%S')   
        # 设置index
        df = df.set_index('datetime', drop=True)
        all_data = all_data.append(df)

    # 新增一个空列，backtrader的要求
    all_data['openinterest'] = 0
    # 保存成csv文件
    filepath = os.path.join(os.path.dirname(__file__), '%s_%s_%s.csv' % (
        exchange, symbol.replace('/', ''), timeframe))
    all_data.to_csv(filepath)  # comma seperate Value


if __name__ == '__main__':
    limit = 30000
    symbol = 'BTC/USDT'
    exchange_name = 'binance'
    timeframe = '1m'

    try:
        ccxt_download(exchange_name, symbol, timeframe='1m', limit=2000000)
    except:
        print('不能连接交易所！')
    # ccxt_download(exchange_name, symbol, timeframe='3m', limit=30000)
    # ccxt_download(exchange_name, symbol, timeframe='5m', limit=30000)
    # ccxt_download(exchange_name, symbol, timeframe='15m', limit=30000)
    # ccxt_download(exchange_name, symbol, timeframe='1h', limit=300000)
    # ccxt_download(exchange_name, symbol, timeframe='4h', limit=30000)
    # ccxt_download(exchange_name, symbol, timeframe='1d', limit=30000)
