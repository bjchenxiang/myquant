import backtrader as bt
import os
import pandas as pd
from ccxtbt import CCXTStore
from time import time
import time
from loguru import logger
from backtrader_plotting import Bokeh
from backtrader_plotting.schemes import Tradimo
from datetime import datetime, timedelta
from myquant.utils.message import send_dingding_message, print_sqn, print_trade_analysis
from myquant.utils.constant import BROKER_MAPPING
from myquant.utils.object import CustomDataset, FullMoney
# from myquant.strategies.echo_strategy import EchoStrategy
# from myquant.strategies.rsi_strategy import RSIStrategy
from myquant.strategies.grid_strategy import GridStrategy
from myquant.strategies.maflow import MAFlowStrategy
# from myquant.strategies.boll_strategy import BollStrategy
# from myquant.strategies.turtle_strategy import TurtleStrategy, TradeSizer
from setting import *


def set_live_broker(cerebro):
    """
    通过CCXTStore创建数字货币的实盘接口
    """
    broker_config = {
        'apiKey': APIKEY,
        'secret': SECRET,
        'nonce': lambda: str(int(time()*1000)),
        'enabledRateLimit': True
    }
    store = CCXTStore(exchange=EXCHANGE, currency='USDT',
                      config=broker_config, retries=5, debug=DEBUG)
    broker = store.getbroker(broker_mapping=BROKER_MAPPING)
    cerebro.setbroker(broker)

    # 设置数据
    hist_start_date = datetime.utcnow() - timedelta(minutes=30000)
    data = store.getdata(
        dataname='%s/%s' % (COIN_TARGET, COIN_REFER),
        name='%s%s' % (COIN_TARGET, COIN_REFER),
        timeframe=bt.TimeFrame.Minutes,
        fromdate=hist_start_date,
        compression=30,
        ohlcv_limit=99999
    )
    cerebro.adddata(data)


def set_backtest_data(cerebro):
    data = CustomDataset(
        name=COIN_TARGET,
        dataname=os.path.join(os.path.dirname(__file__),
                              "dataset/binance_btcusdt_1m.1.csv"),
        timeframe=bt.TimeFrame.Minutes,
        fromdate=datetime(2017, 8, 17),
        todate=datetime(2017, 10, 31),
        # todate=datetime(2018, 3, 18),
        # todate=datetime(2020, 7, 7),
        # todate=datetime(2021, 4, 27),
        nullvalue=0.0
    )
    cerebro.resampledata(data, timeframe=bt.TimeFrame.Minutes, compression=1)
    # cerebro.resampledata(
    #     data, timeframe=bt.TimeFrame.Minutes, compression=60*6)

    broker = cerebro.getbroker()
    # Simulating exchange fee
    broker.setcommission(commission=0.008, name=COIN_TARGET)
    broker.setcash(100000.0)
    cerebro.broker.set_coc(True)  # 设置以当日收盘价成交
    # cerebro.addsizer(TradeSizer)
    # broker.setsize(10)
    # cerebro.addsizer(FullMoney)


def get_order_list(cerebro, init_cash):
    orders = []
    for order in cerebro.broker.orders:
        if order.executed.size == 0:
            continue
        orders.append({
            "datetime": bt.num2date(order.executed.dt),
            "size": order.executed.size,
            "price": order.executed.price,
            "cost": order.executed.value,
            "comm": order.executed.comm
        })
    if orders == []:
        return
    df = pd.DataFrame(orders)
    df['cost'] = df['size'] * df['price']+df['comm']
    df['all_cost'] = df['cost'].cumsum()
    df['cash'] = init_cash - df['all_cost']
    df['btc'] = df['size'].cumsum()
    df['策略净值'] = df['cash'] + df['btc'] * df['price']
    df['原净值'] = init_cash * df['price'] / df.loc[0, 'price']
    df.loc[0, '原净值'] = init_cash

    df = df[['datetime', '原净值', '策略净值', 'cash', 'btc', 'price', 'size', 'comm']]
    df.rename(columns={
        'datetime': '时间',
        'cash': '可用资金',
        'btc': '比特币数量',
        'price': '交易价格',
        'size': '交易数量',
        'comm': '手续费'
    }, inplace=True)

    df.to_csv('orders.csv')


def main():

    # 创建bt引擎
    cerebro = bt.Cerebro(quicknotify=True)

    if ENV == LIVE:
        # 通过CCXTS tore设置交易所
        logger.info('实盘模式')
        set_live_broker(cerebro)
    else:
        logger.info('回测模式')
        set_backtest_data(cerebro)
    # 设置分析系统
    # cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="ta")
    # cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")

    # 设置运行策略
    setting_path = os.path.join(os.path.dirname(
        __file__), 'btcusd_grid_settings.json')
    # cerebro.addstrategy(GridStrategy, setting_path)
    cerebro.addstrategy(GridStrategy, grid_size=13)

    # 运行策略

    initial_value = cerebro.broker.getvalue()
    logger.info('起始资产: %.2f' % initial_value)
    result = cerebro.run()
    final_value = cerebro.broker.getvalue()
    logger.info('最新资产: %.2f' % final_value)
    logger.info('现金：%.2f' % cerebro.broker.cash)
    logger.info('利润 %.3f%%' %
                ((final_value - initial_value) / initial_value * 100))

    # 分析策略
    # print_trade_analysis(result[0].analyzers.ta.get_analysis())
    # print_sqn(result[0].analyzers.sqn.get_analysis())
    if ENV == BACKTEST:
        get_order_list(cerebro, 100000)
        # cerebro.plot(numfigs=1)
        b = Bokeh(style='bar', plot_mode='single',
                  scheme=Tradimo())  # 传统白底，多页
        cerebro.plot(b)


if __name__ == '__main__':
    # try:
    main()
    # except KeyboardInterrupt:
    #     logger.info("策略正常结束")
    #     time = datetime.now().strftime("%d-%m-%y %H:%M")
    #     send_dingding_message("%s: 用户中止策略" % time)
    # except Exception as err:
    #     send_dingding_message("错误: %s" % err)
    #     logger.error("错误: ", err)
    #     raise
