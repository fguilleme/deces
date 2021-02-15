import pandas as pd
import numpy as np
import datetime

import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import scale as mscale
from matplotlib import transforms as mtransforms
import matplotlib.dates as mdates
import math
from struct import unpack
import os

import insee

df = insee.load_db()

precision = 10
df['AGEX'] = ((df['AGE']*precision).astype(int)).astype(float)/precision

df = df[['DD', 'NOM', 'AGEX']][df['DD'].dt.year > 1990]

fig = plt.figure()
ax = plt.subplot(111)
lines = ax.plot([], [])
title = ax.text(x=0, y=0, s='', size=25, color='gray')

print("align dates...", end='')
df['DDX'] = df['DD'].apply(lambda x: datetime.date(x.year, 1, 1))
print('OK')

print("Grouping...", end='')
grouped = df.groupby(['DDX', 'AGEX']).count()
dates = grouped.index.get_level_values(0).unique()
print('OK')

# grouped = grouped['NOM']/precision
ax.set_xticks(range(0, 110, 10))
m = grouped['NOM'].max()
n = int(math.pow(10, max(0, math.floor(math.log10(m))-1)))
ax.set_yticks(range(0, m, n))

def init():
    for i, line in enumerate(lines):
        line.set_data([], [])
    return lines

def animate(dt):
    title.set_text(dt.year)
    df = grouped.loc[dt]
    lines[0].set_xdata(df.index.values)
    lines[0].set_ydata(df['NOM'])
    return lines+[title]

ani = animation.FuncAnimation(fig, animate, init_func=init, frames=dates, blit=True, interval=500, repeat=False)
plt.show()
