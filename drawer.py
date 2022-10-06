from matplotlib import pyplot as plt, dates
plt.switch_backend('agg')
import matplotlib.ticker as plticker
import seaborn as sns
import numpy as np
import mplfinance as mplf
from datetime import datetime
import mybinance
import pandas as pd
import time
import os


def plt_init():
    plt.rcParams['figure.figsize'] = [16, 12]
    plt.rcParams['figure.dpi'] = 300
    plt.rcParams['ytick.right'] = plt.rcParams['ytick.labelright'] = True
    plt.rcParams['ytick.left'] = plt.rcParams['ytick.labelleft'] = False
    plt.rcParams.update({'font.size': 10})
    plt.rcParams.update({'figure.max_open_warning': 0})


def max_quantity(data):
    return data.sort_values(by='quantity', ascending=False).head(1)


def draw_depth(data, ax, bounds):
    for label in (ax.get_xticklabels() + ax.get_yticklabels()):
        label.set_fontsize(16)
    ax.set_xlabel("Quantity", fontsize=16)
    #sns.histplot(y="price", weights="quantity", bins=100,  hue="side", data=data, palette=["green", "red"], ax=ax)
    ax = sns.scatterplot(y="price", x="quantity", hue="side",  data=data, palette=["green", "red"], ax=ax, marker='o')
    sns.ecdfplot(y="price", weights="quantity", stat="count", complementary=True, data=data[data.side == 'bids'], color="green", ax=ax)
    sns.ecdfplot(y="price", weights="quantity", stat="count", data=data[data.side == 'asks'], color="red", ax=ax)
    l1 = ax.lines[0]
    l2 = ax.lines[1]
    x1 = l1.get_ydata()
    y1 = l1.get_xdata()
    x2 = l2.get_xdata()
    y2 = l2.get_ydata()
    ax.fill_between(y1, x1, color="green", step="pre", alpha=0.1)
    ax.fill_between(x2, y2, max(l2.get_ydata()), color="red",  step="pre", alpha=0.1)
    ax.fill_between(x1, y1, max(l1.get_ydata()), color="red", step="pre", alpha=0.1)
    ax.set_ylim(bounds)

    for tick in ax.get_xticklabels():
        tick.set_rotation(45)
    bounds = ax.get_ylim()
    return bounds


def draw_candles(ax, ticker, bounds):
    ax.set_xlabel("Time")
    ax.set_ylabel("Price")
    data = mybinance.get_candles_df(ticker)
    mc = mplf.make_marketcolors(up="#7FBF7F",down="#FF7F7F", edge='#6F5353', wick='black', volume='in', ohlc='#6F5353')
    s = mplf.make_mpf_style(marketcolors=mc)
    ax = mplf.plot(data.set_index('Close Time').tail(200), type='candle', style=s, volume=False, ax=ax, ylim=bounds)
    return ax


def format_time_ticks(ax_price, angle=45, format='%H:%M:%S'):
    for tick in ax_price.get_xticklabels():
        tick.set_rotation(angle)
        ax_price.xaxis.set_major_formatter(dates.DateFormatter(format))


def get_bounds(bounds1, bounds2, levels=0, margin=1):
    if levels != 0:
        level = [x['price'] for x in levels]
        if isinstance(level, list):
            #bounds = [min([bounds1[0], bounds2[0], min(level)]), max([bounds1[1], bounds2[1], max(level)])]
            bounds = [min([bounds2[0], min(level)]), max([bounds2[1], max(level)])]
        else:
            bounds = [min([bounds1[0], bounds2[0], level]), max([bounds1[1], bounds2[1], level])]
            #bounds = [min([bounds2[0], min(level)]), max([bounds2[1], max(level)])]
    else:
        bounds = [min([bounds1[0], bounds2[0]]), max([bounds1[1], bounds2[1]])]
    margin_bounds = (bounds[1] - bounds[0]) * margin
    bounds = [bounds[0] - margin_bounds, bounds[1] + margin_bounds]
    return bounds


def draw_levels(ax, ax2, levels):
        if isinstance(levels, list):
            for level in levels:
                ax.axhline(y=level['price'], color=level['color'],  linestyle=level['style'], label=level['label'])
                ax2.axhline(y=level['price'], color=level['color'], linestyle=level['style'],  label=level['label'])
        else:
            level = levels
            ax.axhline(y=level['price'], color=level['color'], linestyle=level['style'],  label=level['label'])
            ax2.axhline(y=level['price'], color=level['color'], linestyle=level['style'],  label=level['label'])
        ax.legend(loc="upper left")


def draw_recent_trades(data, ax_price, ax_volume, bounds):
    for label in (ax_price.get_xticklabels() + ax_price.get_yticklabels() + ax_volume.get_yticklabels()):
        label.set_fontsize(16)
    ax_price.set_ylabel("Price", fontsize=16)
    points, qty_data, times = list(), list(), list()

    for point in data:
        times.append(datetime.fromtimestamp(point['time']/1000))
        points.append(float(point['price']))
        qty_data.append(float(point['quoteQty']))

    ax_price.plot(times, np.array(points))
    ax_volume.stackplot(times, np.array(qty_data), color='#0000FF', alpha=0.2)
    ax_price.set_ylim(bounds)
    format_time_ticks(ax_price)


def create_levels(price, order):
    levels = list()
    levels.append({'price': price, 'color': 'black', 'style': '--', 'label': 'wall: ' + str(round(price, 6))})
    levels.append({'price': order['price'], 'color': 'blue', 'style': '-', 'label': 'limit: ' + str(round(order['price'], 6))})
    levels.append({'price': order['stop'], 'color': 'red', 'style': '--', 'label': 'stop: ' + str(round(order['stop'], 6))})
    levels.append({'price': order['take'], 'color': 'green', 'style': '--', 'label': 'take: ' + str(round(order['take'], 6))})
    return levels


def load_charts_data(ticker, depth_limit=100, recent_trades_limit=1000, levels=0):
    depth = mybinance.get_depth_data(ticker, depth_limit)
    data = mybinance.get_recent_trades(ticker, limit=recent_trades_limit)
    data_price, bounds_price, last_price = data['data'], data['bounds'], data['last_price']
    bounds = get_bounds(depth.bounds, bounds_price, levels=levels, margin=0.1)
    return {'data_price': data_price, 'depth': depth, 'bounds': bounds, 'last_price': float(last_price)}


def create_charts(filename=None, data_price=None, depth=None, bounds=None, text='Testing', levels=None, last_price=0):
    plt_init()
    fig, (ax_price, ax_depth) = plt.subplots(1, 2)
    depth_data_df = depth.df_data
    draw_depth(depth_data_df, ax_depth, bounds)
    ax_volume = ax_price.twinx()
    draw_recent_trades(data_price, ax_price, ax_volume, bounds)
    if levels is not None:
        draw_levels(ax_price, ax_depth, levels)
    fig.text(0.05, 0.9, text, fontsize=16)
    try:
        if os.path.exists(filename[0:filename.rfind('/')]):
            fig.savefig(filename, dpi=100)
    except Exception as e:
        print('Error in writing ', e)
#    plt.show()
    plt.close(fig)


#data = load_charts_data('BNBUSDT')
#create_charts('images/TEST/test.png', **data, level=float(mybinance.get_recent_trades('BNBUSDT')['last_price']))
