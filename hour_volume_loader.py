import mybinance
import threading
import os
import json
import time
import logging


class HourVolumeLoader:
    volumes = {'updated': 0, 'data': dict()}
    logger = 0

    def __init__(self, save_file='data/hour_volume.json', tickers=None):
        self.tickers = tickers
        self.results_path = save_file
        logging.info('Started')
        if self.load_from_file():
            logging.info('Data loaded from file')
        else:
            logging.warning('File not exists: ' + self.results_path)
        thread = threading.Thread(target=self.start_updater, args=(), daemon=True)
        thread.start()

        if __name__ == "__main__":
            logging.info('Launched as main *')
            thread.join()
        else:
            logging.info('Launched not as main, deamon thread *')

    def load_from_file(self):
        if os.path.exists(self.results_path):
            with open(self.results_path) as f:
                self.volumes = json.load(f)
                return True
        else:
            return False

    def check_relevance(self):
        if time.time() - self.volumes['updated'] > 3600:
            logging.info('Relevance_check: Need update')
            return False
        else:
            logging.info('Relevance_check: Data is fresh')
            return True

    def save_to_file(self):
        with open(self.results_path, 'w') as f:
            json.dump(self.volumes, f, indent=4)
            logging.debug('Data saved to file ' + self.results_path)

    def update(self):
        self.volumes['updated'] = time.time()
        for ticker in self.tickers:
            candles = mybinance.get_candles(ticker, limit=60)
            volume = 0
            for candle in candles:
                volume = volume + float(candle[7])
            self.volumes['data'][ticker] = volume
            time.sleep(1)
        logging.info('All tickers volume\'s loaded')
        return True

    def get_volume(self, ticker):
        if ticker in self.volumes['data']:
            return self.volumes['data'][ticker]
        else:
            return 0

    def start_updater(self):
        while True:
            if not self.check_relevance():
                self.update()
                self.save_to_file()
            time.sleep(600)
