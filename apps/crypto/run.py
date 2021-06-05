import sys
import os
import backtrader as bt
from datetime import datetime
from utils.helper import read_setting,import_class
from utils.constant import BROKER_MAPPING
from ccxtbt import CCXTStore


def start_live(config):
    store = CCXTStore(exchange=config['exchange'], currency=config['coin_refer'],
                      config=config['broker'], retries=5, debug=False)
    broker = store.getbroker(broker_mapping=BROKER_MAPPING)

    cerebro = bt.Cerebro()
    cerebro.setbroker(broker)

    # 设置数据
    hist_start_date = datetime.utcnow()
    data = store.getdata(
        dataname='%s/%s' % (config['coin_target'], config['coin_refer']),
        name='%s%s' % (config['coin_target'], config['coin_refer']),
        timeframe=bt.TimeFrame.Ticks,
        compression=1
    )
    cerebro.adddata(data)

    # 设置策略
    strategy = import_class(config['strategy']['module'],config['strategy']['class'])
    params = config['strategy']['params']
    cerebro.addstrategy(strategy,**params)

    return cerebro

def get_curfile_fullname(name):
    return  os.path.join(os.path.dirname( os.path.abspath(__file__)) ,name)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('请带配置文件运行本程序: python run.py setting_biance_BTCUSDT.json')
    else:
        setting = read_setting(get_curfile_fullname(sys.argv[1]))
        cerebro = start_live(setting)
        result = cerebro.run()