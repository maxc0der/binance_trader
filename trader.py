import mybinance
from trader__class import BinanceTrader
from walls__class import WallsList, Wall, WallsDb
import threading
import drawer
import time
import record__class as recordlib
import logging


class Trader:
    def __init__(self, walls_list=None, recorders=None, tgbot=None, binance=None, volume_loader=None):
        self.walls_list = walls_list
        self.recorders = recorders
        self.tgbot = tgbot
        self.binance = binance
        self.volume_loader = volume_loader

    @staticmethod
    def filter(wall):
        filters = [
            wall.life >= 30,
            wall.eating_time >= 30,
            wall.volume > wall.medium_amount,
            wall.left_to_level < 0.004,
            wall.volume_left > 0.5,
            wall.difference_with_max > 2
        ]
        return all(filters)

    def start_checking(self):
        while True:
            for wall in list(self.walls_list.get_walls()):
                if self.filter(wall) or wall.id in self.recorders.keys():
                    order = self.prepare_order(wall)
                    charts_data = drawer.load_charts_data(wall.ticker, depth_limit=500, levels=drawer.create_levels(float(wall.price), order))
                    last_price = charts_data['last_price']
                    futures_price = mybinance.get_futures_price(wall.ticker)
                    hour_volume = self.volume_loader.get_volume(wall.ticker)

                    # Cancel when wall disappeared
                    if not wall.update_and_filter_wall(charts_data['depth'], hour_volume, last_price=last_price):
                        if wall.id in self.recorders.keys() and not wall.canceled:
                            self.send_tg_alert(self.tgbot, wall, order, charts_data, '❌ Wall canceled', short=True)
                            close_caption = '❌ Wall ' + wall.ticker + ' ' + str(wall.id) + ' was canceled'
                            self.close(wall, close_caption, cancel_orders=True) if not wall.canceled else None
                        continue
                    else:

                        # Open order if all is okey
                        if wall.id not in self.recorders.keys() and self.filter(wall):
                            self.recorders[wall.id] = recordlib.Recorder(wall)
                            order = self.prepare_order(wall)
                            wall.order = {'date': time.time(),
                                          'side': order['side'],
                                          'price': order['price'],
                                          'stop': order['stop'],
                                          'take': order['take'],
                                          'old_price': 0,
                                          'old_futures_price': 0,
                                          'status': 'wait'}
                            response = self.binance.open_position(wall.ticker, *self.prepare_order(wall).values())
                            if response is True:
                                self.send_tg_alert(self.tgbot, wall, order, charts_data, 'Orders Opened')
                            else:
                                self.send_tg_alert(self.tgbot, wall, order, charts_data, '❌ ' + response)
                            # self.tgbot.bot.send_message(5471506567, text, parse_mode='HTML')

                    if wall.id in self.recorders.keys() and not wall.canceled:
                        self.recorders[wall.id].take_snapshot(charts_data)
                        if wall.order['old_futures_price'] != 0:
                            if (wall.order['side'] == 'BUY' and wall.order['old_futures_price'] > futures_price
                                or wall.order['side'] == 'SELL' and wall.order['price'] < futures_price) \
                                    and wall.order['status'] == 'wait':
                                wall.order['status'] = 'filled'
                                self.send_tg_alert(self.tgbot, wall, order, charts_data, 'Limit filled ', short=True)
                                print('Limit filled ', futures_price)
                                print(wall.order)
                            if self.cross(wall.order['stop'], wall.order['old_futures_price'], futures_price):
                                if wall.order['status'] == 'filled':
                                    self.send_tg_alert(self.tgbot, wall, order, charts_data, '❌ Stop-loss', short=True)
                                    close_caption = '❌ Stop-loss ' + wall.ticker + ' ' + str(wall.id)
                                    self.close(wall, close_caption, cancel_orders=False) if not wall.canceled else None
                                    print('❌ Stop-loss ', futures_price)
                                    print(wall.order)
                                else:
                                    self.close(wall, 'Price did not reached limit-price, but stop-loss', cancel_orders=True) if not wall.canceled else None
                            if self.cross(wall.order['take'], wall.order['old_futures_price'], futures_price):
                                if wall.order['status'] == 'filled':
                                    self.send_tg_alert(self.tgbot, wall, order, charts_data, '✅ Take-profit', short=True)
                                    income_caption = self.tgbot.alert_income(self.binance.view_order_income(wall.ticker, wall.order['date']))
                                    close_caption = self.tgbot.alert_wall(wall, charts_data, description='✅ Take-profit \n \n') + '\n\n' + income_caption
                                    self.close(wall, close_caption, cancel_orders=False) if not wall.canceled else None
                                    print('✅ Take-profit ', futures_price)
                                    print(wall.order)
                                else:
                                    self.close(wall, 'Price did not reached limit-price, but take-profit', cancel_orders=True) if not wall.canceled else None
                        else:
                            pass
                        if wall.order is not None: wall.order['old_futures_price'] = futures_price
                        if wall.order is not None: wall.order['old_price'] = last_price
            time.sleep(5)

    @staticmethod
    def send_tg_alert(tgbot, wall, order, charts_data, description, short=False):
        text = recordlib.Recorder.create_caption(wall, charts_data)
        levels = drawer.create_levels(float(wall.price), order)
        drawer.create_charts(filename='images/TEST/test.png', **charts_data, levels=levels, text=text)
        tgbot.bot.send_photo(-1001800435114, open('images/TEST/test.png', 'rb'), caption=tgbot.alert_wall(wall, charts_data, description=description, short=short), parse_mode='HTML')

    def close(self, wall, caption, cancel_orders=False, send_video=True):
        wall.canceled = True
        self.binance.close_position(wall.ticker) if cancel_orders else None
        if self.recorders[wall.id].counter > 20 and send_video:
            video_name = self.recorders[wall.id].render_video()
            self.tgbot.send_video(video_name, caption)
            if wall.id in self.recorders.keys():
                del self.recorders[wall.id]
        wall.order = None
        wall.canceled = False

    def view(self):
        for wall in list(self.walls_list.get_walls()):
            if self.filter(wall):
                logging.info(wall.json())

    @staticmethod
    def prepare_order(wall):
        if wall.side == 'asks':
            side, side_stop = 'SELL', 'BUY'
            price = float(wall.price) * (1 - 0.002)
            high = {'type': 'STOP_MARKET', 'price': float(wall.price) * (1 + 0.003)}
            low = {'type': 'TAKE_PROFIT_MARKET', 'price': float(wall.price) * (1 - 0.007)}
            stop, take = high['price'], low['price']
        else:
            side, side_stop = 'BUY', 'SELL'
            price = float(wall.price) * (1 + 0.002)
            high = {'type': 'TAKE_PROFIT_MARKET', 'price': float(wall.price) * (1 + 0.007)}
            low = {'type': 'STOP_MARKET', 'price': float(wall.price) * (1 - 0.003)}
            stop, take = low['price'], high['price']
        return {'side': side, 'side_stop': side_stop, 'price': price, 'high': high, 'low': low, 'stop': stop, 'take': take}

    @staticmethod
    def cross(targ, x1, x2):
        if (x2 < targ < x1) or (x1 < targ < x2):
            return True
        else:
            return False