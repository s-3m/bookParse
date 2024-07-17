import pprint

import pandas as pd

df = pd.read_excel('One1.xlsx').set_index('Артикул').to_dict('index')
df = pd.DataFrame(df).to_dict('records')
pprint.pprint(df)
# df = pd.DataFrame(df).to_dict('list')
# pd.DataFrame(df).to_excel('One_one.xlsx')
