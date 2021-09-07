import requests
import json
import pandas as pd
from datetime import datetime
from colorama import init, Fore, Back, Style

class Wallet:
    
    def __init__(self):
        self.budget        = 10000
        self.order_list    = []
        self.current_price = 0
        self.old_price     = 0
        self.ema5          = [0, 0, 0]
        self.ema20         = [0, 0, 0]
        self.order         = True
        self.candle_id     = 0
        self.trend         = ''
        self.time          = '5m'
        self.simulation    = False
        self.file          = ''
        self.df            = pd.DataFrame()
        self.simulation_index = 0
        self.simu_candle_index = 0
        self.end           = False
        self.nb_of_trades  = 0
        init()

    def load_simulation_file(self, path):
        self.file = path
        self.simulation = True
        self.df = pd.read_csv(self.file)
        if len(self.df) < 500:
            print('Simulation file too small')
        self.simulation_index = 500

    def place_order(self, type_, SL, TP, price, qty):
        print(Fore.CYAN + "Order placed :", type_, SL, TP, price, qty, Style.RESET_ALL)
        self.order_list.append({'type' : type_, 'price' : price, 'quantity' : qty, 'value' : qty*price, 'current_value' : qty*price, 'SL' : SL, 'TP' : TP, 'profit' : 0, 'percent' : 0})
        self.budget -= qty*price
        self.nb_of_trades += 1

    def sell_order(self, id_):
        self.update_orders()
        order = self.order_list[id_]
        
        if (order['type'] == 'A' and self.current_price >= order['TP']) or order['type'] == 'V' and self.current_price <= order['TP']:
            result = Fore.GREEN + 'Won'
        else:
            result = Fore.RED + 'Lost'

        print(result, order['type'], order['SL'], order['TP'], order['price'], order['quantity'], Style.RESET_ALL)
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
        if not self.simulation:
            r = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=' + symbol)
            price = json.loads(r.text)['price']
            self.old_price = self.current_price
            self.current_price = float(price)
        else:
            self.current_price = float(self.df[str(self.simu_candle_index + 1)][self.simulation_index])
            self.simu_candle_index = (self.simu_candle_index + 1) % 4
            if self.simu_candle_index == 0:
                self.simulation_index += 1

    def get_date(self):
        if not self.simulation:
            return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        else:
            return datetime.fromtimestamp(self.df['0'][self.simulation_index] // 1000).strftime('%Y-%m-%d %H:%M:%S')


    def update_ema(self):
        self.ema5  = self.get_ema(21)
        self.ema20 = self.get_ema(55)
        if self.ema5[-2] > self.ema20[-2]:
            self.trend = 'up'
        else:
            self.trend = 'down'

    def check_cross(self):
        if not self.order:
            self.order = True
            if self.ema5[-3] > self.ema20[-3] and self.ema5[-2] < self.ema20[-2]:
                SL = min(self.ema20[-2], 1.01*self.current_price)
                TP = min(self.current_price - ((SL - self.current_price) * 1.5), self.current_price * 0.9975)
                self.place_order('V', SL, self.current_price - ((SL - self.current_price) * 1.5), self.current_price, 0.01)
            elif self.ema5[-3] < self.ema20[-3] and self.ema5[-2] > self.ema20[-2]:
                SL = max(self.ema20[-2], 0.99*self.current_price)
                TP = max(self.current_price + ((self.current_price - SL) * 1.5), 1.0025*self.current_price)
                self.place_order('A', SL, TP, self.current_price, 0.01)

    def check_new_candle(self, symbol = 'BTCUSDT'):
        if not self.simulation:
            url = 'https://api.binance.com/api/v3/klines?symbol=' + symbol + '&interval=' + self.time
            data = requests.get(url).json()
            if self.candle_id != data[0][0]:
                self.candle_id = data[0][0]
                self.order = False
                self.update_ema()
                self.check_cross()
        else:
            if self.simu_candle_index == 0:
                self.order = False
                self.update_ema()
                self.check_cross()

    def get_ema(self, period, symbol = 'BTCUSDT'):
        if not self.simulation:
            url = 'https://api.binance.com/api/v3/klines?symbol=' + symbol + '&interval=' + self.time
            data = requests.get(url).json()
            close_prices = [float(i[4]) for i in data]
            return calculate_ema(close_prices, period)
        else:
            if self.simulation_index < period + 5:
                self.order = True
                return [0, 0, 0]
            start_index = max(self.simulation_index - 500, 0)
            return calculate_ema(self.df['4'][start_index + 1:self.simulation_index + 1], period)
    
    def check_end(self):
        if self.simulation_index >= len(self.df) - 1:
            self.end = True

def calculate_ema(prices, days, smoothing=2):
    smoothing = 2
    ema = [sum(prices[:days]) / days]
    for price in prices[days:]:
        ema.append((price * (smoothing / (1 + days))) + ema[-1] * (1 - (smoothing / (1 + days))))
    return ema

