from pylab import mpl
import pandas as pd
from datetime import datetime
import backtrader as bt
import backtrader.feeds as btfeed
import matplotlib.pyplot as plt
from myquant.strategies.grid_strategy import GridStrategy
from setting import *
import os

# 正常显示画图时出现的中文和负号
mpl.rcParams['font.sans-serif'] = ['SimHei']
mpl.rcParams['axes.unicode_minus'] = False


if __name__ == '__main__':
    cerebro = bt.Cerebro()
    # 回测期间
    start = datetime(2010, 3, 31)
    end = datetime(2020, 3, 31)
    # 加载数据
    data = btfeed.GenericCSVData(
        name=COIN_TARGET,
        dataname=os.path.join(os.path.dirname(__file__),
                              "dataset/binance_btcusdt_1h.csv"),
        # timeframe=bt.TimeFrame.Minutes,
        fromdate=datetime(2020, 9, 19),
        todate=datetime(2021, 9, 21),
        nullvalue=0.0
    )
    # 将数据传入回测系统
    cerebro.adddata(data)
    # 将交易策略加载到回测系统中
    cerebro.addstrategy(GridStrategy)
    # 设置初始资本为10,000
    startcash = 10000
    cerebro.broker.setcash(startcash)
    # 设置交易手续费为 0.2%
    cerebro.broker.setcommission(commission=0.002)
    # 股票交易的手续费一般由交易佣金、印花税、过户费3部分组成，其中佣金不同证券公司的收费不同，一般在买卖金额的0.1%-0.3%之间，最低收费为5元
