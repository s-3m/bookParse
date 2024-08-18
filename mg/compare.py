import os.path
import time
from pprint import pprint

import pandas.io.formats.excel
from bs4 import BeautifulSoup as bs
from fake_useragent import UserAgent
import aiohttp
import asyncio
import pandas as pd

pandas.io.formats.excel.ExcelFormatter.header_style = None

BASE_URL = "https://www.dkmg.ru"
USER_AGENT = UserAgent()
headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "user-agent": USER_AGENT.random
}
ajax_headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "user-agent": USER_AGENT.random,
    'X-Requested-With': 'XMLHttpRequest',
}

df = pd.read_excel('gv_result.xlsx', converters={'id': str})
df = df.where(df.notnull(), None)
sample = df.to_dict('records')
count = 1


async def get_item_data(session, item):
    global count
    url = f"{BASE_URL}/tovar/{item['id']}"
    async with session.get(url, headers=headers) as response:
        soup = bs(await response.text(), 'lxml')
        buy_btn = soup.find('a', class_='btn_red wish_list_btn add_to_cart')
        if buy_btn:
            item['stock'] = 2
        else:
            item['stock'] = 'del'
        print(f'\r{count}', end='')
        count += 1


async def to_check_id(session, item):
    if not item['id']:
        isbn = item['article'][:-2]
        await asyncio.sleep(20)
        # try:
        async with session.get(
                f'https://www.dkmg.ru/ajax/ajax_search.php?term={isbn}&Catalog_ID=0&Series_ID=&Publisher_ID=&Year_Biblio=',
                headers=ajax_headers) as response:
            await asyncio.sleep(20)
            resp = await response.json(content_type='text/html', encoding='utf-8')
            item_id = resp[0]['value'].split('/')[-1].strip()
            item['id'] = item_id
        # except:
        #     item['stock'] = 'check to del'
        #     flag = True
        #     return
    # try:
    await get_item_data(session, item)
    # except TimeoutError:
    #     item['stock'] = 'check to del'
    #     flag = True


async def get_gather_data():
    # flag = False
    # loop = 1
    # while True:
    #     if not flag:
    #         if loop > 1:
    #             break
    #         loop += 1
        tasks = []
        async with (aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False, limit_per_host=10, limit=50),
                                          timeout=aiohttp.ClientTimeout(total=None)) as session):
            for item in sample:
                task = asyncio.create_task(to_check_id(session, item))
                tasks.append(task)

            await asyncio.gather(*tasks)
        # else:
        #     flag = False
        #     await asyncio.sleep(300)
        #     tasks = []
        #     async with (aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False, limit_per_host=10, limit=50),
        #                                       timeout=aiohttp.ClientTimeout(total=None)) as session):
        #         for item in sample:
        #             if item['stock'] == 'check to del':
        #                 task = asyncio.create_task(to_check_id(session, item, flag))
        #                 tasks.append(task)
        #         await asyncio.gather(*tasks)


def main():
    asyncio.run(get_gather_data())
    df_result = pd.DataFrame(sample)
    df_result.to_excel('gv_result.xlsx', index=False)


if __name__ == '__main__':
    start_time = time.time()
    main()
    print()
    print(time.time() - start_time)
