import os.path
from pprint import pprint

from fake_useragent import UserAgent
from bs4 import BeautifulSoup as bs
import aiohttp
import asyncio
import pandas as pd
import datetime

from utils import save_img

BASE_URL = "https://tss.ru"
USER_AGENT = UserAgent()
headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "user-agent": USER_AGENT.random
}
CATALOG_TYPE = '&CATALOG_DISPLAY_TYPE=table'
result = []


async def get_item_data(session, item_link):
    try:
        response = await session.get(BASE_URL + item_link, headers=headers)
        response_text = await response.text()
        soup = bs(response_text, 'lxml')
        item_data = {}
        try:
            title = soup.find('h1', {'itemprop': 'name'}).text.strip()
        except:
            title = 'Наименование отсутствует'
        item_data['Наименование'] = title
        try:
            price = soup.find('span', class_='new-price').text.split('руб.')[0].strip()
        except:
            price = 'Цена не указана'
        item_data['Цена'] = price
        try:
            description = soup.find('span', attrs={'itemprop': 'description'}).text.strip()
        except:
            description = 'Нет описания'
        item_data['Описание'] = description
        try:
            th = soup.find('table', class_='table-data-sheet').find_all('tr')
            item_data['Общие характеристики'] = {}
            for row in th:
                row_data = row.find_all('td')
                item_data['Общие характеристики'][row_data[0].text.strip()] = row_data[1].text.strip()
        except:
            item_data['Общие характеристики'] = 'Характеристики отсутствуют'
        try:
            article = soup.find('p', id='product_reference').find('span').text.strip()
        except:
            article = 'Артикул не указан'
        item_data['Артикул'] = article
        try:
            category_list_pure = soup.find('div', class_='breadcrumb clearfix').find_all('li')
            category_list = [i.text.strip() for i in category_list_pure][2:-1]
            name_of_item = category_list_pure[-1].text.strip()
            for i in range(len(category_list)):
                item_data[f'Категория {i + 1}'] = category_list[i].strip()
            folder = '/'.join(category_list) + '/' + name_of_item
        except:
            item_data['Категория'] = 'Категория не указана'
            folder = f'/Без категории'
        os.makedirs(f'./result/{folder}', exist_ok=True)
        try:
            varantie = soup.find('div', class_='product_attributes').find('p', id='product_condition').find('span').text.strip()
        except:
            varantie = 'Гарантия не указана'
        item_data['Гарантия'] = varantie
        try:
            photo_list = [i['src'] for i in
                          soup.find('div', class_='pb-left-column col-xs-12 col-md-6 col-lg-6').find_all('img')]
            await save_img(BASE_URL, headers, session, photo_list, article, folder)

        except Exception as e:
            with open('error_save_img.txt', 'a+') as f:
                f.write(f'error with article {article}\n{e}\n')

        df = pd.DataFrame([item_data])
        df.to_json(f'./result/{folder}/{article}.json', indent=4, orient='records', force_ascii=False)
        result.append(item_data)
    except Exception as e:
        with open('error_global.txt', 'a+') as f:
            f.write(f'{BASE_URL}{item_link}\n{e}\n')


async def gather_data():
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
        response = await session.get(BASE_URL, headers=headers)
        response_text = await response.text()
        soup = bs(response_text, 'lxml')
        menu = soup.find('div', id='megamenu-row-1-1').find_all('li', class_='category')
        all_category = [li.find('a')['href'] for li in menu][:-2]

        tasks = []
        for category in all_category[:1]:
            print(f'---Категория {category}')
            page_number = 1
            pagination = True
            while pagination:
                print(f'\r---------Страница {page_number}', end='')
                response = await session.get(f'{BASE_URL}{category}&PAGEN_1={page_number}', headers=headers)
                response_text = await response.text()
                soup = bs(response_text, 'lxml')
                paginator_btn = soup.find('div', class_='bottom-pagination-content clearfix').find('a')
                # if not paginator_btn:
                #     pagination = False
                if page_number == 5:
                    pagination = False
                items = soup.find_all('a', class_='product_img_link')
                for item in items[:1]:
                    item_link = item['href']
                    task = asyncio.create_task(get_item_data(session, item_link))
                    tasks.append(task)
                page_number += 1

        await asyncio.gather(*tasks)


def main():
    asyncio.run(gather_data())
    df = pd.DataFrame(result)
    df.to_json('test.json', indent=4, orient='records', force_ascii=False)


if __name__ == '__main__':
    main()
