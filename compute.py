import pandas as pd

df = pd.read_csv('df.csv')

df['new_column'] = df.WARD * df.SECTION

df.to_csv('df_csv')

print('Data modified.')