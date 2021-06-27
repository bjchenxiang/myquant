from __future__ import print_function, absolute_import
from gm.api import *
import os


set_token('545324c4b51478b92232ef80e4775797976f8e52')
symbol = 'CFFEX.IC00'
fre = '60s'
data = history(symbol=symbol, frequency=fre, start_time='2020-01-01 09:00:00', end_time='2020-12-31 16:00:00',
                adjust=ADJUST_NONE,  df=True)
path = os.path.join(os.path.dirname(__file__), symbol+'_'+fre+'.csv')
data.to_csv(path,index=None)