import backtrader as bt
from datetime import datetime, timezone, timedelta


class EchoStrategy(bt.Strategy):

    def __init__(self):
        self.status = "DISCONNECTED"
        print("Using Echo strategy")
        self.profit = 0
        self.localzone = timezone(timedelta(hours=8))

    def notify_data(self, data, status, *args, **kwargs):
        self.status = data._getstatusname(status)
        print('='*66)

    def next(self):
        dt = self.data.datetime.datetime(0).astimezone(self.localzone)
        print('\r%s:%s' %
              (dt.strftime('%Y-%m-%d %H:%M:%S'), self.data.close[0]), end='')
        # print('\r'+self.status, end='')
