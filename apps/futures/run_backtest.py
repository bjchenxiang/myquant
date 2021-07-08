import os
import backtrader as bt
import backtrader.feeds as btfeed
import numpy as np
from datetime import datetime
from loguru import logger
from strategies.rbreakers import RBreakers
from backtrader_plotting import Bokeh
from backtrader_plotting.schemes import Tradimo,Blackly

settings = {
    'coin':'IC',
    'data1':os.path.join(os.path.dirname(__file__),
                       'data/CFFEX.IC00_60s_.csv' ),
    'start':datetime(2020,1,1),
    'end':datetime(2020,12, 31),
    'start_cash':200000,
    'commission':0.00001        
}

class FixPeriodCSVData(btfeed.GenericCSVData):
    lines = ('pre_day_open','pre_day_high','pre_day_low','pre_day_close')
    params = (
        ('pre_day_open',8),
        ('pre_day_high',9),
        ('pre_day_low',10),
        ('pre_day_close',11)
    )

def run_testback():
    cerebro = bt.Cerebro(cheat_on_open=True)
    data1 = FixPeriodCSVData(
        name = settings['coin'],
        dataname = settings['data1'],
        fromdate = settings['start'],
        todate = settings['end'],
        nullvalue = 0.0, 
        timeframe=bt.TimeFrame.Minutes,
        dtformat ='%Y/%m/%d %H:%M',
        datetime=1,
        high=3,
        low=4,
        open=2,
        close=5,
        volume=6,
        openinterest=7
    )
    cerebro.adddata(data1)
    cerebro.resampledata(data1, timeframe=bt.TimeFrame.Minutes, compression=5)

    cerebro.broker.setcash(settings['start_cash'])
    # 注意期货佣金的设置
    cerebro.broker.setcommission(commission=settings['commission'], margin=2800,mult=10)

    cerebro.addstrategy(RBreakers)

    cerebro.addanalyzer(bt.analyzers.SharpeRatio,riskfreerate=0.02)
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='回测')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer)
    # cerebro.addanalyzer(bt.analyzers.PyFolio)

    initial_value = cerebro.broker.getvalue()
    logger.info('起始资产: %.2f' % initial_value)
    result = cerebro.run()
    final_value = cerebro.broker.getvalue()
    logger.info('最新资产: %.2f' % final_value)
    logger.info('现金：%.2f' % cerebro.broker.cash)
    logger.info('利润 %.3f%%' %
                ((final_value - initial_value) / initial_value * 100))

  
    b = Bokeh(style='bar', tabs='multi', scheme=Tradimo(),toolbar_location='left')  # 传统白底，多页
    cerebro.plot(b)

def opt_params():
    cerebro = bt.Cerebro(cheat_on_open=True)
    cerebro.optstrategy(RBreakers, lose_stop=np.arange(1,20,0.1), win_stop=np.arange(1,20,0.1))
    data1 = FixPeriodCSVData(
        name = settings['coin'],
        dataname = settings['data1'],
        fromdate = settings['start'],
        todate = settings['end'],
        nullvalue = 0.0, 
        timeframe=bt.TimeFrame.Minutes,
        dtformat ='%Y/%m/%d %H:%M',
        datetime=1,
        high=3,
        low=4,
        open=2,
        close=5,
        volume=6,
        openinterest=7
    )
    cerebro.adddata(data1)
    cerebro.resampledata(data1, timeframe=bt.TimeFrame.Minutes, compression=5)
    cerebro.broker.setcash(settings['start_cash'])
    # 注意期货佣金的设置
    cerebro.broker.setcommission(commission=settings['commission'], margin=2800,mult=10)
    cerebro.run()

if __name__ == '__main__':
    # run_testback()
    opt_params()