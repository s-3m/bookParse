import os.path
import time

from fake_useragent import UserAgent
from bs4 import BeautifulSoup as bs
import aiohttp
import asyncio
import pandas as pd
from selenium_data import get_selenium_page
import datetime
from concurrent.futures import ThreadPoolExecutor
from utils import to_write_price_dict

BASE_URL = ""
USER_AGENT = UserAgent()
headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "user-agent": USER_AGENT.random
}
count = 1
result = []


def get_item_data(item):
    global count
    res_dict = {}
    link = f'{BASE_URL}{item}'
    res_dict['Ссылка'] = link


async def get_page_data(items):
    # futures = [asyncio.to_thread(get_item_data, item, main_category) for item in items]
    # for i in futures:
    #     result.append(await i)

    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(get_item_data, item) for item in items]
        result_future = [f.result() for f in futures if f.result() is not None]
    for i in result_future:
        result.append(i)


async def get_gather_data():
    all_need_links = []

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), trust_env=True) as session:
        response = await session.get(f'{BASE_URL}/...', headers=headers)
        response_text = await response.text()
        soup = bs(response_text, "lxml")

        tasks = []

        await asyncio.gather(*tasks)


def main():
    asyncio.run(get_gather_data())
    df = pd.DataFrame(result)
    df.to_excel('result2.xlsx', index=False)


if __name__ == "__main__":
    a = time.time()
    main()
    print(time.time() - a)
