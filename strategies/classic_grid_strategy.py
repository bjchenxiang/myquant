import backtrader as bt
import numpy as np
import pandas as pd
import math
import time
from enum import Enum
from datetime import datetime
from indicators.classic_grid import ClassicGridIndicator
from utils.math import floor, cut, get_min_space_index


pd.set_option('display.max_rows', 500)

class GridType(Enum):
    Different=0 #等金额
    Ratio=1 #等比例
    Dynamic=2 # 根据指标ATR
    Manual=3 # 手工指定

class GridSizeType(Enum):
    FixCash=0 #固定金额
    FixAmount=1 # 固定数量
    Compound=2 # 复利

class ClassicGridStrategy(bt.Strategy):
    params = (
        ('bottom', 400), # 网格底部价格
        ('top', 40000),  # 网格顶部价格
        ('type',GridType.Different),  # 网格类型
        ('line_space', 100), #  网格间距
        ('max_order_amount', 3), # 单向预埋单数量
        ('percise', 3),  #  价格精度
        ('min_trade_unit', 0.00001), #最小交易单位
        ('cash',3000),  # 用于本策略使用的最大现金
        ('position', 0), # 参与网格的仓位
        ('is_live', False), # 是否实盘交易
    )

    def __init__(self):
        self.grid_manager = None
        self.is_trading = False        
        self.order = None
        # self.trades = pd.DataFrame(columns=['price','buy','sell','size','profit'])
        self.orders = OrderManager()
        

    def start(self):
        message = '启动网格策略：' + ('实盘交易' if self.params.is_live else '模拟交易')
        dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.log(message, date=dt)

    def next(self):
        if not (self.params.bottom <= self.data0.close[0] <= self.params.top):
            self.stop()
      
        # 建仓
        if self.grid_manager is None:
            open_orders = self._get_open_orders()
            self.grid_manager = GridManager(self.params, self._get_cash(), self.params.min_trade_unit)
            self.grid_manager.check_orders(open_orders, self.data0.close[0]) 
            size = self.grid_manager.get_availble_cash() / self.data0.close - self.params.position
            size = cut(size, self.params.min_trade_unit)
            self.order = self.buy(size=size)
            return
        # 检查网格完整性
        if not self.is_trading and self.order is None: 
            open_orders = self._get_open_orders()
            # print(len(open_orders))
            self._set_grid_index(self.orders.get_last_key_price())           
            df_orders = self.grid_manager.check_orders(open_orders, self.data0.close[0])  #dataframe,columes=['price','action','size']
            self.is_trading = True
            for idx, order in df_orders.iterrows():
                if order['action'] == 'buy':
                    self.buy(size=order['size'], exectype=bt.Order.Limit, price=order['price'])
                elif order['action'] == 'sell':
                    self.sell(size = order['size'], exectype=bt.Order.Limit, price=order['price'])
                elif order['action'] == 'drop':
                    order_obj = self._find_order(price=order['price'])
                    self.cancel(order_obj)
            self.is_trading = False
            

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:
            size, created_price = self._get_order_value(order)
            trade_price = self._get_executed_price(order)
            dt = self._get_executed_time(order)
            if order.isbuy():
                self.orders.add_order(dt,'buy',size,created_price,trade_price)
                # self.log("   BUY(oid={id})：  price={p}, amount={m}, size={s}， cash={c}".format(id=order.ref, p=round(created_price,3),m=round(size,4),s=round(self.getposition().size,4),c=round(self.broker.cash)))
            elif order.issell():
                self.orders.add_order(dt,'sell',size,created_price,trade_price)
                # self.log("   SELL(oid={id})： price={p}, amount={m}, size={s}， cash={c}".format(id=order.ref, p=round(created_price,3),m=round(size,4),s=round(self.getposition().size,4),c=round(self.broker.cash)))
                self.orders.orders.loc[self.orders.orders['action']=='buy','add']=1
                self.orders.orders.loc[self.orders.orders['action']=='sell','add']=-1
                self.orders.orders['size']=self.orders.orders['size'].abs()*self.orders.orders['add']
                pos = self.orders.orders['size'].sum()
                cash = (self.orders.orders['trade_price'] * self.orders.orders['size']).sum()
                self.log('Buy %.4f at price %.2f, now current price=%.2f' % (pos,cash/pos, self.data0.close[0]))
            self.order = None
               
    def stop(self):
        self.log('策略停止',date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    def log(self,message, date=None):
        if date is None:
            date = self.data0.datetime.datetime(0)
        print('%s:%s' % (date, message))

    def _get_order_value(self, order):
        if hasattr(order,'created'):
            return order.created.size,order.created.price
        elif hasattr(order,'ccxt_order'):
            return order.ccxt_order['amount'], order.ccxt_order['price']
        raise ValueError('未定义的订单类型，无法获取交易订单的价格和数量')

    def _get_executed_price(self, order):
        if hasattr(order,'executed'):
            return order.executed.price
        elif hasattr(order,'ccxt_order'):
            return order.ccxt_order['price']
        raise ValueError('未定义的订单类型，无法获取交易订单的价格和数量')

    def _get_executed_time(self, order):
        if hasattr(order,'executed'):
            return bt.utils.num2date(order.executed.dt)
        elif hasattr(order,'ccxt_order'):
            return  order.ccxt_order['dt']
        raise ValueError('未定义的订单类型，无法获取交易订单的价格和数量')

    def _get_open_orders(self):
        def live_orders(orders):
            open_orders = pd.DataFrame(columns=['price','action','size'])
            for order in orders:
                odr = {
                    'price':order.ccxt_order['price'],
                    'action': 'buy' if order.isbuy() else 'sell',
                    'size' : abs(order.ccxt_order['amount'])
                }
                open_orders = open_orders.append(odr, ignore_index=True)               
            return open_orders
        
        def backtest_orders(orders):
            open_orders = pd.DataFrame(columns=['price','action','size'])
            for order in orders:
                if order.status in [order.Submitted, order.Accepted]:
                    odr = {
                        'price':order.created.price,
                        'action': 'buy' if order.isbuy() else 'sell',
                        'size' : abs(order.created.size)
                    }
                    open_orders = open_orders.append(odr, ignore_index=True)               
            return open_orders

        if self.params.is_live:
            return live_orders(self.broker.open_orders)
        else:
            return backtest_orders(self.broker.orders)

    def _set_grid_index(self, current_price):
        active_price = self.grid_manager.grid.loc[self.grid_manager.index, 'trigger_price']
        if current_price > active_price:
            index = get_min_space_index(self.grid_manager.grid['trigger_price'].tolist(),current_price)
            if index >= self.grid_manager.index:
                self.grid_manager.index = index
        elif current_price < active_price:
            index = 1 + get_min_space_index(self.grid_manager.grid['trigger_price'].tolist(),current_price)
            if current_price in self.grid_manager.grid['trigger_price'].tolist():
                self.grid_manager.index = index - 1
            elif index < self.grid_manager.index:
                self.grid_manager.index = index

    def _get_cash(self):
        if self.params.is_live:
            return self.params.cash + self.params.position * self.data0.close[0]
        else:
            return self.broker.cash

    def _find_order(self, price):
        def live_order(orders, price):
            for order in orders:
                if order.ccxt_order['price'] == price:
                    return order
            return None
        
        def backtest_order(orders, price):
            for order in orders:
                if order.created.price == price:
                    return order   
            return None

        if self.params.is_live:
            return live_order(self.broker.open_orders,price)
        else:
            return backtest_order(self.broker.orders, price)


class GridManager():
    
    def __init__(self, params, cash, min_trade_unit=100) -> None:
        self.params = params
        self.grid = None #  self.create_grid(params.type)
        self.cash = cash
        self.min_trade_unit = min_trade_unit
        self.index = -1

    def create_grid(self, price):
        def _create_different_grid(bottom, top, price, line_space):
            # 创建价格分布
            trigger_price = price
            manager = pd.DataFrame(columns=['trigger_price','size'])
            while trigger_price < top:
                manager = manager.append([{'trigger_price':trigger_price}], ignore_index=True)
                trigger_price += line_space
            manager = manager.append([{'trigger_price':trigger_price}], ignore_index=True)

            trigger_price = price - line_space
            while trigger_price > bottom:
                manager = manager.append([{'trigger_price':trigger_price}], ignore_index=True)
                trigger_price -= line_space
            manager = manager.append([{'trigger_price':trigger_price}], ignore_index=True) 
            manager = manager.sort_values(by="trigger_price" , ascending=True) 
            manager = manager.reset_index()
            manager = manager[['trigger_price','size']]

            # 创建对应仓位
            average_price = floor(self.cash / (len(manager) - 1),self.params.percise)
            for idx,row in manager.iterrows():
                size = average_price / row['trigger_price']
                manager.loc[idx,'size'] =  cut(size, self.min_trade_unit)


            return  manager

        
        if self.params.type == GridType.Different:
            manager = _create_different_grid(self.params.bottom, self.params.top, price, self.params.line_space)
        else:
            raise ValueError('未实现的网格类型')

        return manager

    def check_orders(self, open_orders, price):
        """
        orders: dataframe,columes=['price','action','size']
        """
        if self.grid is None:
            self.grid = self.create_grid(price)
        if self.index == -1:# 建仓
            self.index = get_min_space_index(self.grid['trigger_price'].tolist(),price) 

        _open_orders = open_orders.set_index(['price'])
        favorite_orders = self._get_favorite_orders(price).set_index(['price'])
        to_add_orders = pd.concat([favorite_orders, _open_orders, _open_orders]).drop_duplicates(keep=False)
        to_remove_orders = pd.concat([_open_orders, favorite_orders, favorite_orders]).drop_duplicates(keep=False)
        to_remove_orders['action']='drop'
        orders = to_add_orders.append(to_remove_orders)
        orders.reset_index(inplace=True)
        return orders

    def get_availble_cash(self):
        df = self.grid[self.grid.index > self.index]
        df['sum'] = self.grid['trigger_price'] * self.grid['size']
        return sum(df['sum'].tolist())

    def _get_favorite_orders(self, price):
        favorite_orders  = pd.DataFrame(columns=['price','action','size'])
        if self.params.type == GridType.Different:
           
            for i in range(self.index-self.params.max_order_amount,self.index):
                if i < 0:
                    continue
                order = {
                        'price':self.grid.loc[i,'trigger_price'],
                        'action':'buy',
                        'size':self.grid.loc[i,'size']
                    }
                favorite_orders = favorite_orders.append(order, ignore_index=True)

            for i in range(self.index + 1,self.index + self.params.max_order_amount + 1):
                if i >= len(self.grid):
                    break
                order = {
                        'price':self.grid.loc[i,'trigger_price'],
                        'action':'sell',
                        'size':self.grid.loc[i,'size']
                    }
                favorite_orders = favorite_orders.append(order, ignore_index=True)
        else:
            raise ValueError('未定义的网格类型')
        return favorite_orders

class OrderManager():

    def __init__(self):
        self.orders = pd.DataFrame(columns=['time','created_price','trade_price','action','size'])   

    def add_order(self,time, action, size, created_price, trade_price):
        self.orders = self.orders.append({
            'time':time, 
            'action':action, 
            'size':size,
            'created_price':created_price, 
            'trade_price':trade_price
        },ignore_index=True)

    def get_last_key_price(self):
        if len(self.orders) > 0:
            dt = self.orders.tail(1)['time'].values[0]
            action = self.orders.tail(1)['action'].values[0]
            df = self.orders[self.orders['time']==dt]
            if action == 'buy':
                return df['trade_price'].min()
            else:
                return df['trade_price'].max()

        return 0

class GridManager1():

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
        current_preorders = self._get_pre_orders()

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

        self.last_preorders = self._get_pre_orders()
   
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
                index = self.manager['trigger_price'].tolist().index(order.created.price)
                if index is not None:
                    pre_orders.append(index)
        pre_orders.sort()
        return pre_orders

    def _get_pre_orders_live(self):
        pre_orders = []
        for order in self.strategy.broker.open_orders:
            index = self.manager['trigger_price'].tolist().index(order.created.price)
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
            if row['trigger_price'] == order.created.price:
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
        line_space = 100
        percise = 3
        type=GridType.Different
        max_order_amount=3

    class Strategy():
        params = None

        def buy(self, size):
            print('buy ' + str(size))
            return Params()

    strategy = Strategy()
    strategy.params = Params    

    grid = GridManager(Params(), 3000,0.00001)
    open_orders = pd.DataFrame(columns=['price','action','size'])
    orders = grid.check_orders(open_orders,3112.5)
    
    orders = orders.drop(index=2)
    grid.index = 11
    orders = grid.check_orders(orders,3000)
    # print(grid.manager)

