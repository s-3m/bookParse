import os.path
import time
from concurrent.futures import ThreadPoolExecutor
from pprint import pprint

from fake_useragent import UserAgent
from bs4 import BeautifulSoup as bs
import aiohttp
import asyncio
import pandas as pd
import datetime
import json
import requests
from republik.utils import get_selenium_page

BASE_URL = "https://www.respublica.ru"
USER_AGENT = UserAgent()
headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "user-agent": USER_AGENT.random
}
result = []
item_counter = 1


def get_item_data(item):
    global item_counter
    print(item_counter)
    item_text_page = get_selenium_page(item)

    try:
        item_data = {}
        # response = await session.get("https://www.respublica.ru"+link, headers=headers)
        soup = bs(item_text_page[0], "lxml")
        try:
            category = soup.find_all('li', class_='breadcrumbs-item')[1].text
        except:
            category = 'Нет категории'
        item_data['Категория'] = category.strip()

        try:
            img = soup.find('meta', {'itemprop': 'image'}).attrs['content']
        except:
            img = 'Нет изображения'
        item_data['Изображение'] = img

        try:
            title = soup.find('h1').text
        except:
            title = None
        item_data['Название'] = title.strip()

        try:
            price = soup.find('meta', {'itemprop': 'price'}).attrs['content']
        except:
            price = None
        item_data['Цена'] = price.strip()

        try:
            description = soup.find('div', class_='static-body').text.strip()
        except:
            description = 'Нет описания'
        item_data['Описание'] = description

        try:
            articul = soup.find('h1').find_next('div').text.split(':')[1].strip()
        except:
            articul = 'Нет артикула'
        item_data['Артикул'] = articul
        try:
            full_data = {**item_data, **item_text_page[1]}
            api = f'https://api.respublica.ru/api/v1/items/get/{articul}/delivery_points?query='
            response = requests.get(api, headers=headers)
            api_dict: list[dict] = json.loads(response.text)['points']['pickup']
            for i in api_dict:
                full_data[i['address']] = i['available']
            result.append(full_data)
        except:
            pass
            result.append(item_data)
        item_counter += 1
    except Exception as e:
        with open('error.txt', 'a+') as file:
            file.write(f'Что-то пошло не так с {item}\n{e}')


async def get_thread(unique_items_links):
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(get_item_data, item) for item in unique_items_links]
        result_future = [f.result() for f in futures if f.result() is not None]
    for i in result_future:
        result.append(i)


async def get_gather_data():
    counter = 1
    async with aiohttp.ClientSession() as session:
        response = await session.get(BASE_URL + '/knigi', headers=headers)
        soup = bs(await response.text(), "lxml")
        page_count = soup.find('ul', class_='pages').find_all('a')[-2].text.strip()
        tasks = []
        for page in range(1, int(page_count) + 1):

            if page <= 2:
                print(f'Делаю {counter} страницу')
                response = await session.get(f'{BASE_URL}/knigi?page={page}', headers=headers)
                soup = bs(await response.text(), "lxml")
                all_page_items = soup.find('main', class_='right').find_all("div", class_='relative mb-5')

                items_links = [i.find('a')['href'] for i in all_page_items]
                unique_items_links = set(items_links)

                task = asyncio.create_task(get_thread(list(unique_items_links)[:11]))
                tasks.append(task)
                counter += 1

        await asyncio.gather(*tasks)

        # pprint(unique_items_links)
        # pprint(len(unique_items_links))


def main():
    start = time.time()
    asyncio.run(get_gather_data())
    df = pd.DataFrame(result)
    print(time.time() - start)
    df.to_excel('result.xlsx', index=False)


if __name__ == '__main__':
    main()
