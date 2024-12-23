import os
import time

import pandas.io.formats.excel
from bs4 import BeautifulSoup as bs
from pprint import pprint
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

df_price_one = pd.read_excel("one.xlsx", converters={"Артикул": str}).set_index('Артикул').to_dict('index')
df_price_two = pd.read_excel("two.xlsx", converters={"Артикул": str}).set_index('Артикул').to_dict('index')
df_price_three = pd.read_excel("three.xlsx", converters={"Артикул": str}).set_index('Артикул').to_dict('index')
sample = pd.read_excel("abc.xlsx", converters={"Артикул": str}).set_index('Артикул').to_dict('index')
not_in_sale = pd.read_excel("not_in_sale.xlsx", converters={"Артикул": str}).set_index('Артикул').to_dict('index')

result = []
id_to_add = []
id_to_del = []

semaphore = asyncio.Semaphore(10)

count = 1
async def get_item_data(session, link, main_category=None):
    global count
    if not link.startswith('https'):
        link = BASE_URL + link
    global semaphore
    # try:
    item_data = {}
    async with semaphore:
        async with session.get(link, headers=headers) as response:
            soup = bs(await response.text(), "lxml")

            if not main_category:
                main_category = soup.find('div', class_='way').find_all('a')[2].text.strip()
            item_data["Категория"] = main_category

            try:
                title = soup.find("h1").text.strip()
                item_data["Названия"] = title
            except:
                item_data["Названия"] = 'Нет названия'
            try:
                options = soup.find('div', class_="item_basket_cont").find_all("tr")
                for option in options:
                    item_data[option.find_all("td")[0].text.strip()] = option.find_all("td")[1].text.strip()
                    if option.find_all("td")[0].text.strip() == "ISBN:":
                        isbn = option.find_all("td")[1].text.strip()
                try:
                    additional_options = soup.find('div', class_="additional_information").find_all('tr')
                    for option in additional_options:
                        item_data[option.find_all("td")[0].text.strip()] = option.find_all("td")[1].text.strip()
                except:
                    pass
            except:
                item_data["Характеристика"] = 'Характиристики не указаны'
            try:
                info = soup.find("div", class_='content_sm_2').find('h4')
                if info.text.strip() == 'Аннотация':
                    info = info.find_next().text.strip()
                else:
                    info = 'Описание отсутствует'
                item_data["Описание"] = info
            except:
                item_data["Описание"] = 'Описание отсутствует'
            try:
                price = soup.find_all("div", class_="product_item_price")[1].text.strip().split('.')[0]
                item_data["Цена"] = price
            except:
                item_data["Цена"] = 'Цена не указана'

            item_id = soup.find('a', class_='btn_red wish_list_btn add_to_cart')
            if item_id:
                item_id = item_id['data-tovar']

            item_data['id'] = item_id
            try:
                quantity = soup.find("div", class_="wish_list_poz").text.strip()
                item_data["Наличие"] = quantity
            except:
                item_data["Наличие"] = 'Наличие не указано'
            try:
                photo = soup.find("a", class_="highslide")['href']
                item_data["Фото"] = BASE_URL + photo
            except:
                item_data["Фото"] = 'Нет изображения'

            if isbn + '.0' in not_in_sale:
                not_in_sale[isbn + '.0']['В продаже'] = 'да'
            elif isbn + '.0' not in sample and quantity == 'есть в наличии':
                id_to_add.append(item_data)
            elif isbn + '.0' in sample and quantity != 'есть в наличии':
                id_to_del.append({'Артикул': f'{isbn}.0'})

            if isbn + '.0' in df_price_one:
                df_price_one[isbn + '.0']['Цена'] = price
            if isbn + '.0' in df_price_two:
                df_price_two[isbn + '.0']['Цена'] = price
            if isbn + '.0' in df_price_three:
                df_price_three[isbn + '.0']['Цена'] = price
            result.append(item_data)
            print(f'\r{count}', end='')
            count += 1

async def get_gather_data():

    async with (aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session):

        with open('error.txt') as file:
            item_links = [item.split(' ----- ')[0] for item in file.readlines()]
        print(len(item_links))
        print('----------------------------')
        os.remove('error.txt')
        reparse_tasks = []
        for link in item_links:
            task = asyncio.create_task(get_item_data(session, link))
            reparse_tasks.append(task)
        await asyncio.gather(*reparse_tasks)


def main():
    asyncio.run(get_gather_data())
    df = pd.DataFrame(result)
    df.to_excel('re_result.xlsx', index=False)

    df_add = pd.DataFrame(id_to_add)
    df_add.to_excel('re_add.xlsx', index=False)

    df_del = pd.DataFrame(id_to_del)
    df_del.to_excel('re_del.xlsx', index=False)

    df_one = pd.DataFrame().from_dict(df_price_one, orient='index')
    df_one.index.name = 'Артикул'
    df_one.to_excel('re_price_one.xlsx')

    df_two = pd.DataFrame().from_dict(df_price_two, orient='index')
    df_two.index.name = 'Артикул'
    df_two.to_excel('re_price_two.xlsx')

    df_three = pd.DataFrame().from_dict(df_price_three, orient='index')
    df_three.index.name = 'Артикул'
    df_three.to_excel('re_price_three.xlsx')

    df_not_in_sale = pd.DataFrame().from_dict(not_in_sale, orient='index')
    df_not_in_sale.index.name = 'Артикул'
    df_not_in_sale.to_excel('re_not_in_sale.xlsx')


if __name__ == "__main__":
    start_time = time.time()
    main()
    pprint(time.time() - start_time)
