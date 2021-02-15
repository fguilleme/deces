import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
matplotlib.use('Agg')

import pandas as pd
import requests
from io import StringIO
import datetime

req = requests.get('https://www.data.gouv.fr/fr/datasets/r/08c18e08-6780-452d-9b8c-ae244ad529b3')
csv = pd.read_csv(StringIO(req.text), delimiter=';', parse_dates=['jour'])

REGIONS = {
    1: ["IDF", 12_213_447],
    11: ["IDF", 12_213_447],
    2: ["Centre", 2_572_853],
    24: ["Centre", 2_572_853],
    27: ["Bourgogne-Franche Comté", 2_807_807],
    28: ["Normandie", 3_499_280],
    3: ["Nord", 4_050_756],
    32: ["Nord", 6_004_108],
    4: ["Grand Est", 5_550_389],
    44: ["Grand Est", 5_550_389],
    52: ["Pays de Loire", 3_781_423],
    53: ["Bretagne", 3_335_414],
    75: ["Nouvelle Acquitaine", 5_879_778],
    76: ["Occitanie", 5_885_496],
    84: ["Auvergne", 7_994_459],
    93: ["Provence Côte d'Azur", 5_052_832],
    94: ["Corse", 338_554]
}
pop = {r:v for r,v in REGIONS.values()}
population = sum(pop.values())

print(f"Population totale = {population}")

def plot_par_region(title, col, pond=False, smooth=1):
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
        p = df.clip(0).rolling(smooth).median()\
            .plot(figsize=(18, 8), title=title+f' - {now}')
        p.yaxis.set_major_formatter(
            FuncFormatter(lambda y, _: '{:.2%}'.format(y)))
    else:
        df.clip(0).rolling(smooth).median()\
            .plot.area(stacked=True, figsize=(18, 8), title=title+f' - {now}')

dest = '/home/francois/www/francois_www/html/playground/img/'
# dest = 'www/img/'

plot_par_region("Hospitalisations par région", 'hosp')
plt.savefig(dest + 'covid-hosp-par-region.png')
plot_par_region("Hospitalisations pondérées par région", 'hosp', pond=True)
plt.savefig(dest + 'covid-hosp-par-region-pondere.png')

plot_par_region("Réanimations par région", 'rea')
plt.savefig(dest + 'covid-rea-par-region.png')
plot_par_region("Réanimations pondérées par région", 'rea', pond=True)
plt.savefig(dest + 'covid-rea-par-region-pondere.png')

plot_par_region("Décès par région", 'dc', smooth=1)
plt.savefig(dest + 'covid-deces-par-region.png')
plot_par_region("Décès pondérés par région", 'dc', pond=True, smooth=1)
plt.savefig(dest + 'covid-deces-par-region-pondere.png')

plt.show()
