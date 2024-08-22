import os.path
import time

import numpy as np
import pandas.io.formats.excel
from bs4 import BeautifulSoup as bs
from pprint import pprint
from fake_useragent import UserAgent
import aiohttp
import asyncio
import pandas as pd

from utils import get_item_id

pandas.io.formats.excel.ExcelFormatter.header_style = None

BASE_URL = "https://www.dkmg.ru"
USER_AGENT = UserAgent()
headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "user-agent": USER_AGENT.random
}

df = pd.read_excel('gv_result.xlsx', converters={'article': str})
df = df.replace({np.nan: None})
sample = df.set_index('article').to_dict('index')


async def get_item_data(session, link):
    try:
        async with session.get(BASE_URL + link, headers=headers) as response:
            soup = bs(await response.text(), "lxml")
            buy_btn = soup.find('a', class_='btn_red wish_list_btn add_to_cart')
            option_div = soup.find('div', class_="item_basket_cont")
            isbn = 'isbn'
            if option_div:
                options = option_div.find_all("tr")
                for option in options:
                    if option.find_all("td")[0].text.strip() == "ISBN:":
                        isbn = option.find_all("td")[1].text.strip()
            if isbn + '.0' in sample:
                if buy_btn:
                    sample[isbn + '.0']['stock'] = 2
                else:
                    sample[isbn + '.0']['stock'] = 'del'
    except:
        with open('compare_error.txt', 'a+', encoding='utf-8') as f:
            f.write(f'{link}\n')


async def get_item_list(session, cat_list):
    tasks = []
    for cat_link in cat_list:

        response = await session.get(BASE_URL + cat_link[0], headers=headers)
        response_text = await response.text()
        soup = bs(response_text, 'lxml')
        pagin_max = int(soup.find("div", class_="navitem").find_all("a")[-2]['href'].split('=')[-1])
        pagin_min = 1
        if len(cat_link) > 1:
            pagin_min = int(cat_link[1])
        main_category = soup.find("h1").text.split(' (')[0]
        print(f'\n---Делаю категорию - {main_category}---')

        for page_numb in range(pagin_min, pagin_max + 1):
            print(f'----------------стр - {page_numb} из {pagin_max}-----------')
            try:
                response = await session.get(f'{BASE_URL}{cat_link[0]}?page={page_numb}')
                await asyncio.sleep(5)
                response_text = await response.text()
                soup = bs(response_text, 'lxml')
                items_on_page = soup.find_all('div', class_='product_img')
                items_links = [item.find('a')['href'] for item in items_on_page]
                for link in items_links:
                    task = asyncio.create_task(get_item_data(session, link))
                    tasks.append(task)
            except Exception:
                with open('cat_error.txt', 'a+') as f:
                    f.write(f'{cat_link} --- {page_numb}\n')
                    continue
    return tasks


async def check_empty_stock(session, item):
    item_id = sample[item]['id']
    try:
        if not item_id:
            item_id = await get_item_id(session, item)
        if item_id and item_id != '#':
            sample[item]['id'] = item_id
            link = f'/tovar/{item_id}'
            await get_item_data(session, link)
        else:
            sample[item]['stock'] = 'del'
    except Exception as e:
        with open('check_empty_error.txt', 'a+') as f:
            f.write(f'{item} --- {item_id} --- {e}')
            sample[item]['stock'] = 'del'



async def get_gather_data():
    async with (aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False, limit_per_host=10)) as session):
        response = await session.get(BASE_URL, headers=headers)
        response_text = await response.text()
        soup = bs(response_text, "lxml")
        cat_list = soup.find_all("h4")
        cat_list = [(item.find('a')['href'],) for item in cat_list[:8]]
        tasks = await get_item_list(session, cat_list)

        await asyncio.gather(*tasks)

        print('+++++ Start parse empty stock +++++')
        await asyncio.sleep(300)
        empty_stock_tasks = []
        for item in sample:
            if not sample[item]['stock']:
                task = asyncio.create_task(check_empty_stock(session, item))
                empty_stock_tasks.append(task)
        print(f'+++ {len(empty_stock_tasks)} empty stock tasks ++++')

        await asyncio.gather(*empty_stock_tasks)

        print('+++++ Start parse item error +++++')
        reparse_count = 0

        while os.path.exists('compare_error.txt') and reparse_count < 7:
            await asyncio.sleep(100)
            with open('compare_error.txt', encoding='utf-8') as file:
                reparse_item = file.readlines()
            os.remove('compare_error.txt')
            new_tasks = [asyncio.create_task(get_item_data(session, i)) for i in reparse_item]
            await asyncio.gather(*new_tasks)

        print('+++++ Start parse category stock +++++')
        reparse_count = 0

        while os.path.exists('cat_error.txt') and reparse_count < 7:
            await asyncio.sleep(300)
            with open('cat_error.txt', encoding='utf-8') as file:
                reparse_cat_list = [(reparse_line.split(' --- ')[0], reparse_line.split(' --- ')[1].strip())
                                    for reparse_line in file.readlines()]
            os.remove('cat_error.txt')
            tasks = await get_item_list(session, reparse_cat_list)
            await asyncio.gather(*tasks)


def main():
    asyncio.run(get_gather_data())
    df_one = pd.DataFrame().from_dict(sample, orient='index')
    df_one.index.name = 'article'
    df_one.to_excel('gv_result.xlsx')


if __name__ == "__main__":
    start_time = time.time()
    main()
    print()
    pprint(time.time() - start_time)
