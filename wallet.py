import requests
import json
import pandas as pd
import numpy as np
from datetime import datetime
from colorama import init, Fore, Back, Style

class Wallet:
    
    def __init__(self, symbol = 'BTCUSDT'):
        self.budget        = 10000
        self.order_list    = []
        self.current_price = 0
        self.old_price     = 0
        self.ema_quick     = [0, 0, 0]
        self.ema_slow      = [0, 0, 0]
        self.ma_quick      = [0, 0, 0]
        self.ma_slow       = [0, 0, 0]
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
        self.ratio         = 6/5
        self.symbol        = symbol
        self.win_trades    = 0
        self.supertrend    = [0, 0, 0, 0, 0]
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
            self.win_trades += 1
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
                    return self.check_tp()
            else:
                if self.current_price < order['TP'] or self.current_price > order['SL']:
                    self.sell_order(i)
                    return self.check_tp()


    def update_price(self):
        if not self.simulation:
            r = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=' + self.symbol)
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
        self.ema_quick = self.get_ema(21)
        self.ema_slow  = self.get_ema(55)
        if self.ema_quick[-2] > self.ema_slow[-2]:
            self.trend = 'up'
        else:
            self.trend = 'down'

    def update_ma(self):
        self.ma_quick = self.get_ma(21)
        self.ma_slow  = self.get_ma(55)

    def check_cross(self):
        if not self.order:
            self.order = True
            if self.ema_quick[-3] > self.ema_slow[-3] and self.ema_quick[-2] < self.ema_slow[-2]:
                SL = min(self.ema_slow[-2], 1.01*self.current_price)
                TP = self.current_price - ((SL - self.current_price) * self.ratio)
                self.place_order('V', SL, TP, self.current_price, (0.1*self.budget) / self.current_price)
            elif self.ema_quick[-3] < self.ema_slow[-3] and self.ema_quick[-2] > self.ema_slow[-2]:
                SL = max(self.ema_slow[-2], 0.99*self.current_price)
                TP = self.current_price + ((self.current_price - SL) * self.ratio)
                self.place_order('A', SL, TP, self.current_price, (0.1*self.budget) / self.current_price)

    

    def check_new_candle(self):
        if not self.simulation:
            url = 'https://api.binance.com/api/v3/klines?symbol=' + self.symbol + '&interval=' + self.time
            data = requests.get(url).json()
            if self.candle_id != data[0][0]:
                self.candle_id = data[0][0]
                self.order = False
                self.update_ema()
                self.update_ma()
                self.check_cross()
        else:
            if self.simu_candle_index == 0:
                self.order = False
                self.update_ema()
                self.update_ma()
                self.check_cross()

    def get_ema(self, period):
        if not self.simulation:
            url = 'https://api.binance.com/api/v3/klines?symbol=' + self.symbol + '&interval=' + self.time
            data = requests.get(url).json()
            close_prices = [float(i[4]) for i in data]
            return calculate_ema(close_prices, period)
        else:
            if self.simulation_index < period + 5:
                self.order = True
                return [0, 0, 0]
            start_index = max(self.simulation_index - 500, 0)
            return calculate_ema(self.df['4'][start_index + 1:self.simulation_index + 1], period)

    def get_ma(self, period):
        if not self.simulation:
            url = 'https://api.binance.com/api/v3/klines?symbol=' + self.symbol + '&interval=' + self.time
            data = requests.get(url).json()
            close_prices = [float(i[4]) for i in data]
            return calculate_ma(close_prices, period)
        else:
            print('cc')
            if self.simulation_index < period + 5:
                self.order = True
                return [0, 0, 0]
            start_index = max(self.simulation_index - 500, 0)
            return calculate_ma(self.df['4'][start_index + 1:self.simulation_index + 1], period)
    
    def check_end(self):
        if self.simulation_index >= len(self.df) - 1:
            self.end = True
            self.close_all_order()

    def close_all_order(self):
        while self.order_list:
            self.sell_order(0)

    def update_supertrend(self, length, factor):
        if not self.simulation:
            url = 'https://api.binance.com/api/v3/klines?symbol=' + self.symbol + '&interval=' + self.time
            data = requests.get(url).json()
            opens  = np.array([float(i[1]) for i in data])
            highs  = np.array([float(i[2]) for i in data])
            lows   = np.array([float(i[3]) for i in data])
            closes = np.array([float(i[4]) for i in data])
        else:
            opens  = self.df['1']
            highs  = self.df['2']
            lows   = self.df['3']
            closes = self.df['4']

        tr1 = pd.DataFrame(highs[1:] - lows[1:])
        tr2 = pd.DataFrame(abs(highs[1:] - closes[:-1]))
        tr3 = pd.DataFrame(abs(lows[1:] - closes[:-1]))
        frames = [tr1, tr2, tr3]
        tr = pd.concat(frames, axis = 1, join = 'inner').max(axis = 1)
        atr = tr.ewm(10).mean()
        atr = np.array(atr)
        hla = np.array((highs[1:] + lows[1:]) / 2)
        basic_upper_band = (hla + (3 * atr))
        basic_lower_band = (hla - (3 * atr))
        final_upper_band = [0]
        for i in range(1, len(basic_upper_band)):
            if basic_upper_band[i] < final_upper_band[i-1] or closes[i-1] > final_upper_band[i-1]:
                final_upper_band.append(basic_upper_band[i])
            else:
                final_upper_band.append(final_upper_band[i-1])
                
        final_lower_band = [0]
        for i in range(1, len(basic_lower_band)):
            if basic_lower_band[i] > final_lower_band[i-1] or closes[i-1] < final_lower_band[i-1]:
                final_lower_band.append(basic_lower_band[i])
            else:
                final_lower_band.append(final_lower_band[i-1])
        self.supertrend = [0]
        for i in range(1, len(final_upper_band)):
            if self.supertrend[i-1] == final_upper_band[i-1] and closes[i] < final_upper_band[i]:
                self.supertrend.append(final_upper_band[i])
            elif self.supertrend[i-1] == final_upper_band[i-1] and closes[i] > final_upper_band[i]:
                self.supertrend.append(final_lower_band[i])
            elif self.supertrend[i-1] == final_lower_band[i-1] and closes[i] > final_lower_band[i]:
                self.supertrend.append(final_lower_band[i])
            elif self.supertrend[i-1] == final_lower_band[i-1] and closes[i] < final_lower_band[i]:
                self.supertrend.append(final_upper_band[i])

def calculate_ma(data, smaPeriod):
    j = next(i for i, x in enumerate(data) if x is not None)
    our_range = range(len(data))[j + smaPeriod - 1:]
    empty_list = [None] * (j + smaPeriod - 1)
    sub_result = [np.mean(data[i - smaPeriod + 1: i + 1]) for i in our_range]

    return np.array(empty_list + sub_result)

def calculate_ema(prices, days, smoothing=2):
    smoothing = 2
    ema = [sum(prices[:days]) / days]
    for price in prices[days:]:
        ema.append((price * (smoothing / (1 + days))) + ema[-1] * (1 - (smoothing / (1 + days))))
    return ema

