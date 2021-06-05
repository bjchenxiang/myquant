import backtrader as bt
import numpy as np


class GridIndicator(bt.Indicator):
    params = (('period', 144),)
    lines = ('top', 'bottom', 'l1', 'l2', 'l3',
             'l4', 'l5', 'l6', 'l7', 'l8', 'l9')

    plotlines = dict(
        top=dict(_samecolor=True),
        bottom=dict(_samecolor=True),
        l1=dict(ls='--', color='red'),
        l2=dict(ls='--', color='red'),
        l3=dict(ls='--', color='red'),
        l4=dict(ls='--', color='red'),
        l5=dict(ls='--', color='red'),
        l6=dict(ls='--', color='red'),
        l7=dict(ls='--', color='red'),
        l8=dict(ls='--', color='red'),
        l9=dict(ls='--', color='red'),
    )

    def __init__(self):
        self.addminperiod(self.params.period+1)

    def next(self):
        if np.isnan(self.lines.top[-1]) or self.data0.high >= self.lines.top[-1] or self.data0.low <= self.lines.bottom[-1]:
            self.lines.top[0] = max(self.data0.high.get(
                ago=-1, size=self.params.period))*1.2
            self.lines.bottom[0] = min(self.data0.low.get(
                ago=-1, size=self.params.period))*0.8
        else:
            self.lines.top[0] = self.lines.top[-1]
            self.lines.bottom[0] = self.lines.bottom[-1]

        height = (self.top[0] - self.bottom[0]) / 10
        self.lines.l1[0] = self.lines.bottom[0] + height
        self.lines.l2[0] = self.lines.bottom[0] + height*2
        self.lines.l3[0] = self.lines.bottom[0] + height*3
        self.lines.l4[0] = self.lines.bottom[0] + height*4
        self.lines.l5[0] = self.lines.bottom[0] + height*5
        self.lines.l6[0] = self.lines.bottom[0] + height*6
        self.lines.l7[0] = self.lines.bottom[0] + height*7
        self.lines.l8[0] = self.lines.bottom[0] + height*8
        self.lines.l9[0] = self.lines.bottom[0] + height*9


class GridPositionIndicator(bt.Indicator):
    params = (('period', 144), ('grid_size', 10))
    lines = ('position',)

    def __init__(self):
        self.addminperiod(self.params.period+1)
        self.grid_lines = [0] * (self.params.grid_size+1)
        self.pre_pos = None

    def next(self):
        if self.grid_lines == [0] * (self.params.grid_size+1) or self.data0.high >= self.grid_lines[-1] or self.data0.low <= self.grid_lines[0]:
            self.grid_lines[-1] = max(self.data0.high.get(
                ago=-1, size=self.params.period))*1.2
            self.grid_lines[0] = min(self.data0.low.get(
                ago=-1, size=self.params.period))*0.8

        height = (self.grid_lines[-1] - self.grid_lines[0]
                  ) / self.params.grid_size
        for i in range(1,  self.params.grid_size, 1):
            self.grid_lines[i] = self.grid_lines[0] + height*i

        idx = self._get_closest_index(self.grid_lines, self.data0.close)
        pos = (len(self.grid_lines) - idx - 1)/(len(self.grid_lines) - 1)
        r = 1 / self.params.grid_size
        if self.pre_pos is None or pos < self.pre_pos:
            self.lines.position[0] = round(pos, 2)
            self.pre_pos = round(pos, 2)
        elif pos > self.pre_pos + r:
            self.lines.position[0] = round(pos - r, 2)
            self.pre_pos = round(pos - r, 2)
        else:
            self.lines.position[0] = round(self.pre_pos, 2)

    def _get_closest_index(self, array, num):
        arr = [num - a for a in array]
        for idx, value in enumerate(arr):
            if value < 0:
                return idx - 1 if idx - 1 >= 0 else 0
        return -1
