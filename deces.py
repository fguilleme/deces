# data source https://www.data.gouv.fr/en/datasets/fichier-des-personnes-decedees/
# create few graphs from the insee deceased person database
# it grabs the data from 1991 to 2020 and stored it locally so it can be processed faster later on
# as it is a pretty big sample (17 millions persons)
T=True
import matplotlib
import matplotlib.pyplot as plt
T and matplotlib.use('Agg')

from io import StringIO
import pandas as pd
import numpy as np
import datetime
from struct import unpack
import os
import sys
import hashlib
import requests
import itertools

# load the database
# it either grabs and parse it from the insee site or use a cached copy if it exists
def load_db():
    def read_fwf(path):
        # date parser as the date in insee csv is sometimes malformed
        # handle invalid dates
        def date_parser(x):
            if len(x) != 8:
                if len(x) > 4:
                    # just keep the year it should not be so bad
                    x = x[:4]+'0101'
                else:
                    x = '19000101'      # completely invalid assume 1900 person
                print(f'Invalid length "{x}"')

            y, m, d = map(int, unpack('4s2s2s', bytes(x.encode('ascii'))))

            # deal with invalid dates
            y = max(y, 1870)
            d = max(d, 1)
            m = max(min(m, 12), 1)

            if m in [4, 6, 9, 11]:
                d = min(30, d)
            elif m == 2:
                if (y % 4) == 0:
                    d = min(d, 29)
                else:
                    d = min(d, 28)
            else:
                d = min(d, 31)
            try:
                return datetime.date(y, m, d)
            except Exception as err:
                print(err, y, m, d)
                return datetime.date(y, m, d-1)

        names = ['NOM', 'GENRE', 'DN', 'CP', 'VN', 'PN', 'DD', 'CPD', 'REF']
        df = pd.read_fwf(path, widths=[80, 1, 8, 5, 30, 30, 8, 5, 9], header=None, names=names, dtype={'NOM': str, 'GENRE': int})\
            .drop(columns=['CP', 'CPD', 'REF', 'VN'])
        # date parsing while loading causes issues for 1999 so
        # we do the conversion afterward. slower but apparently safer...
        df['DN'] = pd.to_datetime(df['DN'].astype(str).apply(
            date_parser), errors='coerce')  # some date are invalid -> na
        df['DD'] = pd.to_datetime(df['DD'].astype(
            str).apply(date_parser), errors='ignore')
        # calculate the age of death
        df['AGE'] = ((df['DD']-df['DN']).dt.days/365.24)    # precise age
        # because some dates are na
        df['AGE'] = df['AGE'].fillna(0)
        df['AGEI'] = df['AGE'].round().astype(int)          # in years
        # no birth country means france
        df['PN'] = df['PN'].fillna('FRANCE')
        # return valid records with at leat a correct birth year
        return df[df['DN'].dt.year > 1850]

    # list of url to grab the data
    # it should be mostly yearly data but it does not need to
    src = [
        "https://www.data.gouv.fr/en/datasets/r/a1f09595-0e79-4300-be1a-c97964e55f05",  # 2020
        "https://www.data.gouv.fr/en/datasets/r/02acf8f5-9190-4f8e-a37c-3b34eccac833",  # 2019
        "https://www.data.gouv.fr/en/datasets/r/c2a97b38-5c0d-4f21-910f-1cea164c2c89",  # 2018
        "https://www.data.gouv.fr/en/datasets/r/fd61ff96-1e4e-450f-8648-3e3016edbe34",  # 2017
        "https://www.data.gouv.fr/en/datasets/r/8fb032c1-b81e-46c4-a48a-15380ce41e40",  # 2016
        "https://www.data.gouv.fr/en/datasets/r/22274343-816c-4220-8ca9-05ac0ff9b6f8",  # 2015
        "https://www.data.gouv.fr/en/datasets/r/9409dd78-1c54-47a4-850c-d903bb274a32",  # 2014
        "https://www.data.gouv.fr/en/datasets/r/33769f81-6507-4b0e-8f7a-f078a2c47084",  # 2013
        "https://www.data.gouv.fr/en/datasets/r/85a225fc-f0ab-4462-b8be-03981332bb98",  # 2012
        "https://www.data.gouv.fr/en/datasets/r/2581b087-003e-4b21-8175-7e7eef38c9cb",  # 2011
        "https://www.data.gouv.fr/en/datasets/r/2a7d69bd-6edf-4181-8b96-3ac4f0552ba6",  # 2010
        "https://www.data.gouv.fr/en/datasets/r/240f89af-1b80-4c48-b896-d4f4ae943d4a",  # 2009
        "https://www.data.gouv.fr/en/datasets/r/4d887ca2-af0e-4407-aa19-b7ab12077223",  # 2008
        "https://www.data.gouv.fr/en/datasets/r/7709f33d-4624-441a-bc04-bd72a28e4d08",  # 2007
        "https://www.data.gouv.fr/en/datasets/r/dd9ca2d6-21bb-40f1-a26c-9c50a3aceeef",  # 2006
        "https://www.data.gouv.fr/en/datasets/r/045bcee9-bb3c-4410-a013-f2a4183473fc",  # 2005
        "https://www.data.gouv.fr/en/datasets/r/36653f18-ae52-40c8-9c5f-6de43eeddac6",  # 2004
        "https://www.data.gouv.fr/en/datasets/r/edd5725f-2362-49b6-901f-1b43eac5824e",  # 2003
        "https://www.data.gouv.fr/en/datasets/r/8a9ff686-ae72-4cbd-b883-a9e4690c2d48",  # 2002
        "https://www.data.gouv.fr/en/datasets/r/da1c8b63-3c0f-4aa7-a244-6fed6b2e3cf8",  # 2001
        "https://www.data.gouv.fr/en/datasets/r/01bd668a-a8ba-4287-838d-3acbd3b30ba2",  # 2000
        "https://www.data.gouv.fr/en/datasets/r/47273447-cd13-42bb-8069-f4ba7327e86a",  # 1999
        "https://www.data.gouv.fr/en/datasets/r/eb86c3cf-82d4-46c3-b2ab-b17c5ae53d14",  # 1998
        "https://www.data.gouv.fr/en/datasets/r/41f13b67-0e94-4860-9bb5-d84743be4fca",  # 1997
        "https://www.data.gouv.fr/en/datasets/r/df4d19f8-cb30-414f-9f09-032f641e26af",  # 1996
        "https://www.data.gouv.fr/en/datasets/r/d2b7d1c9-d462-4821-a6b2-2a0070dc9283",  # 1995
        "https://www.data.gouv.fr/en/datasets/r/d8200490-bb80-4925-8023-9921f28797c8",  # 1994
        "https://www.data.gouv.fr/en/datasets/r/b2164c79-e2a1-48b2-af12-520a8645e3a5",  # 1993
        "https://www.data.gouv.fr/en/datasets/r/cca6afa1-a4a6-4fe1-ab37-2afea70c4708",  # 1992
        "https://www.data.gouv.fr/en/datasets/r/ac43b776-cded-41a3-a2ef-f2ecca148f61",  # 1991
    ]
    # use the md5 of the list to build the cache file name
    m = hashlib.md5()
    for x in src:
        m.update(x.encode('utf-8'))
    hash = m.hexdigest()
    path = f'dat/{hash}.hdf'
    if os.path.exists(path):
        # the cache exists
        print('reading compressed...', end='')
        data = pd.read_hdf(path, 'test')
        print('OK')
    else:
        # no cache exist for this list grab everything
        data = None
        for url in src:
            print('read', url)
            req = requests.get(url)
            temp = read_fwf(StringIO(req.text))
            if data is None:
                data = temp
            else:
                data = data.append(temp)
        print('saving...', end='')
        data.to_hdf(path, 'test', format='fixed',
                    mode='w', complib='lzo', complevel=3)
        print('OK')
    return data

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
    df = None

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
    df = None

def plot_deaths_in_year(df, agemax, path=None):
    print("plot_deaths_in_year")
    smooth = 3
    dfs = split_by_year(df)
    ymin = min(dfs.keys())
    ymax = max(dfs.keys())
    years = range(ymin, ymax+1)
    colors = ['green', 'magenta', 'blue',  'pink', 'cyan', 'red'] + ['black']
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
             title=f'Nombre de décès journaliers de {years[0]} à {years[-1]} {age_s}lissé sur {smooth} jours')
    ax.set_xticklabels(['JANVIER', 'FEVRIER', 'MARS', 'AVRIL', 'MAI', 'JUIN', 'JUILLET', 'AOUT', 'SEPTEMBRE',
                        'OCTOBRE', 'NOVEMBRE', 'DECEMBRE', ''], fontdict={'fontsize': 12,  'horizontalalignment': 'left'})
    ax.set_xlabel('Date de décès')
    ax.set_yticks(range(0, 3000, 500))
    if path:
        plt.savefig(f'{base}/' + path)
    temp = None
    df = None


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
    df = None
    dfh = None
    dff = None


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
base = './img'
db = load_db()
db['AGEX'] = ((db['AGE']*10).astype(int)).astype(float)/10

start = 1991
last = db['DD'].max().year

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

sys.exit()
