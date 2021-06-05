import backtrader as bt
import numpy as np
import pandas as pd
import math
import time
from datetime import datetime
from indicators.classic_grid import ClassicGridIndicator


pd.set_option('display.max_rows', 500)

class ClassicGridStrategy(bt.Strategy):
    params = (
        ('bottom', 400),
        ('top', 40000),
        ('count', 250),
        ('live_records',None),
        ('cash',None),
        ('position',None),
    )

    def __init__(self):
        self.grid = ClassicGridIndicator(bottom=self.params.bottom,top=self.params.top)
        self.grid.plotinfo.plotmaster = self.data
        self.grid_object = GridManager(self)
        
        self.trades = {}
        self.profit = 0

    def start(self):
        print('start')

    def next(self):
        if len(self) == 1:
            if self.params.cash is None:
                cash = self.broker.cash - self.broker.getcommissioninfo(self.data).p.commission * self.broker.cash
            else:
                cash = self.params.cash
            if self.params.position is not None:
                cash = cash + self.params.position * self.data0.close[0]
            self.grid_object.start(self.data0.close[0], cash)      
            # self.grid_object.start(31000, cash)      
        elif not self.grid_object.first_order.pre_casted:  # 尚未下预埋单
            self.grid_object.pre_cast(deep=10)
            self.grid_object.first_order.pre_casted = True
            self._init_trades()

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed, order.Cancelled] and self.grid_object.first_order.pre_casted:
            if order.isbuy():
                # self.log("   BUY(oid={id})：  price={p}, amount={m}".format(id=order.ref, p=round(order.created.price,3),m=round(order.created.size,4)))
                buy_order = self.trades[order.ccxt_order['price']]
                if buy_order is not None:
                    if 'sell' in buy_order:
                        profit = order.ccxt_order['amount']*(buy_order['sell'] - order.executed.price)
                        self.profit +=profit
                        self.log('buy=%.2f,sell=%.2f,size=%.4f,profit=%.3f, total_profit=%.3f' % ( order.ccxt_order['price'],buy_order['sell'], order.ccxt_order['amount'],profit,self.profit))
                        self.trades.update({order.ccxt_order['price']:{}})
                    else:
                        self.trades.update({order.ccxt_order['price']:{'buy':order.ccxt_order['price']}})
            elif order.issell():
                # self.log("   SELL(oid={id})： price={p}, amount={m}".format(id=order.ref, p=round(order.created.price,3),m=round(order.created.size,4)))
                trigger_price, buy_order = self._get_buy_order(order.ccxt_order['price']) 
                if buy_order is not None:
                    if 'buy' in buy_order:
                        profit = order.ccxt_order['amount']*(order.ccxt_order['price'] - buy_order['buy'])
                        self.profit += profit
                        self.log('buy=%.2f,sell=%.2f,size=%.4f,profit=%.3f, total_profit=%.3f' % (buy_order['buy'], order.ccxt_order['price'], order.ccxt_order['amount'],profit, self.profit))
                        self.trades.update({trigger_price:{}})
                    else:
                        self.trades.update({trigger_price:{'sell':order.ccxt_order['price']}})
            self.grid_object.add_order(order)
        self.order = None

    def stop(self):
        pass

    def log(self,message):
        print('%s:%s' % (self.data0.datetime.datetime(0), message))

    def _get_buy_order(self, price):
        try:
            idx = list(self.trades.keys()).index(price)

            if idx >= 0:
                return list(self.trades.keys())[idx - 1], self.trades[list(self.trades.keys())[idx - 1]]
        except:
            return None,None
        return None, None

    def _init_trades(self):
        count=0
        for idx, row in self.grid_object.manager.iterrows():
            if row['trigger_price'] > self.grid_object.first_order.created.price:
                if count==0:
                    count+=1
                    ix = len(list(self.trades.keys())) - 1
                    last_price = list(self.trades.keys())[ix]
                    self.trades.update({last_price:{'buy':self.grid_object.first_order.created.price}})
                self.trades.update({row['trigger_price']:{'buy':self.grid_object.first_order.created.price}})
            else:
                self.trades.update({row['trigger_price']:{}})


class GridManager():

    def __init__(self, strategy):
        self.bottom = strategy.params.bottom
        self.top = strategy.params.top
        self.count = strategy.params.count
        self.live_records = strategy.params.live_records # 实盘时 计算交易记录
        self.cash = strategy.params.cash # 实盘时 计划用于交易的现金
        self.position = strategy.params.position # 实盘时 初始投入策略的标的
        self.strategy = strategy
        self.first_order = None
        self.deep = None
        self.index = None
        self.last_preorders = [] # 最新的预埋单

        lines =  np.arange(self.bottom, self.top, (self.top-self.bottom)/(self.count - 1))
        lines = [round(p,2) for p in lines]
        if lines[-1] != self.top:
            lines = np.append(lines,self.top)
        self.manager = pd.DataFrame(columns=['trigger_price','size'])
        self.manager['trigger_price'] = lines

    def start(self, price, cash):
        """计算每格的触发价格，并根据当前价格和现金买入初始头寸

        Args:
            price ([float]): 最初建立头寸时的价格
            cash ([float]): 投入的总资金（扣除手续费)
        """
        # 每份等金额
        sell_grid = self.manager[self.manager['trigger_price'] > price]
        size = 0

        for index, row in sell_grid.iterrows():
            self.manager.loc[index,'size'] = cash / self.count / row['trigger_price']
            size += self.manager.loc[index,'size']

        buy_grid = self.manager[self.manager['trigger_price'] <= price]
        self.index = len(buy_grid) - 1
        buy_grid.drop(self.index,inplace=True)
        for index, row in buy_grid.iterrows():
            self.manager.loc[index, 'size'] = cash /self.count / row['trigger_price']

        self.manager.loc[self.index, 'size'] = cash / self.count/ row['trigger_price']
        
        # 建仓 根据当前价格所在网格空间的比例 买入对应金额的
        if self.position is not None:
            size = size - self.position
        size = round(size,4)
        if size > 0:
            self.first_order = self.strategy.buy(size = size)
        elif size <= 0 :
            self.first_order = self._create_first_order()
            self.first_order.created.price=price

        self.first_order.pre_casted = False

    def pre_cast(self, deep=None):
        """根据建立的网格 建立预埋单

        Args:
            deep ([int], optional): [预埋单深度，即预埋跟当前价格相隔几档的买卖单]. 缺省：None，建立网格范围内的所有预埋单.
        """
        self.deep = deep
        for idx,row in self._get_range(-deep).iterrows():
            size = round(row['size'],4)
            order = self.strategy.buy(size=size, exectype=bt.Order.Limit, price = round(row['trigger_price'],2) )
        for idx,row in self._get_range(deep).iterrows():
            size = round(row['size'],4)
            order = self.strategy.sell(size=size, exectype=bt.Order.Limit, price =round( row['trigger_price'],2))

    def add_order(self, triggered_order):
        triggered_index = self._get_index_from_order(triggered_order)
        current_preorders = self._get_pre_orders_live()

        finished_orders = list(set(self.last_preorders).difference(set(current_preorders)))
        if finished_orders == []:
            finished_orders = [triggered_index]
        if len(finished_orders) == 1:
            supposed_orders = self._get_supposed_orders(triggered_index,[])    
            to_trade_orders =  list(set(supposed_orders).difference(set(current_preorders)))
            self.index = self._get_index(triggered_index, finished_orders)

            buy_orders = [order for order in to_trade_orders if order < self.index]
            for order in buy_orders:
                row = self.manager.loc[order]
                size = round(row['size'],4)
                self.strategy.buy(size=size, exectype=bt.Order.Limit, price=round(row['trigger_price'],2))
            
            sell_orders = [order for order in to_trade_orders if order > self.index]
            for order in sell_orders:
                row = self.manager.loc[order]
                size = round(row['size'],4)
                self.strategy.sell(size=size, exectype=bt.Order.Limit, price=round(row['trigger_price'],2))
        else:
            pass

        self.last_preorders = self._get_pre_orders_live()
   
    def _get_index(self, triggered_index, reserved_orders):
        if len(reserved_orders) == 1 and triggered_index == reserved_orders[0]:
            return triggered_index
        elif triggered_index > max(reserved_orders):
            return min(reserved_orders)
        elif triggered_index < min(reserved_orders):
            return max(reserved_orders)
        raise ValueError('未实现的跳开情况')
      
    def _get_pre_orders(self):
        pre_orders = []
        for order in self.strategy.broker.orders:
            if order.status in [order.Submitted, order.Accepted]:
                index = self.manager['trigger_price'].tolist().index(order.ccxt_order['price'])
                if index is not None:
                    pre_orders.append(index)
        pre_orders.sort()
        return pre_orders

    def _get_pre_orders_live(self):
        pre_orders = []
        for order in self.strategy.broker.open_orders:
            index = self.manager['trigger_price'].tolist().index(order.ccxt_order['price'])
            if index is not None:
                pre_orders.append(index)
        pre_orders.sort()
        return pre_orders


    def _get_supposed_orders(self,triggered_index, reserved_orders):
        idxs = range(triggered_index - self.deep,triggered_index + self.deep+1)
        idxs = [idx for idx in idxs if idx >=0 and idx < len(self.manager)]
        if reserved_orders == []:
            idxs.remove(triggered_index)
        elif triggered_index > min(reserved_orders):
            idxs.remove(min(reserved_orders))
        else:
            idxs.remove(max(reserved_orders))
        return idxs
   
    def _get_range(self, range):
        """得到self.index上下range区域的dataframe，不包含range

        Args:
            range ([int]): range>0 获取index后range的区域，否则获取index前range的区域

        Returns:
            [dataframe]: [包含区域]
        """
        if range > 0 :
            return self.manager[self.manager.index > self.index].head(range)
        elif range < 0 :
            return self.manager[self.manager.index < self.index].tail(-range)
        raise ValueError('range参数不能为0')

    def _get_index_from_order(self,order):
        for idx, row in self.manager.iterrows():
            if row['trigger_price'] == order.ccxt_order['price']:
                return idx
        return None
    
    def _is_ele_null(self, ele):
        try:
            if pd.isnull(ele):
                return True
            return False
        except:
            return False
    
    def _create_first_order(self):
        class _created():
            price=0
        class _first_order():
            created=_created()
            pre_casted=None
        return _first_order()

if __name__ == '__main__':
    class Params():
        bottom = 2000
        top = 5000
        count = 20

    class Strategy():
        params = None

        def buy(self, size):
            print('buy ' + str(size))
            return Params()

    strategy = Strategy()
    strategy.params = Params    

    grid = GridManager(strategy)
    grid.start(4268, 100000)
    print(grid.manager)

