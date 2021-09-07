
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

    try:
        
        print_header(stdscr)
        stdscr.refresh()
        stdscr.clrtobot()

        wallet.load_simulation_file('./history/BTCUSDT - 5m - 1629331201 - 1629935999')

        while(not wallet.end):
            # time.sleep(0.1)

            wallet.update_price()
            wallet.update_orders()
            wallet.check_new_candle()
            wallet.check_tp()
            wallet.check_end()
            

            print_price(stdscr, wallet.old_price, wallet.current_price)
            print_datetime(stdscr, wallet.get_date())
            print_orders(stdscr, wallet.order_list)
            print_ema(stdscr, wallet.ema5[-2], wallet.ema20[-2], wallet.trend)
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

    rows, cols = stdscr.getmaxyx()

    for i in range(0, rows):
        stdscr.addstr(i, 40, ' ' * (cols - 41))

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



    

def print_ema(stdscr, ema5, ema20, trend):
    stdscr.addstr(8, 0, "EMA 21 : {:.2f}".format(ema5))
    stdscr.addstr(9, 0, "EMA 55 : {:.2f}".format(ema20))
    if trend == 'up':
        stdscr.addstr(8, 20, "↑", curses.color_pair(2))
    else:
        stdscr.addstr(8, 20, "↓", curses.color_pair(1))

def print_budget(stdscr, budget):
    stdscr.addstr(11, 0, "Budget : {:.2f}".format(budget))

def print_datetime(stdsrc, date):
    stdsrc.addstr(7, 0, date)

if __name__ == '__main__':
    init_curses()