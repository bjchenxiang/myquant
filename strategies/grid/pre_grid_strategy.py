import backtrader as bt 
import pandas as pd
import numpy as np
from loguru import logger
from utils.message import send_dingding_msg

class PreGridStrategy(bt.Strategy):
    params = (
        ('bottom', 400),
        ('top', 40000),
        ('count', 250),
        ('deep', 10),
        ('live_records',None),
        ('cash',None),
        ('position',None),
        ('ding_token',None)
    )

    def __init__(self):
        self.grid = GridManager(self.params)
        self.first_order = None #  如果网格标的不够，建立网格时购买标的的订单

    def start(self):
        message = '交易提醒：\n预埋单网格策略启动：, 投入资金={:.2f}, 投入标的={:.4f}, 最低价={:d}, 最高价={:d}, 网格数量={:d}， 记录文件={}'.format(self.params.cash,self.params.position,self.params.bottom,
        self.params.top,self.params.count,self.params.live_records)
        
        self.log(message)
        send_dingding_msg(message, self.params.ding_token)

    def next(self):
        if len(self) == 1:
            cash = self._get_available_cash()
            size = self.grid.get_init_buy_size(self.data0.close[0], cash)
            if size is not None:
                self.first_order = self.buy(size=size)
            else:
                buy_orders, sell_orders = self.grid.get_new_orders(None)
                try:
                    self._make_orders(buy_orders,sell_orders)
                except:
                    pass

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:
            if order == self.first_order:
                buy_orders, sell_orders = self.grid.get_new_orders(None)
            else:
                price = self._get_order_price(order)
                idx = self.grid.find_index(price)
                buy_orders, sell_orders = self.grid.get_new_orders(idx, self.broker.open_orders)
                ord = self._get_order(order)
                if order.isbuy():
                    self.grid.add_buy_record(ord)
                else:
                    info = self.grid.compute_gross(ord)
                    if info is not None:
                        self._send_message(info)
                self._make_orders(buy_orders,sell_orders)

    def stop(self):
        self.log('预埋单网格策略结束')

    def log(self,message):
        logger.info(message)

    def _get_available_cash(self):
        if self.params.cash is None:
            cash = self.broker.cash - self.broker.getcommissioninfo(self.data).p.commission * self.broker.cash
        else:
            cash = self.params.cash
        if self.params.position is not None:
            cash = cash + self.params.position * self.data0.close[0]
        return cash

    def _make_orders(self, buy_orders, sell_orders):
        if buy_orders is not None:
            for order in buy_orders:
                if self.broker.cash > order['trigger_price'] * order['size']:
                    try:
                        odr = self.buy(size=order['size'], exectype=bt.Order.Limit, price = order['trigger_price'] )
                    except:
                        continue
        
        if sell_orders is not None:
            for order in sell_orders:
                try:
                    odr = self.sell(size=order['size'], exectype=bt.Order.Limit, price=order['trigger_price'])
                except:
                    continue

    def _get_order_price(self, order):
        return order.ccxt_order['price']

    def _get_order(self, order):
        return {
            'trigger_price':order.ccxt_order['price'],
            'size': order.ccxt_order['amount']
        }

    def _send_message(self, info):
        buy_price = info['buy_price']
        buy_size = info['buy_size']
        sell_price = info['sell_price']
        sell_size = info['sell_size']
        total_gross = info['total_gross']
        total_target = info['total_target']

        message = '交易提醒：\n'
        message += '买入价格:%f;   买入数量:%f' % (buy_price,buy_size)
        message += '\n'
        message += '卖出价格:%f;   卖出数量:%f' % (sell_price,sell_size)
        message += '\n'
        message += '现金收益:%f;   标的收益:%f' % (sell_price*sell_size - buy_price*buy_size,buy_size - sell_size)
        message += '\n'
        message += '总现金收益:%f;   总标的收益:%f' % (total_gross, total_target)

        send_dingding_msg(message, self.params.ding_token)

class GridManager():

    def __init__(self,params):
        self.index = None
        self.params = params
        self.manager = pd.DataFrame(columns=['trigger_price','size'])
        self.manager['trigger_price'] = self._create_lines()
        self.buy_records = {}
        self.trades = []
        self.total_gross = 0 #  总现金收益
        self.total_target = 0 # 总标的收益
        
    def get_init_buy_size(self, price, cash):
        """计算每格的触发价格，并根据当前价格和现金买入初始头寸

        Args:
            price ([float]): 最初建立头寸时的价格
            cash ([float]): 投入的总资金（扣除手续费)
        """
        # 每份等金额
        for index, row in self.manager.iterrows():
            self.manager.loc[index,'size'] = round(cash / self.params.count / row['trigger_price'],5)           
        
        # 设置当前价格所在网格
        buy_grid = self.manager[self.manager['trigger_price'] <= price]
        self.index = len(buy_grid) - 1

        # 建仓时应有头寸
        size = 0
        sell_grid = self.manager[self.manager['trigger_price'] > price]
        for index, row in sell_grid.iterrows():
            size += self.manager.loc[index,'size']
        

        if self.params.position is not None:
            size = size - self.params.position
        size = round(size,4)
        
        return size if size > 0 else None

    def get_new_orders(self, triggered_index, open_orders=None):
        # 创建初始订单
        if triggered_index == None:
            self._create_init_buy_orders()
            return self._get_full_orders(self.index)
        
        buy_orders, sell_orders = self._get_full_orders(triggered_index)
        if abs(triggered_index - self.index) == 1:
            for order in open_orders:
                if order.isbuy():
                    for i in range(len(buy_orders)-1 , -1 ,-1):
                        if order.ccxt_order['price'] == buy_orders[i]['trigger_price']:
                            buy_orders.pop(i)
                            break
                elif order.issell():
                    for i in range(len(sell_orders) - 1, -1, -1):
                        if order.ccxt_order['price'] == sell_orders[i]['trigger_price']:
                            sell_orders.pop(i)
                            break
            self.index = triggered_index
            return buy_orders, sell_orders
        return None, None

    def find_index(self, price):
        for idx, row in self.manager.iterrows():
            if row['trigger_price'] == price:
                return idx
        return None
    
    def add_buy_record(self, order):
        key = order['trigger_price']
        if key in self.buy_records.keys() and self.buy_records[key] !=0:
            print('错误买单：价格=%.2f' % key)
        self.buy_records.update({
            key: order['size']
        })

    def compute_gross(self, sell_order):
        index = self.find_index(sell_order['trigger_price'])        
        if index - 1 >= 0:
            index -= 1
            buy_price = self.manager.loc[index,'trigger_price']
            buy_size = self.manager.loc[index, 'size']
            if buy_price in self.buy_records.keys():
                info = {
                    'buy_price':buy_price,
                    'buy_size': buy_size,
                    'sell_price': sell_order['trigger_price'],
                    'sell_size': sell_order['size'],
                    'total_gross':0,
                    'total_target':0

                }
                self.buy_records.pop(buy_price)
                self.trades.append(info)
                gross = (info['sell_price'] * info['sell_size']) - (info['buy_price']*info['buy_size'])
                self.total_gross += gross
                self.total_target += info['buy_size'] - info['sell_size']
                
                info['total_gross'] = self.total_gross
                info['total_target'] = self.total_target
                print('完成一次网格交易：买入价格=%.2f,数量=%.4f' % (info['buy_price'], info['buy_size']))
                print('                  卖出价格=%.2f,数量=%.4f' % (info['sell_price'], info['sell_size']))
                print('                  现金收益=%.4f, 标的收益=%.5f个' % (gross, info['buy_size'] - info['sell_size']))
                print('                  总现金收益=%.4f, 总标的收益=%.5f个' % (info['total_gross'], info['total_target']))
                print('='*40)

                return info

        return None

    def _get_full_orders(self,index):
        deep = self.params.deep
        p1 = index - deep if index - deep >=0 else 0
        p2 = index - 1 if index - 1 >=0 else 0
        buy_orders = self.manager.loc[p1:p2].to_dict(orient='records')

        p1 = index + 1 if index + 1 < len(self.manager) else len(self.manager)
        p2 = index + deep  if index + deep  < len(self.manager) else len(self.manager) - 1
        sell_orders = self.manager.loc[p1:p2].to_dict(orient='records')

        return buy_orders, sell_orders

    def _create_init_buy_orders(self):
        p1 = self.index if self.index  < len(self.manager) else len(self.manager)
        p2 = self.index + self.params.deep - 1 if self.index + self.params.deep - 1  < len(self.manager) else len(self.manager) - 1
        orders = self.manager.loc[p1:p2].to_dict(orient='records')
        for order in orders:
            self.add_buy_record(order)

    def _create_lines(self):
        params = self.params
        lines =  np.arange(params.bottom, params.top, (params.top-params.bottom)/(params.count - 1))
        lines = [round(p,2) for p in lines]
        if lines[-1] != params.top:
            lines = np.append(lines,params.top)
        
        return lines