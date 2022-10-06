import pandas as pd
from math import sqrt


class DepthClass:
    def __init__(self, source_data):
        self.source_data = source_data
        self.price = self.get_price()
        self.data = self.get_data()
        self.df_data = self.get_df_data()
        self.bounds = self.get_bounds()

    def get_price(self):
        try:
            current_price = (float(self.source_data['bids'][0][0]) + float(self.source_data['asks'][0][0])) / 2
        except:
            current_price = 0
        return current_price

    def get_bounds(self):
        bounds = [float(self.source_data['bids'][-1][0]), float(self.source_data['asks'][-1][0])]
        return bounds

    def get_medium_amount(self):
        s = 0
        for key, value in self.data.items():
            s = s + value[0] * value[0]
        medium_amount = s / len(self.data)
        return sqrt(medium_amount)

    def difference_from_second_maximum(self, price, volume, delta=0.005):
        max_volume = {'price': 0, 'value': 0}
        n = 0
        n_max = 0
        for key, value in self.data.items():
            if abs(float(key) - price)/price < delta and float(value[0]) > max_volume['value'] and float(key) != price:
                max_volume = {'price': key, 'value': float(value[0])}
                n_max = n
            n = n+1
        n = 0
        for key, value in self.data.items():
            if abs(n - n_max) < 10 and float(value[0]) > max_volume['value'] and float(key) != price:
                max_volume = {'price': key, 'value': float(value[0])}
        if max_volume['value'] == 0:
            return 0
        return volume/max_volume['value']

    @staticmethod
    def get_sorted_depth_delta(old_data, depth_data):
        depth_delta = {}
        sorted_depth_delta = {}
        if len(old_data) != 0:
            for i in set().union(depth_data.keys(), old_data.keys()):
                if i in old_data.keys() and i in depth_data.keys():
                    depth_delta[i] = {'delta': depth_data[i][0] - old_data[i][0], 'side': depth_data[i][1]}
                elif i not in old_data.keys():
                    depth_delta[i] = {'delta': depth_data[i][0], 'side': depth_data[i][1]}
                elif i not in depth_data.keys():
                    depth_delta[i] = {'delta': -old_data[i][0], 'side': old_data[i][1]}
            sorted_depth_delta = list(sorted(depth_delta.items(), key=lambda item: -item[1]['delta']))
        return sorted_depth_delta

    def get_data(self):
        combined_data = dict()
        for side in ['bids', 'asks']:
            combined_data = {**combined_data, **{i[0]: (float(i[1]) * self.price, side) for i in self.source_data[side]}}
        return combined_data

    def get_df_data(self):
        df_list = []
        for side in ['asks', 'bids']:
            for i in self.source_data[side]:
                i[1] = float(i[1]) * self.price
        for side in ['bids', 'asks']:
            df = pd.DataFrame(self.source_data[side], columns=["price", "quantity"], dtype=float)
            df["side"] = side
            df_list.append(df)
        return pd.concat(df_list).reset_index(drop=True)
