from walls__class import WallsList, Wall, WallsDb
import time
from hour_volume_loader import HourVolumeLoader
from findwalls import FindWalls
import threading
from trader import Trader
from telegram_bot import TelegramBot
from trader__class import BinanceTrader
import log_settings


with open("private.txt", "r") as token_file:
    txt = token_file.read()
    TG_TOKEN = txt.split(' ')[0]
    API_KEY = txt.split(' ')[1]
    SECRET = txt.split(' ')[2]
    print(TG_TOKEN)
    print(API_KEY)
    print(SECRET)


walls_list = WallsList()
walls_db = WallsDb(walls_list, save_file='data/walls.json', saving_delay=60)

walls_db.load_from_file()
walls_db.start_saving()

tgbot = TelegramBot(token=TG_TOKEN)
binance_trader = BinanceTrader(api=API_KEY, secret=SECRET)

with open('data/coins.txt') as f:
    lines = [line.rstrip('\n') for line in f]
tickers = [x.strip() for x in lines]
volume_loader = HourVolumeLoader(save_file='data/hour_volume.json', tickers=tickers)

find_walls = FindWalls(walls_list, tickers=tickers, min_wall_amount=50000, delay=60, depth_limit=500, volume_loader=volume_loader, save_file='data/walls.json')
thread = threading.Thread(target=find_walls.start, args=(), daemon=True)
thread.start()

recorders = {}
trader = Trader(walls_list=walls_list, recorders=recorders, tgbot=tgbot, binance=binance_trader, volume_loader=volume_loader)
#thread = threading.Thread(target=trader.start_checking, args=(), daemon=True)
#thread.start()

trader.start_checking()

time.sleep(1500)