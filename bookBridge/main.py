import pandas as pd
from pprint import pprint

# a = pd.read_excel('One.xlsx')
#
# b = a.set_index('Артикул').to_dict('index')
# c = 0
# pprint(b)
sample = pd.read_excel("abc.xlsx", converters={"Артикул": str}).set_index('Артикул').to_dict('index')

for i in sample:
    print(sample[i])