import backtrader as bt
import numpy as np

class ClassicGridIndicator(bt.Indicator):
    params=(
        ('bottom',400),
        ('top',40000)
    )
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
        pass

    def next(self):
        self.lines.bottom[0] = self.params.bottom
        self.lines.top[0] = self.params.top

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