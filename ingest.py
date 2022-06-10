import csv
import pandas

df = pd.read_csv(https://data.cityofchicago.org/api/views/bbt9-ihrm/rows.csv?accessType=DOWNLOAD)

df.to_csv('df.csv')

print('Data ingested')