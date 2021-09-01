
from colorama import init, Fore, Back, Style
from wallet import Wallet
from os import system, name
import requests
import json
import time
import curses

# Use of the wrapper function to get thing easier
def init_curses():
    curses.wrapper(main)

# Definition of color here
def define_color():
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)

# main function each second it will update the interface
def main(stdscr):
    stdscr.nodelay(1)
    define_color()

    wallet = Wallet()

    wallet.place_order('A', 30000, 50000, 35000, 0.01)
    wallet.place_order('V', 50000, 40000, 41000, 0.01)

    try:
        print_header(stdscr)
        stdscr.refresh()

        while(1):
            time.sleep(1)

            wallet.update_price()
            wallet.update_ema()
            wallet.update_orders()
            
            print_price(stdscr, wallet.old_price, wallet.current_price)
            print_orders(stdscr, wallet.order_list)
            print_ema(stdscr, wallet.ema5, wallet.ema20)
            print_budget(stdscr, wallet.budget)

            stdscr.refresh()
            if stdscr.getch() == ord('q'):
                break

    except KeyboardInterrupt:
        curses.endwin()

# Graphical functions
def print_header(stdscr):
    stdscr.addstr('+--------------------------+\n', curses.color_pair(3))
    stdscr.addstr('|          Botcoin         |\n', curses.color_pair(3))
    stdscr.addstr('+--------------------------+\n', curses.color_pair(3))


def print_price(stdscr, old_price, current_price, symbol = 'BTCUSDT'):
    stdscr.addstr(5, 0, 'Symbol : ' + symbol)
    stdscr.addstr(6, 0, 'Price  :               ')
    if old_price > current_price:
        stdscr.addstr(6, 10, str(current_price), curses.color_pair(1))
    else:
        stdscr.addstr(6, 10, str(current_price), curses.color_pair(2))


def print_orders(stdscr, order_list):
    for i, order in enumerate(order_list):
        if order['profit'] > 0:
            c = curses.color_pair(2)
        else:
            c = curses.color_pair(1)

        stdscr.addstr(4*i + 0, 40, 'Type : ' + order['type'])
        stdscr.addstr(4*i + 0, 50, 'Start price : {:.2f}'.format(order['price']))
        stdscr.addstr(4*i + 0, 75, 'Quantity : ' + str(order['quantity']))
        stdscr.addstr(4*i + 0, 95, 'Value : {:.2f}'.format(order['value']))
        stdscr.addstr(4*i + 1, 50, 'SL : {:.2f}'.format(order['SL']))
        stdscr.addstr(4*i + 1, 70, 'TP : {:.2f}'.format(order['TP']))
        stdscr.addstr(4*i + 1, 90, 'Current value : {:.2f}'.format(order['current_value']))
        stdscr.addstr(4*i + 2, 50, 'Profit : {:.2f}'.format(order['profit']), c)
        stdscr.addstr(4*i + 2, 70, '{:.2f}%'.format(order['percent']), c)

def print_ema(stdscr, ema5, ema20):
    stdscr.addstr(8, 0, "EMA 5  : {:.2f}".format(ema5))
    stdscr.addstr(9, 0, "EMA 20 : {:.2f}".format(ema20))

def print_budget(stdscr, budget):
    stdscr.addstr(11, 0, "Budget : {:.2f}".format(budget))


# Sell an order if TP/SL are hit
def check_tp(order_list):
    current_price = get_price()
    value = 0
    for i, order in enumerate(order_list):
        if order['type'] == 'A':
            if current_price > order['TP'] or current_price < order['SL']:
                print('Vente de A')
                value += sell_order(order_list, i)
        else:
            if current_price < order['TP'] or current_price > order['SL']:
                print(current_price)
                print(order['TP'])
                print(order['SL'])
                value += sell_order(order_list, i)

    return value


# Calculate profit from each trade
def update_orders(order_list, current_price):
    for order in order_list:
        price = order['price']
        if order['type'] == 'V':
            order['profit']  = (current_price - price) * order['quantity']
            order['percent'] =  ((current_price / price) - 1) * 100
        elif order['type'] == 'V':
            order['profit']  = (price - current_price) * order['quantity']
            order['percent'] =  ((price / current_price) - 1) * 100   



if __name__ == '__main__':
    init_curses()