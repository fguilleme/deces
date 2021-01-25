import pandas as pd
import numpy as np

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.path as mpath
import matplotlib.artist as artist
import matplotlib.animation as animation
from matplotlib import scale as mscale
from matplotlib import transforms as mtransforms
import matplotlib.dates as mdates


import datetime
from struct import unpack
import os
import time
import math

HDF_NAME = 'dat/1991-2020-count.hdf'
if os.path.exists(HDF_NAME):
    print('reading compressed...')
    df = pd.read_hdf(HDF_NAME, 'test')
    print('done')
else:
    HDF_NAME = 'dat/1991_2020.hdf'
    if os.path.exists(HDF_NAME):
        print('reading compressed...')
        df = pd.read_hdf(HDF_NAME, 'test')
        print('counting...')
        df = df.groupby('DD').count()['NOM']
        df = df[df.index.year > 1990]
        print('writing...')
        df.to_hdf('dat/1991-2020-count.hdf', 'test', format='fixed', mode='w', complib='lzo', complevel=3)
df

df = df[df.index.year >= 2010]

miny = df.index.min().year
maxy = df.index.max().year
print(miny, maxy)

# custom scaler to plot polar graphs
class sqrtScale(mscale.ScaleBase):
    name = 'sqrt'

    def __init__(self, axis, **kwargs):
        mscale.ScaleBase.__init__(self, axis)
        self.thresh = None #thresh

    def get_transform(self):
        return self.CustomTransform(self.thresh)

    def set_default_locators_and_formatters(self, axis):
        pass

    class CustomTransform(mtransforms.Transform):
        input_dims = 1
        output_dims = 1
        is_separable = True

        def __init__(self, thresh):
            mtransforms.Transform.__init__(self)
            self.thresh = thresh

        def transform_non_affine(self, a):
            return np.sqrt(a)

        def inverted(self):
            return sqrtScale.InvertedCustomTransform(self.thresh)

    class InvertedCustomTransform(mtransforms.Transform):
        input_dims = 1
        output_dims = 1
        is_separable = True

        def __init__(self, thresh):
            mtransforms.Transform.__init__(self)
            self.thresh = thresh

        def transform_non_affine(self, a):
            return a*a

        def inverted(self):
            return sqrtScale.CustomTransform(self.thresh)

mscale.register_scale(sqrtScale)


def dress_axes(ax):
    ax.set_facecolor('w')
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    # Here is how we position the months labels

    middles = np.arange(big_angle/2, 360, big_angle)*np.pi/180
    ax.set_xticks(middles)
    ax.set_xticklabels(months)

    # ax.set_rlabel_position(359)
    # ax.tick_params(axis='x', color='b')
    # plt.grid(None, axis='x')

    # plt.grid(axis='y', color='b', linestyle=':', linewidth=1)
    # plt.grid(axis='x', color='b', linestyle=':', linewidth=1)
    plt.grid(None, axis='x')
    plt.grid(None, axis='y')

    # Here is the bar plot that we use as background
    max_dc = df.max()
    # bars = ax.bar(middles, max_dc, width=big_angle*np.pi/180*2,
    #               bottom=0, color='white', edgecolor='lightgray', zorder=0)
    # print(artist.getp(bars))
    # ax.set_yscale('sqrt')


months = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin', 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
big_angle = 360/12

fig = plt.figure()
ax = plt.subplot(111, polar=True)
empty = [], []
empty *= (maxy-miny+1)
lines  = ax.plot(*empty)

dress_axes(ax)

title = ax.text(x=0, y=0, s='', size=25, color='gray')
marker, = ax.plot([], [], color='black', marker='o')

t = mdates.date2num(df.index.to_pydatetime())
tnorm = (t-t.min())/(t.max()-t.min())*2.*np.pi*(maxy-miny+1)
ax.fill_between(tnorm, df ,0, alpha=0.2)

def init():
    colors = ['red', 'blue', 'green', 'magenta', 'cyan', 'brown', 'black']
    for i, line in enumerate(lines):
        line.set_data([], [])
        line.set_color(colors[i % len(colors)])
    return lines

def animate(i):
    i *= 2
    year = df.index[i].year
    month = df.index[i].month
    title.set_text(f'{months[month-1]} {year}')
    title.set_ha('center')

    segment = year-miny
    start_in_segment = segment*365
    y = df[start_in_segment:i]
    x = tnorm[start_in_segment:i]
    lines[segment].set_data(x, y)

    if len(x) > 0:
        marker.set_data([x[-1]], [y[-1]])

    for y in range(miny, year-1):
        lines[y-miny].set_alpha(0.5)
        lines[y-miny].set_label(str(y))
    for y in range(miny, miny+(year-miny-1)//2):
        lines[y-miny].set_alpha(0.3)
    legend = ax.legend(lines, [str(y) for y in range(
        miny, year+1)], loc='lower left')
    return lines+[title, marker, legend]

ani = animation.FuncAnimation(fig, animate, init_func=init, frames=len(tnorm)//2, blit=True, interval=15, repeat=False)
plt.show()
print('anim done')
ani.save("deces.mp4")
print('saving done')
