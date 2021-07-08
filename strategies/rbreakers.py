import backtrader as bt
import backtrader.indicators as btind
from datetime import time ,datetime, date
from indicators.rbreaker import RBreakersIndicator

class RBreakers(bt.Strategy):
    params = (
        ('lose_stop', 1), 
        ('win_stop', 1.2)
    )
    def __init__(self):
        self.rbreaker = RBreakersIndicator()
        self.rbreaker.plotinfo.plotmaster  = self.data

        self.long_signal = btind.CrossUp(self.data.close, self.rbreaker.lines.Bbreak, plot=False)
        self.short_signal = btind.CrossDown(self.data.close,self.rbreaker.lines.Sbreak, plot=False)
        self.atr = btind.ATR(self.data)
        
        self.buy_price = None
        self.sell_price = None

    def next(self):
        if self._do_day_close():
            return


        if self.buy_price is not None and self.buy_price > self.data1.close[0] + self.p.lose_stop * self.atr[0]:
            if self.position.size > 0 and self.data1.datetime.datetime(0).day == self.data.datetime.datetime(0).day:
                self.close()
                return
        if self.sell_price is not None and self.sell_price < self.data1.close[0] - self.p.lose_stop * self.atr[0]:
            if self.position.size < 0  and self.data1.datetime.datetime(0).day == self.data.datetime.datetime(0).day:
                self.close()
                return

        if self.buy_price is not None and self.buy_price < self.data1.close[0] - self.p.win_stop * self.atr[0]:
            if self.position.size > 0 and self.data1.datetime.datetime(0).day == self.data.datetime.datetime(0).day:
                self.close()
                return
        if self.sell_price is not None and self.sell_price > self.data1.close[0] + self.p.win_stop * self.atr[0]:
            if self.position.size < 0  and self.data1.datetime.datetime(0).day == self.data.datetime.datetime(0).day:
                self.close()
                return

        if self.long_signal[0] and self.position.size == 0:
               self.buy(size=24)
        elif self.short_signal[0] and self.position.size ==0:
                self.sell(size=24)


    def notify_trade(self, trade):
        if trade.isclosed:
            print('(open:%s,close:%s)毛收益 %0.2f, 扣佣后收益 % 0.2f, 佣金 %.2f' %
                     (bt.num2date(trade.dtopen),bt.num2date(trade.dtclose),trade.pnl, trade.pnlcomm, trade.commission))

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:
            if order.isbuy():
                self.buy_price = order.executed.price
            elif order.issell():
                self.sell_price = order.executed.price

    def _do_day_close(self):
        if self.data.datetime.datetime(0).time() == time(14,59):
            self.close()
            self.buy_price = None
            self.sell_price = None
            return True
        if self.data.datetime.datetime(0).time() == time(15,0):
            return True
        
        return False

class InDay():

    def __init__(self, data, on_day_start):
        self.data = data
        self.on_day_start = on_day_start