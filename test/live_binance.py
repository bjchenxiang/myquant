import backtrader as bt
from ccxtbt import CCXTStore
import time
import datetime as dt
from datetime import datetime

DEBUG = True


class StrategyBase(bt.Strategy):
    def __init__(self):
        self.order = None
        self.last_operation = "SELL"
        self.status = "DISCONNECTED"
        self.bar_executed = 0
        self.buy_price_close = None
        self.soft_sell = False
        self.hard_sell = False
        self.log("Base strategy initialized")

    def reset_sell_indicators(self):
        self.soft_sell = False
        self.hard_sell = False
        self.buy_price_close = None

    def notify_data(self, data, status, *args, **kwargs):
        self.status = data._getstatusname(status)
        print(self.status)
        if status == data.LIVE:
            self.log("LIVE DATA - Ready to trade")

    def short(self):
        if self.last_operation == "SELL":
            return

        if ENV == DEVELOPMENT:
            self.log("Sell ordered: $%.2f" % self.data0.close[0])
            return self.sell()

        cash, value = self.broker.get_wallet_balance(COIN_TARGET)
        amount = value*0.99
        self.log("Sell ordered: $%.2f. Amount %.6f %s - $%.2f USDT" % (self.data0.close[0],
                                                                       amount, COIN_TARGET, value), True)
        return self.sell(size=amount)

    def long(self):
        if self.last_operation == "BUY":
            return

        self.log("Buy ordered: $%.2f" % self.data0.close[0], True)
        self.buy_price_close = self.data0.close[0]
        price = self.data0.close[0]

        if ENV == DEVELOPMENT:
            return self.buy()

        cash, value = self.broker.get_wallet_balance(COIN_REFER)
        amount = (value / price) * 0.99  # Workaround to avoid precision issues
        self.log("Buy ordered: $%.2f. Amount %.6f %s. Ballance $%.2f USDT" % (self.data0.close[0],
                                                                              amount, COIN_TARGET, value), True)
        return self.buy(size=amount)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            self.log('ORDER ACCEPTED/SUBMITTED')
            self.order = order
            return

        if order.status in [order.Expired]:
            self.log('BUY EXPIRED', True)

        elif order.status in [order.Completed]:
            if order.isbuy():
                self.last_operation = "BUY"
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm), True)
                if ENV == PRODUCTION:
                    print(order.__dict__)

            else:  # Sell
                self.last_operation = "SELL"
                self.reset_sell_indicators()
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm), True)

            # Sentinel to None: new orders allowed
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected: Status %s - %s' % (order.Status[order.status],
                                                                         self.last_operation), True)

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        color = 'green'
        if trade.pnl < 0:
            color = 'red'

        self.log(colored('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm), color), True)

    def log(self, txt, send_telegram=False, color=None):
        if not DEBUG:
            return

        value = datetime.now()
        if len(self) > 0:
            value = self.data0.datetime.datetime()

        if color:
            txt = colored(txt, color)

        print('[%s] %s' % (value.strftime("%d-%m-%y %H:%M"), txt))
        if send_telegram:
            send_telegram_message(txt)


class BasicRSI(StrategyBase):
    params = dict(
        period_ema_fast=10,
        period_ema_slow=100
    )

    def __init__(self):
        StrategyBase.__init__(self)
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

        if self.status != "LIVE":  # waiting for live status in production
            return

        if self.order:  # waiting for pending order
            return

        # stop Loss
        if self.profit < -0.03:
            self.log("STOP LOSS: percentage %.3f %%" % self.profit)
            self.short()

        if self.last_operation != "BUY":
            if self.rsi < 30 and self.ema_fast > self.ema_slow:
                self.long()

        if self.last_operation != "SELL":
            if self.rsi > 70:
                self.short()


if __name__ == '__main__':
    COIN_TARGET = "BTC"
    COIN_REFER = "USDT"

    cerebro = bt.Cerebro(quicknotify=True)
    broker_config = {
        'apiKey': 'x2f7KEqKQTe6VyoW8JqTa666KcdvR6l5WlsBldC4Mn2MVvbHKN3RKUlaELSdeOva',
        'secret': 'KjoMLIlCDxmAGSSPdQhCfZ9fOhPvnbN3s7xXIfNToH3yD9UarCOlLZEgbC2fBolA',
        'nonce': lambda: str(int(time.time() * 1000)),
        'enableRateLimit': True,
    }
    store = CCXTStore(exchange='binance', currency='USDT',
                      config=broker_config, retries=5, debug=True)
    broker_mapping = {
        'order_types': {
            bt.Order.Market: 'market',
            bt.Order.Limit: 'limit',
            bt.Order.Stop: 'stop-loss',
            bt.Order.StopLimit: 'stop limit'
        },
        'mappings': {
            'closed_order': {
                'key': 'status',
                'value': 'closed'
            },
            'canceled_order': {
                'key': 'status',
                'value': 'canceled'
            }
        }
    }

    broker = store.getbroker(broker_mapping=broker_mapping)
    cerebro.setbroker(broker)

    hist_start_date = dt.datetime.utcnow() - dt.timedelta(minutes=30000)
    data = store.getdata(
        dataname='%s/%s' % (COIN_TARGET, COIN_REFER),
        name='%s%s' % (COIN_TARGET, COIN_REFER),
        timeframe=bt.TimeFrame.Minutes,
        fromdate=hist_start_date,
        compression=30,
        ohlcv_limit=99999
    )
    cerebro.adddata(data)

    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="ta")
    cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")

    # Include Strategy
    cerebro.addstrategy(BasicRSI)

    # Starting backtrader bot
    initial_value = cerebro.broker.getvalue()
    print('Starting Portfolio Value: %.2f' % initial_value)
    result = cerebro.run()

    # Print analyzers - results
    final_value = cerebro.broker.getvalue()
    print('Final Portfolio Value: %.2f' % final_value)
    print('Profit %.3f%%' % ((final_value - initial_value) / initial_value * 100))
    print_trade_analysis(result[0].analyzers.ta.get_analysis())
    print_sqn(result[0].analyzers.sqn.get_analysis())
