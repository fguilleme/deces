# data source https://www.data.gouv.fr/en/datasets/fichier-des-personnes-decedees/
from io import StringIO
import pandas as pd
import numpy as np
import datetime
from struct import unpack
import os
import hashlib
import requests

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
        'https://www.data.gouv.fr/fr/datasets/r/9bc3b4b0-faf1-49cd-bd1f-feb5bec303bd',  # 2021 - m1
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

