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

    plt.grid(axis='y', color='b', linestyle=':', linewidth=1)

    # Here is the bar plot that we use as background
    max_dc = df.max()
    bars = ax.bar(middles, max_dc, width=big_angle*np.pi/180*2,
                  bottom=0, color='white', edgecolor='lightgray', zorder=0)
    print(artist.getp(bars))
    ax.set_yscale('sqrt')


months = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin', 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
big_angle = 360/12

fig = plt.figure()
ax = plt.subplot(111, polar=True)
line,  = ax.plot([], [])

dress_axes(ax)

title = ax.text(x=0, y=0, s='', size=25, color='gray')

t = mdates.date2num(df.index.to_pydatetime())
tnorm = (t-t.min())/(t.max()-t.min())*2.*np.pi*30
ax.fill_between(tnorm, df ,0, alpha=0.2)

def init():
    line.set_data([], [])
    return line, 

def animate(i):
    year = df.index[i].year
    month = df.index[i].month
    title.set_text(f'{months[month-1]} {year}')
    title.set_ha('center')
    
    datay = df[:i]
    if i > 365:
        datay[:i-365] = 0
    line.set_data(tnorm[:i], datay)

    return line,title

ani = animation.FuncAnimation(fig, animate, init_func=init, frames=len(tnorm), blit=True, interval=15, repeat=False)
plt.show()
