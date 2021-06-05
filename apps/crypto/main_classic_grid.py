import os
import backtrader as bt
import backtrader.feeds as btfeed
from loguru import logger
from time import time
from datetime import datetime, timedelta
from ccxtbt import CCXTStore
from backtrader_plotting import Bokeh
from backtrader_plotting.schemes import Tradimo,Blackly
from myquant.strategies.classic_grid_strategy import ClassicGridStrategy
from myquant.strategies.grid_strategy import GridStrategy
from myquant.utils.constant import BROKER_MAPPING


settings = {
    'coin':'BTC',
    'data':os.path.join(os.path.dirname(__file__),
                          "dataset/binance_btcusdt_1m.3.csv"),
    'start': datetime(2021, 5, 22),
    'end':  datetime(2021, 6, 1),
    'start_cash':100000,
    'commission':0.0002,
    'strategy':{
        'params':{
            'bottom':30000,
            'top':40000,
            'count':100,
            'live_records' : 'live.csv',
            'cash':2249,
            'position':0.027
        }
    }
}


def backtest():
    cerebro = bt.Cerebro()
    data = btfeed.GenericCSVData(
        name=settings['coin'],
        dataname=settings['data'],
        fromdate=settings['start'],
        todate=settings['end'],
        nullvalue = 0.0,
        timeframe=bt.TimeFrame.Minutes

    )
    cerebro.adddata(data)
    cerebro.broker.setcash(settings['start_cash'])
    cerebro.broker.setcommission(commission=settings['commission'])

    params=settings['strategy']['params']
    cerebro.addstrategy(ClassicGridStrategy,bottom=params['bottom'],top=params['top'],count=params['count'])
    
    initial_value = cerebro.broker.getvalue()
    logger.info('起始资产: %.2f' % initial_value)
    result = cerebro.run()
    final_value = cerebro.broker.getvalue()
    logger.info('最新资产: %.2f' % final_value)
    logger.info('现金：%.2f' % cerebro.broker.cash)
    logger.info('利润 %.3f%%' %
                ((final_value - initial_value) / initial_value * 100))


    b = Bokeh(style='bar', tabs='multi', scheme=Tradimo(),toolbar_location='left')  # 传统白底，多页
    # b = Bokeh(style='bar') #黑底 单页
    # b = Bokeh(style='bar', scheme=Tradimo()) #白底，单页
    # b = Bokeh(style='bar', tabs='multi', scheme=Tradimo()) #白底，多页

    cerebro.plot(b)
    # cerebro.plot()


def set_live_broker():
    """
    通过CCXTStore创建数字货币的实盘接口
    """
    EXCHANGE = 'binance'
    COIN_TARGET = "BTC"
    COIN_REFER = "USDT"
    APIKEY = 'x2f7KEqKQTe6VyoW8JqTa666KcdvR6l5WlsBldC4Mn2MVvbHKN3RKUlaELSdeOva'
    SECRET = 'KjoMLIlCDxmAGSSPdQhCfZ9fOhPvnbN3s7xXIfNToH3yD9UarCOlLZEgbC2fBolA'
    

    broker_config = {
        'apiKey': APIKEY,
        'secret': SECRET,
        'nonce': lambda: str(int(time()*1000)),
        'enabledRateLimit': True,
        'proxies': {
            'http': 'http://127.0.0.1:1081',
            'https': 'http://127.0.0.1:1081',
        },
    }
    store = CCXTStore(exchange=EXCHANGE, currency='USDT',
                      config=broker_config, retries=5, debug=False)
    broker = store.getbroker(broker_mapping=BROKER_MAPPING)
    cerebro = bt.Cerebro()
    cerebro.setbroker(broker)

    # 设置数据
    hist_start_date = datetime.utcnow()
    data = store.getdata(
        dataname='%s/%s' % (COIN_TARGET, COIN_REFER),
        name='%s%s' % (COIN_TARGET, COIN_REFER),
        timeframe=bt.TimeFrame.Ticks,
        compression=1
    )
    cerebro.adddata(data)

    return cerebro

def run_live():
    cerebro = set_live_broker()
    params=settings['strategy']['params']
    cerebro.addstrategy(ClassicGridStrategy,bottom=params['bottom'],top=params['top'],count=params['count'],
        live_records=params['live_records'],
        cash = params['cash'],
        position = params['position'])
    initial_value = cerebro.broker.getvalue()
    logger.info('起始资产: %.2f' % initial_value)
    result = cerebro.run()
    final_value = cerebro.broker.getvalue()
    logger.info('最新资产: %.2f' % final_value)
    logger.info('现金：%.2f' % cerebro.broker.cash)
    logger.info('利润 %.3f%%' %
                ((final_value - initial_value) / initial_value * 100))

if __name__ == '__main__':
    print('如需使用回测，请使用backtest()函数')
    # backtest()
    run_live()


