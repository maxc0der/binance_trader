import json
import time
import drawer
import telegram_bot
from walls__class import Wall
from flask import Flask, request, jsonify


app = Flask(__name__)


@app.route('/query')
def query():
    print(request.args.get('test'))
    answer = ''
    result = dict()
    for json_item in json.load(open('data/walls.json', 'r')):
        wall = Wall(**json_item)

        filters = [
            wall.life > 0,
            wall.eating_time >= 1,
            wall.volume > wall.medium_amount,
            wall.left_to_level < 0.01,
            wall.volume_left > 0.5,
            wall.difference_with_max > 0.5
        ]

        if all(filters):
            if wall.ticker not in result.keys():
                result[wall.ticker] = list()
            result[wall.ticker].append(wall)
            answer = answer + '<br>' + wall.json(filter=['ticker', 'price', 'volume', 'volume_left', 'left_to_level', 'life', 'eating_time'])
    return answer


app.run(host='0.0.0.0', port=80)




"""
        charts_data = drawer.load_charts_data(i.ticker, depth_limit=100)
        text = recordlib.Recorder.create_caption(i, charts_data)
        drawer.create_charts(filename='images/TEST/test.png', **charts_data, level=float(i.price), text=text)
        #print(telegram_bot.alert_wall(i, charts_data))
        telegram_bot.bot.send_photo(5471506567, open('images/TEST/test.png', 'rb'),
                                    caption=telegram_bot.alert_wall(i, charts_data), parse_mode='HTML')
"""

print(len(result))

