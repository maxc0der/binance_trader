import dataclasses
from dataclasses import dataclass
from depth__class import DepthClass
import time
from datetime import datetime
import json
from collections import OrderedDict
import logging
import os
import threading


@dataclass
class Wall:
    ticker: str
    price: str
    total_volume: float
    volume: float
    side: str
    current_price: float
    medium_amount: float
    difference_with_max: float
    hour_volume: float
    last_updated: float
    created: float
    futures_price: float = None
    canceled: bool = False
    order: dict[str, int] = None
    volume_left: float = None
    left_to_level: float = None
    eating_time: float = None
    life: float = None
    id: int = None
    history: list = None

    def __post_init__(self):
        self.calc_others()

    def calc_others(self):
        self.volume_left = self.total_volume / self.volume
        self.left_to_level = abs(float(self.price) - self.current_price) / self.current_price
        self.eating_time = round(min(self.volume, self.total_volume) / self.hour_volume * 60) if self.hour_volume != 0 else 0
        self.life = round((time.time() - self.created) / 60)
        self.last_updated = time.time()

    def json_object(self, filter=None):
        view = OrderedDict()
        view.update({'id': self.id})
        filter = self.__dict__.keys() if filter is None else filter
        for key, value in self.__dict__.items():
            if key != 'id' and key in filter:
                view.update({key: value})
        return view

    def json(self, filter=None):
        return json.dumps(self.json_object(filter), indent=4)

    def update(self, depth, medium_amount, difference_with_max, hour_volume, last_price=None):
        self.total_volume = float(depth.data[self.price][0])
        if last_price is not None:
            self.current_price = last_price
        else:
            self.current_price = depth.price
        self.medium_amount = medium_amount
        self.hour_volume = hour_volume
        self.last_updated = time.time()
        self.difference_with_max = difference_with_max
        if self.history is not None:
            #self.history.append([datetime.now().strftime('%Y-%m-%d %H:%M:%S'), *depth.data[self.price]])
            self.history = None
        else:
            pass
            #self.history = [[datetime.now().strftime('%Y-%m-%d %H:%M:%S'), *depth.data[self.price]]]
        self.calc_others()

    def update_and_filter_wall(self, depth, hour_volume, last_price=None):
        if self.price in depth.data.keys():
            difference_with_max = depth.difference_from_second_maximum(float(self.price), min(self.volume, self.total_volume))
            self.update(depth, depth.get_medium_amount(), difference_with_max, hour_volume, last_price=last_price)
            if self.volume_left < 0.3 or self.side != depth.data[self.price][1]:
                return False
            else:
                return True
        else:
            return False


class WallsList:
    def __init__(self):
        self.walls = dict()
        self.counter = 0

    def get_walls(self):
        return self.walls.values()

    def add_wall(self, wall):
        wall.id = self.counter
        self.counter = self.counter + 1
        self.walls.update({wall.id:wall})

    def remove_wall(self, wall):
        del self.walls[wall.id]

    def show(self):
        for wall in self.walls.values():
            print(wall.__dict__)

    def json(self, filter=None):
        for wall in self.walls.values():
                print(wall.json(filter=filter))


class WallsDb:
    def __init__(self, walls_list, saving_delay=60, save_file='walls.json', filter=None):
        self.filter = filter
        self.walls_list = walls_list
        self.saving_delay = saving_delay
        self.save_file = save_file

    def save_to_file(self, filter=None):
        if len(self.walls_list.get_walls()) > 0:
            with open(self.save_file, 'w') as f:
                json.dump([x.json_object(filter=filter) for x in list(self.walls_list.get_walls())], f, indent=4)
            logging.info(str(len(self.walls_list.get_walls())) + ' walls was saved to file ' + self.save_file)
        else:
            logging.warning('Nothing to save ' + self.save_file)

    def saving_loop(self, filter=None):
        while True:
            self.save_to_file(filter)
            time.sleep(self.saving_delay)

    def start_saving(self):
        thread = threading.Thread(target=self.saving_loop, kwargs={'filter': self.filter}, daemon=True)
        thread.start()

    def load_from_file(self):
        if os.path.exists(self.save_file):
            with open(self.save_file) as f:
                json_items = json.load(f)
                for json_item in json_items:
                    if 'recorder' in json_item:
                        del json_item['recorder']
                    self.walls_list.add_wall(Wall(**json_item))
            logging.info(str(len(json_items)) + ' walls was loaded from file ' + self.save_file)
        else:
            logging.warning('File not exists: ' + self.save_file)
