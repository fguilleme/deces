import pandas as pd
import numpy as np

import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import scale as mscale
from matplotlib import transforms as mtransforms
import matplotlib.dates as mdates

from struct import unpack
import os

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

df = df[df.index.year >= 2000]

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


def configure_axes(ax):
    ax.set_facecolor('w')
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)

    # Here is how we position the months labels
    middles = np.arange(big_angle/2, 360, big_angle)*np.pi/180
    ax.set_xticks(middles)
    ax.set_xticklabels(months)

    plt.grid(None, axis='x')
    plt.grid(axis='y', color='lightgray', linestyle=':', lw=2, alpha=0.5)

    max_dc = df.max()
    b = [int(max_dc), 0] * 6
    bars = ax.bar(middles, b, width=big_angle*np.pi/180,
                  bottom=max_dc//4, color='lightgray', edgecolor='gray', alpha=0.2, zorder=0)
    ax.set_yscale('sqrt')


months = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin', 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
big_angle = 360/12

fig = plt.figure()
ax = plt.subplot(111, polar=True)
empty = [], []
empty *= (maxy-miny+1)
lines  = ax.plot(*empty, lw=1)

configure_axes(ax)

title = ax.text(x=0, y=0, s='', size=25, color='gray')
marker, = ax.plot([], [], color='black', marker='o')

t = mdates.date2num(df.index.to_pydatetime())
tnorm = (t-t.min())/(t.max()-t.min())*2.*np.pi*(maxy-miny+1)
ax.fill_between(tnorm, df, 0, alpha=0.2)

class AnimationController:
    def __init__(self, miny, speed=1):
        self.colors = ['red', 'blue', 'green', 'magenta', 'navy', 'brown', 'black'] * 10
        self.favorite = { 2003: {'speed': 1, 'color': 'red', 'lw': 1.5, 'alpha': 1},
                          2020: {'speed': 1, 'color': 'magenta', 'lw': 1.5, 'alpha': 1}}
        self.speed = speed
        self.start = {}
        self.miny = miny
        self.top = miny
        self.stopping = False
        self.record = []

    def get_att(self, y, att, default):
        if y in self.favorite:
            return self.favorite.get(y)[att]
        return default

    def get_speed(self, y):
        return self.get_att(y, 'speed', 2)

    def get_color(self, y):
        return self.get_att(y, 'color', self.colors[y-self.miny])

    def get_lw(self, y):
        return self.get_att(y, 'lw', 1)

    def get_alpha(self, y):
        d = self.top - y
        return self.get_att(y, 'lw', max(1.0-d*0.1, 0.1))

    def gen(self):
        counter = 0
        while not self.stopping:
            yield counter
            counter += self.speed

    def init(self):
        for i, line in enumerate(lines):
            line.set_data([], [])
        return lines

    def get_date_info(self, i, dt):
        year = dt.year
        month = dt.month
        day = i - dt.dayofyear + 1
        self.start[year] = day
        self.speed = self.get_speed(year)
        self.top = max(year, self.top)
        return year, month, year-self.miny, self.start[year]

    def animate(self, i):
        try:
            year, month, segment, start_in_segment = self.get_date_info(i, df.index[i])
        except:
            self.stopping = True
            return lines+[title, marker]
        self.record.append(i)
        print(f"{month}/{year}                                      ", end="\r")
        title.set_text(f'{months[month-1]} {year}')
        title.set_ha('center')

        n = i+self.speed+1
        if n >= len(tnorm):
            n = len(tnorm)
        y = df[start_in_segment:n]
        x = tnorm[start_in_segment:n]

        lines[segment].set_data(x, y)
        marker.set_data(x[-1:], y[-1:])

        lines[segment].set_color(self.get_color(year))
        lines[segment].set_alpha(self.get_alpha(year))
        lines[segment].set_lw(self.get_lw(year))

        # fade old years
        for i in range(year-self.miny):
            lines[i].set_alpha(self.get_alpha(i+self.miny))

        legend = ax.legend(lines, [str(y) for y in range(self.miny, year+1)], loc='lower left')

        return lines+[title, marker, legend]

    def play(self):
        self.ani = animation.FuncAnimation(fig, self.animate, init_func=self.init, frames=self.gen, blit=True, interval=10, repeat=False)
        plt.show()

    def save(self, path):
        print('save to ', path, '...', end='')
        self.ani = animation.FuncAnimation(fig, self.animate, init_func=self.init, frames=self.record, blit=True, interval=10, repeat=False)
        self.ani.save(path)
        print('OK')

ctlr = AnimationController(miny=miny, speed=2)
ctlr.play()
ctlr.save("deces.mp4")
