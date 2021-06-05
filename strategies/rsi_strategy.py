import backtrader as bt
from myquant.base_strategy import BaseStrategy


class RSIStrategy(BaseStrategy):
    params = dict(
        period_ema_fast=10,
        period_ema_slow=100
    )

    def __init__(self):
        BaseStrategy.__init__(self)
        self.log("Using RSI/EMA strategy")

        self.ema_fast = bt.indicators.EMA(period=self.p.period_ema_fast)
        self.ema_slow = bt.indicators.EMA(period=self.p.period_ema_slow)
        self.rsi = bt.indicators.RelativeStrengthIndex()

        self.profit = 0

    def update_indicators(self):
        self.profit = 0
        if self.buy_price_close and self.buy_price_close > 0:
            self.profit = float(
                self.data0.close[0] - self.buy_price_close) / self.buy_price_close

    def next(self):
        self.update_indicators()

        # if self.status != "LIVE" and ENV == PRODUCTION:  # waiting for live status in production
        #     return

        # if self.order:  # waiting for pending order
        #     return

        # 止损
        # if self.profit < -0.03:
        #     self.log("STOP LOSS: percentage %.3f %%" % self.profit)
        #     self.sell()

        if self.rsi < 30 and self.ema_fast > self.ema_slow:
            self.buy()

        if self.rsi > 70:
            self.sell()
