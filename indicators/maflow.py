import backtrader as bt


class MAFlow(bt.Indicator):
    lines = ('ma5', 'ma8', 'ma13', 'ma21', 'ma34',
             'ma55', 'ma89', 'ma144')

    def __init__(self):
        self.addminperiod(145)

    def next(self):
        self.lines.ma5 = bt.indicators.EMA(period=5)
        self.lines.ma8 = bt.indicators.EMA(period=8)
        self.lines.ma13 = bt.indicators.EMA(period=13)
        self.lines.ma21 = bt.indicators.EMA(period=21)
        self.lines.ma34 = bt.indicators.EMA(period=34)
        self.lines.ma55 = bt.indicators.EMA(period=55)
        self.lines.ma89 = bt.indicators.EMA(period=89)
        self.lines.ma144 = bt.indicators.EMA(period=144)
