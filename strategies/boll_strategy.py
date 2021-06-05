import backtrader as bt
import numpy as np
from enum import Enum
from myquant.base_strategy import BaseStrategy


class BollStrategy(BaseStrategy):
    params = (

    )

    def __init__(self):
        self.order = None
        self.boll0 = bt.indicators.BollingerBands(
            self.datas[0].close)
        self.boll = bt.indicators.BollingerBands(
            self.datas[1].close)

    def next(self):
        if self.data.close[-1] < self.boll.lines.bot[-1] and self.data.close > self.boll.lines.bot:
            size = self.broker.cash / self.data.close
            self.order = self.buy(size=size)
        elif self.data.close[-1] > self.boll.lines.top[-1] and self.data.close < self.boll.lines.top:
            size = self.position.size
            self.order = self.sell(size=size)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
