from binance.um_futures import UMFutures
from binance.helpers import round_step_size
from dataclasses import dataclass
from binance.enums import *
import json
from datetime import datetime
import time

API = 'lECjMwD4en6x7vn6UHnjWqnMVcgMpUHdcXIIyaCY3tW7fIQPHLBjLi8zOjDJgDa9'


@dataclass
class Precision:
    qty: float
    price: float


class BinanceTrader:
    def __init__(self, api=None, secret=None):
        self.client = UMFutures(api, secret)
        self.acc_info = None
        self.exchage_info = self.client.exchange_info()

    def open_order(self, params):
        try:
            return self.client.new_order(**params)
        except Exception as e:
            return {'error': e}

    def get_precision(self, ticker):
        qty = [x['quantityPrecision'] for x in self.exchage_info['symbols'] if x['symbol'] == ticker][0]
        price = [x['filters'][0]['tickSize'] for x in self.exchage_info['symbols'] if x['symbol'] == ticker][0]
        return Precision(qty, price)

    def open_position(self, ticker, side, side_stop, price, high, low, stop, take):
        qty_precision = self.get_precision(ticker).qty
        price_precision = self.get_precision(ticker).price
        #price_futures = float([x['markPrice'] for x in self.client.mark_price() if x['symbol'] == ticker][0])
        amount = 500

        price = round_step_size(price, price_precision)
        qty = round(amount / price, qty_precision)
        high_price = round_step_size(high['price'], price_precision)
        low_price = round_step_size(low['price'], price_precision)
        params = {'symbol': ticker, 'side': side, 'type': 'LIMIT', 'quantity': qty, 'price': price, 'timeInForce': 'GTC'}
        params1 = {'symbol': ticker, 'side': side_stop, 'type': high['type'], 'closePosition': 'true', 'stopPrice': high_price}
        params2 = {'symbol': ticker, 'side': side_stop, 'type': low['type'], 'closePosition': 'true', 'stopPrice': low_price}

        order1 = self.open_order(params)
        order2 = self.open_order(params1)
        order3 = self.open_order(params2)

        if all(['error' not in x for x in [order1, order2, order3]]):
            return True
        else:
            self.close_position(ticker)
            return str(order1) + '\n' + str(order2) + '\n' + str(order3)

    def close_position(self, ticker):
        client = self.client
        if self.acc_info is None: return False
        for position in self.acc_info['positions']:
            if position['symbol'] == ticker:
                position['positionAmt'] = float(position['positionAmt'])
                if float(position['positionAmt']) != 0:
                    close_side = 'SELL' if position['positionAmt'] > 0 else 'BUY'
                    params = {'symbol': ticker, 'side': close_side, 'type': 'MARKET',
                              'quantity': abs(position['positionAmt']), 'reduceOnly': 'true'}
                    response = self.client.new_order(**params)
                    print(response)
                break
        print(client.cancel_open_orders(symbol=ticker, recvWindow=2000))

    def view_open_positions(self):
        if self.acc_info is None: return False
        for position in self.acc_info['positions']:
            if float(position['positionAmt']) != 0:
                print({'ticker': position['symbol'], 'amt': str(position['positionAmt']),
                       'price': str(position['entryPrice']), 'pnl': str(position['unrealizedProfit'])})

    def view_balance(self):
      #  print('totalWalletBalance: ' + self.acc_info['totalWalletBalance'])
        print('totalMarginBalance: ' + self.acc_info['totalMarginBalance'])

    def update_acc_info(self):
        self.acc_info = self.client.account(recvWindow=6000)

    def view_orders_income(self):
        orders = self.client.get_income_history()
        baz = dict()
        for order in orders:
            #order['date'] = datetime.utcfromtimestamp(int(order['time'] / 1000) + 3 * 3600).strftime( '%Y-%m-%d %H:%M:%S')
            #date = order['date']
            date = order['time']
            if date in baz:
                if order['incomeType'] in baz[date]:
                    baz[date][order['incomeType']] = baz[date][order['incomeType']] + float(order['income'])
                else:
                    baz[date].update({'symbol': order['symbol'], order['incomeType']: float(order['income'])})
            else:
                baz.update({date: {'symbol': order['symbol'], order['incomeType']: float(order['income'])}})
        print(json.dumps(baz, indent=4))

    def view_order_income(self, ticker, date):
        orders = self.client.get_income_history()
        result = dict()
        result['ticker'] = ticker
        result['date_start'] = datetime.utcfromtimestamp(int(date) + 3*3600).strftime('%Y-%m-%d %H:%M:%S')
        result['date_end'] = datetime.utcfromtimestamp(time.time() + 3*3600).strftime('%Y-%m-%d %H:%M:%S')
        for order in orders:
            if int(order['time']) >= int(date) and order['symbol'] == ticker:
                income_type = order['incomeType'].lower()
                if income_type in result:
                    result[income_type] = round(result[income_type] + float(order['income']), 2)
                else:
                    result[income_type] = round(float(order['income']), 2)
        result['total_fee'] = 0
        if 'funding_fee' in result: result['total_fee'] = round(result['total_fee'] + result['funding_fee'], 2)
        if 'commission' in result: result['total_fee'] = round(result['total_fee'] + result['commission'], 2)
        result['clear_pnl'] = round(result['realized_pnl'] + result['total_fee'], 2)
        print(json.dumps(result, indent=4))
        return(result)


with open("private.txt", "r") as token_file:
    txt = token_file.read()
    TG_TOKEN = txt.split(' ')[0]
    API_KEY = txt.split(' ')[1]
    SECRET = txt.split(' ')[2]
    print(TG_TOKEN)
    print(API_KEY)
    print(SECRET)

binance_trader = BinanceTrader(api=API_KEY,
                               secret=SECRET)

#print(float(binance_trader.client.historical_trades(symbol="BTCUSDT", limit=1)[0]['price']))

#while True:
binance_trader.update_acc_info()
binance_trader.view_balance()
binance_trader.view_open_positions()
#    time.sleep(10)
binance_trader.view_orders_income()
#binance_trader.view_order_income('THETAUSDT', 1664495717 + 3 * 3600)
#binance_trader.view_orders_income()




#params1 = {'symbol': 'BTCUSDT', 'side': 'BUY', 'type': 'LIMIT', 'quantity': 0.001, 'price': 15000, 'timeInForce': 'GTC'}
#print(binance_trader.open_order(params1))
print(binance_trader.close_position('ETCUSDT'))

