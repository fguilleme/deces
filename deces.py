# create few graphs from the insee deceased person database
# it grabs the data from 1991 to 2020 and stored it locally so it can be processed faster later on
# as it is a pretty big sample (17 millions persons)
T=True
import matplotlib
import matplotlib.pyplot as plt
T and matplotlib.use('Agg')

import pandas as pd
import numpy as np

import insee

# DEPRECATED
def plot_death_per_day(df, path=None):
    print("plot_death_per_day")
    smooth = 30
    df[df['DD'].dt.year >= start][['DD', 'NOM']]\
        .groupby(['DD']).count()\
        .rolling(smooth).median()\
        .rename(columns={'NOM': 'Décès/jour'})\
        .plot(figsize=(18, 7), title='Nombre de décès lissé sur 30 jours', yticks=range(0, 3000, 500))
    if path:
        plt.savefig(f'{base}/' + path)

# DEPRECATED
def plot_death_median_age(df, path=None):
    print("plot_death_median_age")
    smooth = 30
    # median death age by genre
    df[df['DD'].dt.year >= start]\
        .groupby(['DD', 'GENRE'])['AGE'].median()        \
        .unstack()        \
        .rolling(smooth)        \
        .median()        \
        .rename(columns={1: "HOMME", 2: "FEMME"})        \
        .plot(figsize=(18, 7), title='Age médian H/F lissé sur 30 jours')
    if path:
        plt.savefig(f'{base}/' + path)

def plot_per_country_birth(df, path=None):
    print("plot_per_country_birth")
    year = df['DD'].dt.year.min()
    df[df['PN'] != 'FRANCE'] \
        .groupby(['PN'])     \
        .count()['NOM']      \
        .rename(f'Pays de naissance (hors france) des personnes décédées en {year}')        \
        .sort_values(ascending=False)\
        .head(16)            \
        .plot.pie(figsize=(10, 10), title=f'Répartition des pays de naissance (hors france) en {year}')
    if path:
        plt.savefig(f'{base}/' + path)

def split_by_year(df):
    ymin = df['DD'].dt.year.min()
    ymax = df['DD'].dt.year.max()
    return {k:df[df['DD'].dt.year == k] for k in range(ymin, ymax+1)}

def plot_age_deces(df, gs, genre, path=None):
    print("plot_age_deces")
    dfs = split_by_year(df)
    ymin = min(dfs.keys())
    ymax = max(dfs.keys())
    dfs = [t[(t['AGE'] > 1) & (t['GENRE'] == genre)]
          .groupby('AGEX')
          .count()['NOM'] for t in dfs.values()]
    df = pd.concat(dfs, axis=1)
    df.columns = range(ymin, ymax+1)
    df.rolling(10).mean()\
        .plot(figsize=(18, 6), grid=True, xticks=range(5, 120, 5),\
        title=f'Age de décès {gs} de {ymin} à {ymax}')
    if path:
        plt.savefig(f'{base}/' + path)

def plot_deaths_in_year(df, agemax, path=None):
    print("plot_deaths_in_year")
    smooth = 3
    dfs = split_by_year(df)
    ymin = min(dfs.keys())
    ymax = max(dfs.keys())
    years = range(ymin, ymax+1)
    colors = ['green', 'magenta', 'blue',  'red', 'cyan', 'brown'] + ['black']
    import itertools
    colors = list(itertools.islice(
        itertools.cycle(colors), len(years)))+['black']

    if agemax is None:
        agemax = 200
        age_s = ''
    else:
        age_s = f'de moins de {agemax+1} ans '

    temp = {k: dfs[k][dfs[k]['AGEX'] <= agemax] for k in dfs.keys()}

    df = [t.groupby(t['DD'].dt.dayofyear).count()['NOM']
          for t in temp.values()]
    df = pd.concat(df, axis=1)
    df['MEAN'] = df.median(axis=1)
    df.columns = list(temp.keys())+['MEDIAN']
    ax = df.rolling(10).median().\
        plot(figsize=(24, 6), grid=True, xticks=np.cumsum([1, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]), color=colors,
             title=f'Nombre de décès journaliers de {years[0]} à {years[-1]} {age_s}lissé sur {smooth} jours', lw=2)
    ax.set_xticklabels(['JANVIER', 'FEVRIER', 'MARS', 'AVRIL', 'MAI', 'JUIN', 'JUILLET', 'AOUT', 'SEPTEMBRE',
                        'OCTOBRE', 'NOVEMBRE', 'DECEMBRE', ''], fontdict={'fontsize': 12,  'horizontalalignment': 'left'})
    ax.set_xlabel('Date de décès')
    ax.set_yticks(range(0, 3000, 500))
    if path:
        plt.savefig(f'{base}/' + path)


def plot_most_death_age(data, path=None):
    print("plot_most_death_age")
    df = data[data['DD'].dt.year >= start]
    dfh = df[df['GENRE'] == 1][['DD', 'NOM', 'AGEX']
                               ].groupby(['DD', 'AGEX']).count()
    dfh = dfh.groupby(['DD']).apply(
        lambda x: x.sort_values('NOM').idxmax()[0][1])
    dff = df[df['GENRE'] == 2][['DD', 'NOM', 'AGEX']
                               ].groupby(['DD', 'AGEX']).count()
    dff = dff.groupby(['DD']).apply(
        lambda x: x.sort_values('NOM').idxmax()[0][1])
    pd.concat([dfh, dff], axis=1).rename(columns={0: 'HOMME', 1: 'FEMME'})\
        .rolling(300).median()\
        .plot(figsize=(18, 8))
    if path:
        plt.savefig(f'{base}/' + path)

def plot_birth_year(df, path=None):
    year = df['DD'].dt.year.min()
    df = df.groupby([df['DN'].dt.year, 'GENRE'])\
        .count()['NOM']\
        .unstack('GENRE')\
        .rename(columns={1: "HOMME", 2: "FEMME"})\
        .fillna(0)

    df.plot(figsize=(18, 5), grid=True,\
            xticks=range(1900, year, 5), \
            title=f'Date de naissance pour les décès en {year}')
    if path:
        plt.savefig(f'{base}/' + path)

# ======================================================================================================================
def main():
    db = insee.load_db()
    db = db[db['DD'].dt.year < 2021]
    db['AGEX'] = ((db['AGE']*10).astype(int)).astype(float)/10

    plot_per_country_birth(db[db['DD'].dt.year == 2020], 'birth_country_2020.png')

    #plot_death_per_day(db, 'death_per_day.png')
    #plot_death_median_age(db, 'death_median_age.png')
    plot_most_death_age(db, 'most_prevalent_death_age.png')

    plot_age_deces(db[db['DD'].dt.year >= 2017], "homme", 1, 'death_age_male_2017_2020.png')
    plot_age_deces(db[db['DD'].dt.year >= 2017], "femme", 2, 'death_age_female_2017_2020.png')

    plot_age_deces(db[(db['DD'].dt.year >= 1996) & (db['DD'].dt.year < 1999)], "homme", 1, 'death_age_male_1996_1998.png')
    plot_age_deces(db[(db['DD'].dt.year >= 1996) & (db['DD'].dt.year < 1999)], "femme", 2, 'death_age_female_1996_1998.png')

    plot_deaths_in_year(db[db['DD'].dt.year >= 2017], None, 'deaths_in_2017_2020.png')
    plot_deaths_in_year(db[db['DD'].dt.year >= 2017], 70, 'deaths_in_2017_2020_below_70.png')
    plot_deaths_in_year(db[db['DD'].dt.year >= 2017], 80, 'deaths_in_2017_2020_below_80.png')

    plot_birth_year(db[db['DD'].dt.year == 2020], 'birth_year_2020.png')
    plot_birth_year(db[db['DD'].dt.year == 1996], 'birth_year_1996.png')

    T or plt.show()

base = './www/img'
start = 1991
main()
