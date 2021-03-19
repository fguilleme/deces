import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Agg')
import pandas as pd
import requests
from io import StringIO
import datetime

req = requests.get('https://www.data.gouv.fr/fr/datasets/r/08c18e08-6780-452d-9b8c-ae244ad529b3')
csv = pd.read_csv(StringIO(req.text), delimiter=';', parse_dates=['jour'])

def filter(col):
    dropped = ['dc', 'rad', 'rea', 'hosp', 'HospConv', 'SSR_USLD', 'autres']
    dropped.remove(col)
    return csv[csv['cl_age90'] > 0]\
        .drop(columns=dropped)\
        .groupby(['jour',  'cl_age90', 'reg'])\
        .sum()\
        .unstack('reg')\
        .sum(axis=1)\
        .unstack('cl_age90')\
        .groupby({9:0, 19:0, 29:0, 39:0, 49:0, 59:1, 69:2, 79:3, 89:4, 90:4}, axis=1).sum()\
        .rename(columns={1: '50 à 59 ans', 2: '60 à 69 ans', 3: '70 à 79 ans', 0: 'Moins de 50 ans', 4: 'Plus de 80 ans'})

dest = '/home/francois/www/francois_www/html/playground/img/'
# dest = 'www/img/'

now= datetime.datetime.today().strftime("%d/%m/%Y %H:%M")
filter('hosp').plot.area(figsize=(18, 6), title=f'Hospitalisations - {now}', grid=True)
plt.savefig(dest + 'covid-hosp-par-age.png')

filter('rea').plot.area(figsize=(18, 6), title=f'Occupation réa - {now}', grid=True)
plt.savefig(dest + 'covid-rea-par-age.png')

# deaths is a cumulative sum so we need to apply a diff (we also smooth on 10 days)
smooth = 3
filter('dc').diff().rolling(smooth).median().clip(0).plot.area( figsize=(18, 6), title=f'Décès lissé sur {smooth}j- {now}', grid=True)
plt.savefig(dest + 'covid-deces-par-age.png')

# temp = csv.groupby(['jour', 'cl_age90']).sum().drop(columns=['reg', 'rad']).unstack(
#     'cl_age90').sum().unstack('cl_age90')
# temp.T.plot.bar(figsize=(18, 7), stacked=True)

plt.show()
