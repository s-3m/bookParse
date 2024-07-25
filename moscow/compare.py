import aiohttp
import pandas as pd
from fake_useragent import UserAgent
from bs4 import BeautifulSoup as bs
BASE_URL = "https://www.moscowbooks.ru/"
USER_AGENT = UserAgent()
headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "user-agent": USER_AGENT.random
}

to_del = []
not_in_new_parse = []


async def request_to_del_item(item_list, result):
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), trust_env=True) as session:
        for item in item_list:
            response = await session.get(f'{BASE_URL}/book/{int(item)}', headers=headers)
            response_text = await response.text()
            soup = bs(response_text, 'lxml')
            if not soup.find('div', class_='book__buy'):
                to_del.append(item)
            else:
                need_element = soup.find_all('script')
                a = need_element[1].text.split('MbPageInfo = ')[1].replace('false', 'False').replace('true', 'True')
                need_data_dict = eval(a[:-1])['Products'][0]
                stock = need_data_dict['Stock']
                articul = item
                # item_data['Наличие'] = stock

                print(f'\r{count}', end='')
                count = count + 1

                result[articul] = {'Наличие': stock}




async def get_compare(result, df: pd.DataFrame = None):
    # parse_result = df.to_dict('index')
    # print(parse_result)
    past_day_result = pd.read_excel('pd.xlsx').set_index('Артикул').to_dict('index')
    parse_result = pd.read_excel('new_result.xlsx').set_index('Артикул').to_dict('index')

    for item in past_day_result:
        if item in parse_result:
            past_day_result[item]['Наличие'] = parse_result[item]['Наличие']
        else:
            not_in_new_parse.append(str(item))
    for i in not_in_new_parse:
        del past_day_result[float(i)]

    await request_to_del_item(not_in_new_parse, result)

    df = pd.DataFrame().from_dict(past_day_result, 'index')
    df.index.name = 'Артикул'
    df.index = df.index.astype(str)

    df.to_excel('new_stock.xlsx')
    del_df = pd.DataFrame({'Артикул': to_del})
    del_df.to_excel('del.xlsx', index=False)


get_compare()
