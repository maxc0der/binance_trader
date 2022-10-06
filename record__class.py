import os
import moviepy.video.io.ImageSequenceClip
import shutil
import time
import threading
import drawer
import queue
import json
import logging


class Recorder:

    q = queue.Queue()

    def __init__(self, wall, fps=5):
        self.fps = fps
        self.wall = wall
        self.images = []
        name = self.wall.ticker + '_' + str(self.wall.id)
        self.img_folder = 'images' + '/' + name
        self.video_name = 'video' + '/' + name + '.mp4'
        self.counter = 0
        if not os.path.exists(self.img_folder):
            os.mkdir(self.img_folder, 0o666)

    def take_snapshot(self, charts_data):
        self.counter = self.counter + 1
        img_name = self.img_folder + '/' + str(self.counter) + '.png'
        levels = drawer.create_levels(float(self.wall.price), self.wall.order)
        Recorder.q.put({'filename': img_name,
                        **charts_data,
                        'text': Recorder.create_caption(self.wall, charts_data),
                        'levels': levels})
        logging.info('Capture in queue for ' + self.wall.ticker + ', saved to ' + img_name + ' [queue: ' + str(Recorder.q.qsize()) + ']')

    def render_video(self):
        print('Creating video ', self.video_name)
        if os.path.exists(self.img_folder):
            image_files = [os.path.join(self.img_folder, img) for img in os.listdir(self.img_folder) if img.endswith(".png")]
            image_files.sort(key=lambda s: int(s.partition('\\')[-1].partition('.')[0]))
            clip = moviepy.video.io.ImageSequenceClip.ImageSequenceClip(image_files, fps=self.fps)
            clip.write_videofile(self.video_name)
            shutil.rmtree(self.img_folder)
        return self.video_name

    @staticmethod
    def queue_processing():
        while True:
            while not Recorder.q.empty():
                drawer.create_charts(**Recorder.q.get())
            time.sleep(1)

    @staticmethod
    def create_caption(wall, charts_data):
        text_items = {'ticker': wall.ticker,
                      'level': wall.price + ' (' + str(round(abs(float(wall.price) - charts_data['last_price']) / charts_data['last_price'] * 1000) / 10) + ' %)',
                      'amount': str(round(wall.total_volume / 1000)) + 'K/' + str(round(wall.volume / 1000)) + 'K (' + str(round(wall.volume_left * 100)) + ' %) ',
                      'life': str(wall.life),
                      'eating': str(wall.eating_time),
                      'updated': str(round(time.time() - wall.last_updated))
                      }
        text = ' '.join(x[0] + ': ' + x[1] for x in text_items.items())
        return text


thread = threading.Thread(target=Recorder.queue_processing, args=(), daemon=True)
thread.start()




