import backtrader as bt
import backtrader.feeds as btfeed

class CustomDataset(bt.feeds.GenericCSVData):
    params = (
        ('datetime', 0),
        ('open', 1),
        ('high', 2),
        ('low', 3),
        ('close', 4),
        ('volume', 5)
    )


class FullMoney(bt.sizers.PercentSizer):
    params = (
        ('percents', 99),
    )

class FixPeriodCSVData(btfeed.GenericCSVData):
    lines = ('pre_day_open','pre_day_high','pre_day_low','pre_day_close')
    params = (
        ('pre_day_open',8),
        ('pre_day_high',9),
        ('pre_day_low',10),
        ('pre_day_close',11)
    )
