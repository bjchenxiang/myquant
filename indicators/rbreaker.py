import backtrader as bt 
import backtrader.indicators as btind

class RBreakersIndicator(bt.Indicator):
    # params = (
    #     ('a', 2),
    #     ('b', 2),
    #     ('c', 2),
    #     ('d', 2),
    # )
    lines = ('Bbreak','Ssetup','Senter','Benter','Bsetup','Sbreak')
    plotlines = dict(
        Bbreak=dict(_name='Bbreak', color='red'),
        Ssetup=dict(_name='Ssetup', color='blue'),
        Senter=dict(_samecolor=True,_name='Senter'),
        Benter=dict(_samecolor=True,_name='Benter'),
        Bsetup=dict(_name='Bsetup',color='blue'),
        Sbreak=dict(_name='Sbreak', color='red'),
    )

    def __init__(self):
        self.addminperiod(241)

    def next(self):
        f1 = 0.03
        f2 = 0.07
        f3 = 0.87
        high = self.data.pre_day_high[0]
        low = self.data.pre_day_low[0]
        close = self.data.pre_day_close[0]
        pivot = (high + low + close) / 3
        if high == low == 0.0:
            return 
        # self.lines.Ssetup[0] = pivot + (high - low)
        # self.lines.Bsetup[0] = pivot - (high - low) 
        # self.lines.Senter[0] = 2 * pivot - low 
        # self.lines.Benter[0] = 2 * pivot - high 
        # self.lines.Sbreak[0] = low - 2 * (high - pivot) 
        # self.lines.Bbreak[0] = high + 2 * (pivot - low) 
        self.lines.Ssetup[0] = high + f1 *(close - low)
        self.lines.Bsetup[0] = low - f1 * (high - close)
        self.lines.Senter[0] = (1 + f2) / 2 * (high + low) - f2 * low
        self.lines.Benter[0] = (1 + f2) / 2 * (high + low) - f2 * high
        self.lines.Sbreak[0] = self.lines.Bsetup[0] - f3 * (self.lines.Ssetup[0] - self.lines.Bsetup[0])
        self.lines.Bbreak[0] = self.lines.Ssetup[0] + f3 * (self.lines.Ssetup[0] - self.lines.Bsetup[0])