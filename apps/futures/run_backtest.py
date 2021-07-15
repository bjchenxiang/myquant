import os
import backtrader as bt
import numpy as np
import pandas as pd
from datetime import datetime
from loguru import logger
from strategies.rbreakers import RBreakers
from backtrader_plotting import Bokeh
from backtrader_plotting.schemes import Tradimo,Blackly

import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.colors import LinearSegmentedColormap
import numpy as np

from utils.object import  FixPeriodCSVData
from utils.analyzer import show_analyzer


stockindex_settings = {
    'coin':'IC',
    'data1':os.path.join(os.path.dirname(__file__),
                       'data/CFFEX.IC00_60s_.csv' ),
    'start':datetime(2020,1,1),
    'end':datetime(2020,1, 31),
    'has_night_trade':False,
    'start_cash':200000,
    'commission':0.00001        
}

goods_settings = {
    'coin':'AL',
    'data1':os.path.join(os.path.dirname(__file__),
                       'data/SHFE.AL_60s_.csv' ),
    'start':datetime(2020,1,1),
    'end':datetime(2020,1, 31),
    'has_night_trade':True,
    'start_cash':200000,
    'commission':0.00001        
}

settings = goods_settings

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
    cerebro.broker.setcommission(
        commission=settings['commission'], 
        margin=0.1,
        mult=200
    )

    cerebro.addstrategy(RBreakers, 
        lose_stop=3, 
        win_stop=15,
        has_night_trade=settings['has_night_trade'], 
        print_log=True
    )

    cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')   

    result = cerebro.run()    
    
    show_analyzer(result[0], name='pyfolio')
    show_plot(cerebro)

def show_plot(cerebro):
    try:
        # b = Bokeh(style='bar', tabs='multi', scheme=Tradimo(),toolbar_location='left')  # 传统白底，多页
        cerebro.plot()
    except:
        pass

def opt_params():
    cerebro = bt.Cerebro(cheat_on_open=True)
    lose_stop = np.arange(0.1,2,0.1)
    win_stop = np.arange(0.1,2,0.1)
    cerebro.optstrategy(
        RBreakers, 
        lose_stop=lose_stop, 
        win_stop=win_stop,
        has_night_trade=settings['has_night_trade']
    )
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
    # //cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name = "sharpe")
    # // cerebro.addanalyzer(bt.analyzers.DrawDown, _name = "drawdown")
    # // cerebro.addanalyzer(bt.analyzers.Returns, _name = "returns")
    
    cerebro.broker.setcash(settings['start_cash'])
    # ?注意期货佣金的设置
    cerebro.broker.setcommission(commission=settings['commission'], margin=0.1,mult=200)
    result = cerebro.run()

    
    par_list = [[x[0].params.lose_stop, 
                x[0].params.win_stop,
                x[0].analyzers.returns.get_analysis()['rtot'],
                x[0].analyzers.drawdown.get_analysis()['max']['drawdown']
                # x[0].analyzers.sharpe.get_analysis()['sharperatio']
                ] for x in result]

    # ?结果转成dataframe
    par_df = pd.DataFrame(par_list, columns = ['lose_stop', 'win_stop','return','dd'])

    print(par_df)
    par_df.to_csv('result.csv')

    x = par_df['lose_stop'].tolist()
    y = par_df['win_stop'].tolist()   
    z = par_df['return'].tolist()

    norm=plt.Normalize(-1,1)
    cmap =LinearSegmentedColormap.from_list("", ["red","violet","blue"])

    plt.scatter(x,y,c=z, cmap=cmap, norm=norm)
    plt.colorbar()
    plt.show()



if __name__ == '__main__':
    run_testback()
    # opt_params()
