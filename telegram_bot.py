import telebot



class TelegramBot:

    def __init__(self, token=None):
        self.bot = telebot.TeleBot(token)

    def send_video(self, path, caption):
        self.bot.send_video(chat_id=-1001800435114, video=open(path, 'rb'), caption=caption, supports_streaming=True)

    def send_message(self, text):
        self.bot.send_message(-1001800435114, text, parse_mode='HTML')

    @staticmethod
    def return_str_time(time):
        if time < 60:
            time = str(time) + 'm'
        else:
            time = str(time // 60) + 'h ' + str(time - (time // 60)*60) + 'm'
        return time

    @staticmethod
    def alert_wall(wall, charts_data, description='', short=False):
        if short:
            text_items = {'type': description}
        else:
            text_items = {'type': description,
                          '💵 Цена уровня': wall.price + ' (' + str(round(abs(float(wall.price) - charts_data['last_price']) / charts_data['last_price'] * 1000) / 10) + ' %)',
                          '⏰ Время жизни': TelegramBot.return_str_time(wall.life),
                          '🪚 Проедание': TelegramBot.return_str_time(wall.eating_time),
                          '📶 Объём':  str(round(wall.total_volume // 1000)) + ' K / ' + str(round(wall.volume // 1000)) + ' K' + ' (' + str(round(wall.volume_left*100)) + ' %)',
                          'Больше средних': str(round(wall.volume/wall.medium_amount*10)/10),
                          'Больше максиамльных': str(round(wall.difference_with_max*10)/10)
                          }
        text = '<b>' + wall.ticker + ' ' + str(wall.id) + '</b>\n' + '\n'.join(x[0] + ': ' + x[1] for x in text_items.items())
        return text

    @staticmethod
    def alert_income(json_obj):
        text = ''
        for key, value in json_obj.items():
            text = text + key + ': ' + str(value) + '\n'
        return text