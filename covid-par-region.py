import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Agg')

import pandas as pd
import requests
from io import StringIO

req = requests.get('https://www.data.gouv.fr/fr/datasets/r/08c18e08-6780-452d-9b8c-ae244ad529b3')
csv = pd.read_csv(StringIO(req.text), delimiter=';', parse_dates=['jour'])

REGIONS = {
    1: ["NA", 12_213_447],
    11: ["IDF", 12_213_447],
    2: ["NA", 2_572_853],
    24: ["Centre-Val de Loire", 2_572_853],
    27: ["Bourgogne-Franche Comté", 2_807_807],
    28: ["Normandie", 3_499_280],
    3: ["NA", 4_050_756],
    32: ["Hauts de France", 6_004_108],
    4: ["NA", 5_550_389],
    44: ["Grand Est", 5_550_389],
    52: ["Pays de Loire", 3_781_423],
    53: ["Bretagne", 3_335_414],
    75: ["Nouvelle Acquitaine", 5_879_778],
    76: ["Occitanie", 5_885_496],
    84: ["Auvergne", 7_994_459],
    93: ["Provence Côte d'Azur", 5_052_832],
    94: ["Corse", 338_554]
}

reg = pd.DataFrame(REGIONS, index=['nom','population']).T
population = reg.population.sum()
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

    if pond:
        for c in df.columns:
            try:
                pop = reg.population[reg.nom==c].values[0]
            except:
                pop=1000000
                #print(df.tail(1))
            df[c] = df[c].divide(pop).multiply(population)

    # group and rename the columns
    df = df.groupby({k: v[0] for k, v in REGIONS.items()}, axis=1).sum()
    s = df.sum()
    if col == 'dc':
        df = df.diff()
    df = df[s.sort_values(ascending=False).index]
    df.clip(0).rolling(smooth).median()\
        .plot.area(stacked=True, figsize=(18, 8))

dest = '/home/francois/www/francois_www/html/playground/img/'

plot_par_region("Hospitalisations", 'hosp')
plt.savefig(dest + 'covid-hosp-par-region.png')
plot_par_region("Hospitalisations", 'hosp', pond=True)
plt.savefig(dest + 'covid-hosp-par-region-pondere.png')

plot_par_region("Réanimations", 'rea')
plt.savefig(dest + 'covid-rea-par-region.png')
plot_par_region("Réanimations", 'rea', pond=True)
plt.savefig(dest + 'covid-rea-par-region-pondere.png')

plot_par_region("Décès", 'dc', smooth=1)
plt.savefig(dest + 'covid-deces-par-region.png')
plot_par_region("Décès", 'dc', pond=True, smooth=1)
plt.savefig(dest + 'covid-deces-par-region-pondere.png')

plt.show()
