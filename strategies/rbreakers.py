import backtrader as bt
import backtrader.indicators as btind
from datetime import time ,datetime, date
from indicators.rbreaker import RBreakersIndicator
from loguru import logger

class RBreakers(bt.Strategy):
    params = (
        ('lose_close', 0.005), #止损参数，参数即上一周期收盘价的倍数，运行中使用lose_close和lose_stop中的最小值作为止损条件
        ('lose_stop', 0.3),  #止损参数，参数即当前atr的倍数
        ('win_stop', 2), #止赢参数，参数即当前atr的倍数
        ('has_night_trade', False),
        ('print_log',False)
    )

    def __init__(self):
        self.rbreaker = RBreakersIndicator()
        self.rbreaker.plotinfo.plotmaster  = self.data

        self.long_signal = btind.CrossUp(self.data.close, self.rbreaker.lines.Bbreak, plot=False)
        self.short_signal = btind.CrossDown(self.data.close,self.rbreaker.lines.Sbreak, plot=False)
        self.atr = btind.ATR(self.data)
        
        self.buy_price = None
        self.sell_price = None
    
    def start(self):
        logger.info('启动参数：lose_stop=%.2f, win_stop=%.2f' % (self.p.lose_stop,self.p.win_stop))

    def next(self):
        if self._do_day_close():
            return

        if self.long_signal[0] and self.position.size == 0:
            self.buy_bracket(
                price=self.data0.close, 
                limitprice=self.data0.close + self.p.win_stop*self.atr[0],
                stopprice=self.data0.close - min(self.p.lose_stop*self.atr[0],self.data0.close[-1]*self.p.lose_close)
            )
        elif self.short_signal[0] and self.position.size ==0:
            self.sell_bracket(
                price=self.data0.close, 
                limitprice=self.data0.close - self.p.win_stop*self.atr[0],
                stopprice=self.data0.close + min(self.p.lose_stop*self.atr[0],self.data0.close[-1]*self.p.lose_close)
            )
            
    def notify_trade(self, trade):        
        if self.params.print_log and trade.isclosed:
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
        is_day_last_bar = (self.data.datetime.datetime(0).time() == time(14,59)) if not self.p.has_night_trade else (self.data.datetime.datetime(0).time() == time(18,59))        
        if is_day_last_bar:
            self.close()
            self.buy_price = None
            self.sell_price = None
            return True
        is_day_last_bar = (self.data.datetime.datetime(0).time() == time(14,59)) if not self.p.has_night_trade else (self.data.datetime.datetime(0).time() == time(19,0))
        if is_day_last_bar:
            return True
        
        return False

class InDay():

    def __init__(self, data, on_day_start):
        self.data = data
        self.on_day_start = on_day_start