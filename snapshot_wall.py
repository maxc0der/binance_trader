import drawer
import json
from walls__class import Wall
from trader import Trader
import record__class as recordlib
import time


for json_item in json.load(open('data/walls.json', 'r')):
    wall = Wall(**json_item)

    filters = [
        wall.ticker == 'OPUSDT',
        wall.life >= 30,
        wall.eating_time >= 30,
 #       wall.volume > wall.medium_amount,
        wall.left_to_level <= 0.02,
  #      wall.volume_left > 0.5,
  #      wall.difference_with_max > 1
    ]

    if all(filters):
        levels = drawer.create_levels(float(wall.price), Trader.prepare_order(wall))
        charts_data = drawer.load_charts_data(wall.ticker, depth_limit=500, levels=levels)
        text = recordlib.Recorder.create_caption(wall, charts_data)
        print(*wall.json_object().items())
    #    drawer.create_charts(filename='images/TEST/' + str(wall.id) + '_' + wall.ticker + '.png', **charts_data, levels=levels, text=text)
        time.sleep(1)


