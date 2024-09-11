import os.path
import time
import schedule
import pandas.io.formats.excel
from bs4 import BeautifulSoup as bs
from fake_useragent import UserAgent
import aiohttp
import asyncio
import pandas as pd
from email_me import send_email
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


df = pd.read_excel('compare/1.xlsx', converters={'id': str})
df = df.where(df.notnull(), None)
sample = df.to_dict('records')
count = 1
count_c = 1
finish_id = 0

async def get_item_id(session, item, semaphore):
    global count_c
    global finish_id
    isbn = item["article-dev"][:-2]
    await asyncio.sleep(2)
    try:
        async with semaphore:
            async with session.get(
                    f'https://www.dkmg.ru/ajax/ajax_search.php?term={isbn}&Catalog_ID=0&Series_ID=&Publisher_ID=&Year_Biblio=',
                    headers=ajax_headers) as response:
                await asyncio.sleep(2)
                resp = await response.json(content_type='text/html', encoding='utf-8-sig')
                item_id = resp[0]['value'].split('/')[-1].strip()
                if item_id != '#':
                    item['id'] = item_id
                    finish_id += 1
                print(f'\rОбработано - {count_c} >>> Найдено - {finish_id}', end='')
                count_c += 1
    except Exception as e:
        with open('get_item_id.txt', 'a+') as f:
            f.write(f'{isbn} --- {e}\n')






async def get_gather_data():

    tasks = []
    async with (aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False, limit_per_host=10, limit=50),
                                      timeout=aiohttp.ClientTimeout(total=None)) as session):
        semaphore = asyncio.Semaphore(2)
        for item in sample:
            if not item['id']:
                task = asyncio.create_task(get_item_id(session, item, semaphore))
                tasks.append(task)
        print(f'>>>>> {len(tasks)} <<<<<<<')

        await asyncio.gather(*tasks)

def main():
    print('start\n')
    asyncio.run(get_gather_data())
    df_result = pd.DataFrame(sample)
    df_result.to_excel('compare/gvardia_new_stock_with_id.xlsx', index=False)

if __name__ == '__main__':
    start_time = time.time()
    main()
    print()
    print(time.time() - start_time)
