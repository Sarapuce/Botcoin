
from colorama import init, Fore, Back, Style
from os import system, name
import requests
import json
import time
import curses

def init_curses():
    curses.wrapper(main)

def define_color():
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)

def main(stdscr):
    stdscr.nodelay(1)
    define_color()
    price = 0
    order_list = []

    place_order(order_list, 'A', 30000, 60000, 35000, 0.01)
    place_order(order_list, 'V', 90000, 60000, 70000, 0.01)

    try:
        print_header(stdscr)
        stdscr.refresh()

        while(1):
            time.sleep(1)
            price = print_price(stdscr, price)
            update_orders(order_list, price)
            print_orders(stdscr, order_list)
            print_ema(stdscr)
            stdscr.refresh()
            if stdscr.getch() == ord('q'):
                break

    except KeyboardInterrupt:
        curses.endwin()

def print_header(stdscr):
    stdscr.addstr('+--------------------------+\n', curses.color_pair(3))
    stdscr.addstr('|          Botcoin         |\n', curses.color_pair(3))
    stdscr.addstr('+--------------------------+\n', curses.color_pair(3))


def print_price(stdscr, old_price, symbol = 'BTCUSDT'):
    price = get_price(symbol)
    stdscr.addstr(5, 0, 'Symbol : ' + symbol)
    stdscr.addstr(6, 0, 'Price  :               ')
    if old_price > price:
        stdscr.addstr(6, 10, str(price), curses.color_pair(1))
    else:
        stdscr.addstr(6, 10, str(price), curses.color_pair(2))
    return price

def print_orders(stdscr, order_list):
    for i, order in enumerate(order_list):
        if order['profit'] > 0:
            c = curses.color_pair(2)
        else:
            c = curses.color_pair(1)

        stdscr.addstr(4*i + 0, 40, 'Type : ' + order['type'])
        stdscr.addstr(4*i + 0, 50, 'Start price : ' + str(order['price']))
        stdscr.addstr(4*i + 0, 70, 'Quantity : ' + str(order['quantity']))
        stdscr.addstr(4*i + 0, 90, 'Value : ' + str(order['value']))
        stdscr.addstr(4*i + 1, 50, 'SL : ' + str(order['SL']))
        stdscr.addstr(4*i + 1, 70, 'TP : ' + str(order['TP']))
        stdscr.addstr(4*i + 2, 50, 'Profit : {:.2f}'.format(order['profit']), c)
        stdscr.addstr(4*i + 2, 70, '{:.2f}%'.format(order['percent']), c)

def print_ema(stdscr):
    ema5 = get_ema(5)
    ema20 = get_ema(20)
    stdscr.addstr(8, 0, "EMA 5  : {:.2f}".format(ema5))
    stdscr.addstr(9, 0, "EMA 20 : {:.2f}".format(ema20))

def place_order(order_list, type_, SL, TP, price, qty):
    order_list.append({'type' : type_, 'price' : price, 'quantity' : qty, 'value' : qty*price, 'SL' : SL, 'TP' : TP, 'profit' : 0, 'percent' : 0})

def update_orders(order_list, current_price):
    for order in order_list:
        price = order['price']
        if order['type'] == 'A':
            order['profit']  = (current_price - price) * order['quantity']
            order['percent'] =  ((current_price / price) - 1) * 100
        elif order['type'] == 'V':
            order['profit']  = (price - current_price) * order['quantity']
            order['percent'] =  ((price / current_price) - 1) * 100   

def get_price(symbol = 'BTCUSDT'):
    r = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=' + symbol)
    price = json.loads(r.text)['price']
    return float(price)

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

if __name__ == '__main__':
    init_curses()