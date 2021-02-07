import insee

db = insee.load_db()

base = 'dat'
db=db[db['DD'].dt.year >= 1991]
db=db.groupby([db['DD'].dt.date, 'GENRE']).count()['NOM'].unstack('GENRE')
db['TOTAL']=db[1]+db[2]
db.rename(columns={1:'HOMME', 2: 'FEMME'}, inplace=True)
db.to_csv(f'{base}/deces.csv', sep=';')