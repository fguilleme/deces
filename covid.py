import pandas as pd
import matplotlib.pyplot as plt
import requests
from io import StringIO

def group_cols(df, cols, gn):
    s = df[cols[0]]
    for c in cols[1:]:
        s = s + df[c]
    df[gn] = s
    return df.drop(columns=cols)

def filter(csv, col):
    dropped = ['dc', 'rad', 'rea', 'hosp']
    dropped.remove(col)
    temp = csv[csv['reg'] != 0].groupby(['jour', 'reg', 'cl_age90']).\
        sum().\
        drop(columns=dropped).\
        unstack('cl_age90').\
        groupby('jour').\
        sum()
    temp.columns = [x for _, x in temp.columns]
    temp = group_cols(temp, [9, 19, 29, 39, 49], 0)
    temp = group_cols(temp, [89, 90], 99)
    temp = temp.reindex(sorted(temp.columns), axis=1)
    temp.columns = ['Moins de 50 ans', '50 à 59 ans',
                    '60 à 69 ans', '70 à 79 ans', 'plus de 80 ans']
    return temp

req = requests.get('https://www.data.gouv.fr/fr/datasets/r/08c18e08-6780-452d-9b8c-ae244ad529b3')
csv = pd.read_csv(StringIO(req.text), delimiter=';', parse_dates=['jour'])

filter(csv, 'hosp').plot.area(figsize=(18, 6), title='Hospitalisations', grid=True)
filter(csv, 'rea').plot.area(figsize=(18, 6), title='Occupation réa', grid=True)
# deaths is a cumulative sum so we need to apply a diff (we also smooth on 5 days)
filter(csv, 'dc').diff().rolling(5).mean().clip(0).plot.area( figsize=(18, 6), title='Décès', grid=True)

# temp = csv.groupby(['jour', 'cl_age90']).sum().drop(columns=['reg', 'rad']).unstack(
#     'cl_age90').sum().unstack('cl_age90')
# temp.T.plot.bar(figsize=(18, 7), stacked=True)

plt.show()
