import backtrader as bt


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
