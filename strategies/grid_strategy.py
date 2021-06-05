import backtrader as bt
from backtrader import indicator
import numpy as np
from myquant.indicators.grid import GridIndicator, GridPositionIndicator


class GridStrategy(bt.Strategy):
    params = (
        ('grid_size', 10),
    )

    def __init__(self):
        # self.grid = GridIndicator(period=144)
        self.grid = GridIndicator(period=144)
        self.grid.plotinfo.plotmaster = self.data
        self.gridposition = GridPositionIndicator(
            period=144, grid_size=self.params.grid_size)

    def next(self):
        if np.isnan(self.gridposition.position[-1]) or self.gridposition.position[0] != self.gridposition.position[-1]:
            self.order_target_percent(
                data=None, target=self.gridposition.position[0])
