import backtrader as bt


class MAFlowStrategy(bt.Strategy):

    def __init__(self):
        self.ma5 = bt.indicators.EMA(period=12)
        self.ma8 = bt.indicators.EMA(period=144)
        self.ma13 = bt.indicators.EMA(period=169)
        self.ma21 = bt.indicators.EMA(period=576)
        self.ma34 = bt.indicators.EMA(period=676)

        self.ma5.plotinfo.plotmaster = self.data
        self.ma8.plotinfo.plotmaster = self.data
        self.ma13.plotinfo.plotmaster = self.data
        self.ma21.plotinfo.plotmaster = self.data
        self.ma34.plotinfo.plotmaster = self.data

        self.ma5.plotlines = dict(
            ema=dict(color='yellow')
        )
        self.ma8.plotlines = dict(
            ema=dict(color='red')
        )
        self.ma13.plotlines = dict(
            ema=dict(color='red')
        )
        self.ma21.plotlines = dict(
            ema=dict(color='blue')
        )
        self.ma34.plotlines = dict(
            ema=dict(color='blue')
        )

    def next(self):
        pass
