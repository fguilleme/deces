import datetime
from labellines import labelLine, labelLines
import matplotlib
from matplotlib.dates import date2num
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
matplotlib.use('Agg')

import pandas as pd
import requests
from io import StringIO

req = requests.get('https://www.data.gouv.fr/fr/datasets/r/08c18e08-6780-452d-9b8c-ae244ad529b3')
csv = pd.read_csv(StringIO(req.text), delimiter=';', parse_dates=['jour'])

REGIONS = {
    1: ["Guadeloupe", 387_629],
    2: ["Martinique", 368_783],
    3: ["Guyane", 276_128],
    4: ["La Réunion", 859_959],
    6: ["Mayotte", 256_518],

    11: ["IDF", 12_213_447],
    24: ["Centre VdL", 2_572_853],
    27: ["BFC", 2_807_807],
    28: ["Normandie", 3_499_280],
    32: ["Hauts de F", 6_004_108],
    44: ["Est", 5_550_389],
    52: ["Loire", 3_781_423],
    53: ["Bretagne", 3_335_414],
    75: ["Nouv Acq", 5_879_778],
    76: ["Occitanie", 5_885_496],
    84: ["Auvergne", 7_994_459],
    93: ["PACA", 5_052_832],
    94: ["Corse", 338_554]
}
pop = {r:v for r,v in REGIONS.values()}
population = sum(pop.values())

print(f"Population totale = {population}")

def plot_par_region(title, col, pond=False, smooth=1, inline=False):
    dropped = ['dc', 'rad', 'rea', 'hosp', 'cl_age90']
    dropped.remove(col)
    df = csv[csv['cl_age90'] == 0]\
        .drop(columns=dropped)\
        .groupby(['jour', 'reg'])\
        .sum()\
        .unstack('reg')\
        .stack(level=0)

    # group and rename the columns
    df = df.groupby({k: v[0] for k, v in REGIONS.items()}, axis=1).sum()
    if pond:
        for c in df.columns:
            df[c] = df[c].divide(pop.get(c, 1))

    s = df.sum()
    if col == 'dc':
        df = df.diff()
    df = df[s.sort_values(ascending=False).index]
    df.index = df.index.get_level_values(0)
    now= datetime.datetime.today().strftime("%d/%m/%Y %H:%M")
    if pond:
        p = df.clip(0).rolling(smooth).mean()\
            .plot(figsize=(18, 8), title=title+f' - {now}')
        p.yaxis.set_major_formatter(
            FuncFormatter(lambda y, _: '{:.2%}'.format(y)))
        if inline:
            xvals = [

                date2num(datetime.date(2020, 4, 15)),   # IDF
                date2num(datetime.date(2020, 4, 15)),   # Est 
                date2num(datetime.date(2021, 2, 15)),   # PACA 
                date2num(datetime.date(2021,  1, 1)),   # BFC 
                date2num(datetime.date(2020, 11, 15)),  # Auvergne 
                date2num(datetime.date(2020, 4, 15)),   # Nord 
                date2num(datetime.date(2020, 12, 15)),  # Centre 
                date2num(datetime.date(2021, 2, 15)),   # Normandie 
                date2num(datetime.date(2020, 7, 15)),   # Guyane 
                date2num(datetime.date(2021, 2, 1)),   # Occitanie
                date2num(datetime.date(2021, 1, 1)),    # Loire 
                date2num(datetime.date(2020, 10, 15)),   # Guadeloupe
                date2num(datetime.date(2021, 1, 1)),   # Corse 
                date2num(datetime.date(2020, 11, 15)),   # Sud Ouest 
                date2num(datetime.date(2020, 11, 15)),  # Mayotte
                date2num(datetime.date(2020, 12, 15)),   # Bretagne
                date2num(datetime.date(2020, 4, 15)),   # Martinique
                date2num(datetime.date(2021,  1, 1)),   # La Réunion
                ]
            if col == 'dc':
                xvals = None
            labelLines(plt.gca().get_lines(), xvals=xvals, align=False, fontsize=12)
    else:
        df.clip(0).rolling(smooth).mean()\
            .plot.area(stacked=True, figsize=(18, 8), title=title+f' - {now}')

dest = '/home/francois/www/francois_www/html/playground/img/'
dest = 'www/img/'

plot_par_region("Hospitalisations par région", 'hosp')
plt.savefig(dest + 'covid-hosp-par-region.png')
plot_par_region("Hospitalisations par région relatifs à la population ",
                'hosp', pond=True, inline=True)
plt.savefig(dest + 'covid-hosp-par-region-pondere.png')

plot_par_region("Réanimations par région", 'rea')
plt.savefig(dest + 'covid-rea-par-region.png')
plot_par_region("Réanimations par région relatifs à la population ", 'rea', pond=True, inline=True)
plt.savefig(dest + 'covid-rea-par-region-pondere.png')

smooth = 3
plot_par_region(f"Décès par région - Lissage {smooth}j ", 'dc', smooth=smooth)
plt.savefig(dest + 'covid-deces-par-region.png')
plot_par_region(f"Décès par région relatifs à la population - Lissage {smooth}j ", 'dc', pond=True, smooth=smooth, inline=True)
plt.savefig(dest + 'covid-deces-par-region-pondere.png')

plt.show()
