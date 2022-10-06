import threading
import logging
import time
import mybinance
from datetime import datetime
import json
import os.path
from depth__class import DepthClass
#import recordlib as recordlib
from walls__class import Wall, WallsList, WallsDb
from copy import deepcopy


class FindWalls:
    threadLock = threading.Lock()
    logger = 0

    def __init__(self, walls_list, min_wall_amount=50000, delay=60, depth_limit=500, volume_loader=None, save_file=None, tickers=None):
        self.tickers = tickers
        self.volume_loader = volume_loader
        self.results_path = save_file
        self.walls_list = walls_list
        self.min_wall_amount = min_wall_amount
        self.delay = delay
        self.depth_limit = depth_limit

    def update_walls(self, ticker, depth):
        for i in list(self.walls_list.walls.keys()):
            if i not in self.walls_list.walls.keys():
                continue
            wall = self.walls_list.walls[i]
            if wall.ticker == ticker:
                hour_volume = self.volume_loader.get_volume(wall.ticker)
                is_updated = wall.update_and_filter_wall(depth, hour_volume)
                if not is_updated:
                    if i not in self.walls_list.walls.keys():
                        continue
                    del self.walls_list.walls[i]

    def finder(self, ticker):
        old_depth = None
        while True:
            depth = mybinance.get_depth_data(ticker, limit=self.depth_limit)
            if not depth:
                continue
            self.update_walls(ticker, depth)
            if old_depth is not None:
                sorted_depth_delta = DepthClass.get_sorted_depth_delta(old_depth.data, depth.data)
                for order in (x for x in sorted_depth_delta if x[1]['delta'] > self.min_wall_amount):
                    source_order = list(order)
                    order = {'ticker': ticker,
                             'price': order[0],
                             'total_volume': depth.data[order[0]][0],
                             'volume': order[1]['delta'],
                             'side': order[1]['side']}
                    walls_prices = list([x.price for x in list(self.walls_list.get_walls())])
                    if order['price'] not in walls_prices:
                        difference_with_max = depth.difference_from_second_maximum(float(order['price']), min(order['volume'], order['total_volume']))
                        hour_volume = self.volume_loader.get_volume(ticker)
                        wall = Wall(**{**order,
                                       'current_price': depth.price,
                                       'medium_amount': depth.get_medium_amount(),
                                       'difference_with_max': difference_with_max,
                                       'hour_volume': hour_volume,
                                       'history': [[datetime.now().strftime('%Y-%m-%d %H:%M:%S'), *source_order]],
                                       'last_updated': time.time(),
                                       'created': time.time()
                                       })
                        self.walls_list.add_wall(deepcopy(wall))
            old_depth = depth
            time.sleep(self.delay)

    def start(self):

        for ticker in self.tickers:
            logging.info(ticker + ' thread started')
            thread = threading.Thread(target=self.finder, args=(ticker,), daemon=True)
            thread.start()
            time.sleep(0.5)
