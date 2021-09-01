import requests
import json

class Wallet:
    
    def __init__(self):
        self.budget        = 10000
        self.order_list    = []
        self.current_price = 0
        self.old_price     = 0
        self.ema5          = 0
        self.ema20         = 0


    def place_order(self, type_, SL, TP, price, qty):
        self.order_list.append({'type' : type_, 'price' : price, 'quantity' : qty, 'value' : qty*price, 'current_value' : qty*price, 'SL' : SL, 'TP' : TP, 'profit' : 0, 'percent' : 0})
        self.budget -= qty*price

    def sell_order(self, id_):
        self.update_orders()
        order = self.order_list[id_]
        self.order_list = self.order_list[:id_] + self.order_list[id_+1:]
        self.budget += order['value'] + order['profit']

    def update_orders(self):
        for order in self.order_list:
            price = order['price']
            if order['type'] == 'A':
                order['profit']        = (self.current_price - price) * order['quantity']
                order['percent']       = ((self.current_price / price) - 1) * 100
                order['current_value'] = order['quantity'] * self.current_price
            elif order['type'] == 'V':
                order['profit']        = (price - self.current_price) * order['quantity']
                order['percent']       = ((price / self.current_price) - 1) * 100
                order['current_value'] = order['quantity'] * self.current_price

    def check_tp(self):
        for i, order in enumerate(self.order_list):
            if order['type'] == 'A':
                if self.current_price > order['TP'] or self.current_price < order['SL']:
                    self.sell_order(i)
            else:
                if self.current_price < order['TP'] or self.current_price > order['SL']:
                    self.sell_order(i)

    def update_price(self, symbol = 'BTCUSDT'):
        r = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=' + symbol)
        price = json.loads(r.text)['price']
        self.old_price = self.current_price
        self.current_price = float(price)

    def update_ema(self):
        self.ema5  = get_ema(5)
        self.ema20 = get_ema(20)


def calculate_ema(prices, days, smoothing=2):
    smoothing = 2
    ema = [sum(prices[:days]) / days]
    for price in prices[days:]:
        ema.append((price * (smoothing / (1 + days))) + ema[-1] * (1 - (smoothing / (1 + days))))
    return ema

def get_ema(period, symbol = 'BTCUSDT'):
    url = 'https://api.binance.com/api/v3/klines?symbol='+ symbol +'&interval='+'1m'
    data = requests.get(url).json()
    close_prices = [float(i[4]) for i in data]
    return calculate_ema(close_prices, period)[-2]