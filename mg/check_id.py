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
from .utils import get_item_id
pandas.io.formats.excel.ExcelFormatter.header_style = None

BASE_URL = "https://www.dkmg.ru"
USER_AGENT = UserAgent()
headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "user-agent": USER_AGENT.random
}

semaphore = asyncio.Semaphore(2)
df = pd.read_excel('compare/gvardia_new_stock.xlsx', converters={'id': str})
df = df.where(df.notnull(), None)
sample = df.to_dict('records')
count = 1


async def get_item_data(session, item):
    if not item['id']:
        item_id = await get_item_id(session, item)
        if item_id:
            item['id'] = item_id



async def get_gather_data():

    tasks = []
    async with (aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False, limit_per_host=10, limit=50),
                                      timeout=aiohttp.ClientTimeout(total=None)) as session):
        for item in sample:
            if not item['id']:
                task = asyncio.create_task(get_item_data(session, item))
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
