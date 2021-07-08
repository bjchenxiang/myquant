from __future__ import print_function, absolute_import
from gm.api import *
import os
import pandas as pd


set_token('545324c4b51478b92232ef80e4775797976f8e52')


def dl(symbol, fre):
    data = history(symbol=symbol, frequency=fre, start_time='2020-01-01 09:00:00', end_time='2020-12-31 16:00:00',
                adjust=ADJUST_NONE,  df=True)
    path = os.path.join(os.path.dirname(__file__), symbol+'_'+fre+'.csv')
    data.to_csv(path,index=None)

def combine(csv1, csv2):
    df1 = pd.read_csv(csv1)
    df1['date'] =pd.to_datetime(df1['bob']).dt.to_period('D')
    df1['pre_open'] = df1['open'].shift()
    df1['pre_high'] = df1['high'].shift()
    df1['pre_low'] = df1['low'].shift()
    df1['pre_close'] = df1['close'].shift()

    df2 = pd.read_csv(csv2)
    df2['date'] = pd.to_datetime(df2['bob']).dt.to_period('D')
    df3 = pd.merge(df2, df1, on='date')
    df3.rename(columns={
        'symbol_x':'symbol',
        'eob_x': 'datetime',
        'open_x': 'open',
        'high_x': 'high',
        'low_x' : 'low',
        'close_x': 'close',
        'volume_x': 'volume',
        'position_x': 'openinterest',
        'pre_open': 'pre_day_open',
        'pre_close_y': 'pre_day_close',
        'pre_high': 'pre_day_high',
        'pre_low': 'pre_day_low'
        },inplace=True)
    df3['datetime'] = pd.to_datetime(df3['datetime'])
    df3 = df3[['datetime','open','high','low','close','volume','openinterest','pre_day_open','pre_day_high','pre_day_low','pre_day_close','symbol']]
    csv_path = csv2.replace('.csv','_.csv')
    df3.to_csv(csv_path)
    



if __name__ == '__main__':
    # symbol = 'CFFEX.IC00'
    # fre = '1d'
    # dl(symbol, fre)

    base_dir = os.path.dirname(__file__)
    csv1 = os.path.join(base_dir, 'CFFEX.IC00_1d.csv')
    csv2 = os.path.join(base_dir, 'CFFEX.IC00_60s.csv')
    combine(csv1, csv2)