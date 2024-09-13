import os.path
import time
import re
from time import sleep

import pandas.io.formats.excel
from fake_useragent import UserAgent
from bs4 import BeautifulSoup as bs
import aiohttp
import asyncio
import pandas as pd

from selenium_data import get_selenium_page
from concurrent.futures import ThreadPoolExecutor

pandas.io.formats.excel.ExcelFormatter.header_style = None
BASE_URL = "https://bookbridge.ru"
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

count = 1
result = []

id_to_del = []
id_to_add = []


def to_write_file(filepath, temporary=False, final_result=False):
    if temporary:
        df = pd.DataFrame(result)
        df.to_excel(f'{filepath}.xlsx', index=False)
        return
    if not final_result:
        filepath = filepath + "/temporary"
    df = pd.DataFrame(result)
    df.to_excel(f'{filepath}/all_result.xlsx', index=False)

    df_one = pd.DataFrame().from_dict(df_price_one, orient='index')
    df_one.index.name = 'Артикул'
    df_one.to_excel(f'{filepath}/price_one.xlsx', index=True)

    df_two = pd.DataFrame().from_dict(df_price_two, orient='index')
    df_two.index.name = 'Артикул'
    df_two.to_excel(f'{filepath}/price_two.xlsx')

    df_three = pd.DataFrame().from_dict(df_price_three, orient='index')
    df_three.index.name = 'Артикул'
    df_three.to_excel(f'{filepath}/price_three.xlsx')

    df_not_in_sale = pd.DataFrame().from_dict(not_in_sale, orient='index')
    df_not_in_sale.index.name = 'Артикул'
    df_not_in_sale.to_excel(f'{filepath}/not_in_sale.xlsx')

    df_add = pd.DataFrame(id_to_add)
    df_add.to_excel(f"{filepath}/add.xlsx", index=False)

    df_del = pd.DataFrame(id_to_del)
    df_del.to_excel(f"{filepath}/del.xlsx", index=False)




semaphore = asyncio.Semaphore(10)

async def get_item_data(item, session, main_category=None):
    global count
    global semaphore
    res_dict = {}
    link = f'{BASE_URL}{item}'
    res_dict['Ссылка'] = link
    await asyncio.sleep(5)
    try:
        async with semaphore:
            async with session.get(link, headers=headers) as response:
                await asyncio.sleep(10)
                soup = bs(await response.text(), 'lxml')

            if soup.find('h1').text.strip() == 'Service Temporarily Unavailable':
                await asyncio.sleep(500)
                async with session.get(link, headers=headers) as response:
                    await asyncio.sleep(5)
                    soup = bs(await response.text(), 'html.parser')

        if not main_category:
            main_category = soup.find_all('span', class_='breadcrumbs__item-name font_xs')[1].text.strip()

        try:
            title = soup.find('h1').text
            res_dict['Наименование'] = title.strip()
        except:
            title = "Нет названия"
            res_dict['Наименование'] = title

        try:
            pattern = re.compile(r"setViewedProduct\((\d+, .+)'MIN_PRICE':([^'].+}),")
            script = soup.find('script', string=pattern)
            price = eval(pattern.search(script.text).group(2)).get('ROUND_VALUE_VAT')
            res_dict['Цена'] = price
        except:
            price = 'Цена не указана'
            res_dict['Цена'] = price

        res_dict['Категория'] = main_category

        try:
            article = soup.find('div', class_='article').find_all('span')[1].text.strip()
            res_dict['Артикул'] = article
        except:
            article = 'Нет артикула'
            res_dict['Артикул'] = article

        try:
            photo_link = soup.find(class_="product-detail-gallery__picture")['data-src']
            photo_path = BASE_URL + photo_link
            res_dict['Ссылка на фото'] = photo_path
        except:
            res_dict['Ссылка на фото'] = 'Нет фото'

        try:
            quantity = soup.find(class_='shadowed-block').find(class_='item-stock').find(
                class_='value').text.strip()
            res_dict['Наличие'] = quantity
        except:
            quantity = 'Наличие не указано'
            res_dict['Наличие'] = quantity

        try:
            desc = soup.find(class_='ordered-block desc').find(class_='content').text.strip()
            res_dict['Описание'] = desc
        except:
            res_dict['Описание'] = 'Нет описания'

        try:
            all_chars = soup.find(class_='char_block').find('table').find_all('tr')
            for i in all_chars:
                char = i.find_all('td')
                res_dict[char[0].text.strip()] = char[1].text.strip()
        except:
            try:
                all_chars = soup.find(class_='product-chars').find_all(class_='properties__item')
                for i in all_chars:
                    res_dict[i.find(class_='properties__title').text.strip()] = i.find(
                        class_='properties__value').text.strip()
            except:
                pass

        for d in [df_price_one, df_price_two, df_price_three]:
            if article + '.0' in d:
                d[article + '.0']['Цена'] = price
                break

        if article + '.0' in not_in_sale and quantity != 'Нет в наличии':
            not_in_sale[article + '.0']['В продаже'] = 'Да'
        elif article + '.0' not in sample and quantity != 'Нет в наличии':
            res_dict['Артикул'] = article + '.0'
            id_to_add.append(res_dict)
        elif article + '.0' in sample and quantity == 'Нет в наличии':
            id_to_del.append({"Артикул": article + '.0'})

        if count % 50 == 0:
            to_write_file(filepath='result/temporary/temporary_result.xlsx' ,temporary=True)

        print(f'\r{count}', end='')
        count = count + 1
        result.append(res_dict)

    except Exception as e:
        if item.strip():
            with open('error_log.txt', 'a+', encoding='utf-8') as file:
                file.write(f'{item} --- {e}\n')
        pass


async def get_gather_data():
    all_need_links = []

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False, limit=50, limit_per_host=10), trust_env=True) as session:
        response = await session.get(f'{BASE_URL}/catalog', headers=headers)
        response_text = await response.text()
        soup = bs(response_text, "lxml")
        all_lang = soup.find("div", class_="catalog_section_list").find_all('li')
        all_lang = [i.find('a')['href'] for i in all_lang]

        for lang in all_lang:
            try:
                response = await session.get(f'{BASE_URL}{lang}', headers=headers)
                soup = bs(await response.text(), "lxml")
                all_cat = soup.find_all("div", class_="section-compact-list__info")
                all_need_cat = [i.find('a')['href'] for i in all_cat]
                all_need_links.extend(all_need_cat)
            except:
                continue

        tasks = []

        for link in all_need_links:
            response = await session.get(f'{BASE_URL}{link}', headers=headers)
            await asyncio.sleep(10)
            soup = bs(await response.text(), "lxml")

            pagination = soup.find("div", class_="nums")
            if pagination:
                pagination = int(pagination.find_all('a')[-1].text.strip())
            else:
                pagination = 1
            # pagination = 3
            for page in range(1, pagination + 1):
                await asyncio.sleep(5)

                try:
                    async with session.get(f'{BASE_URL}{link}?PAGEN_1={page}', headers=headers) as response:
                        await asyncio.sleep(10)
                        soup = bs(await response.text(), 'html.parser')
                        page_items = soup.find_all('div', class_='item-title')
                        items = [item.find('a')['href'] for item in page_items]
                        main_category = soup.find('h1').text.strip()

                    for item in items:
                        task = asyncio.create_task(get_item_data(item, session, main_category))
                        tasks.append(task)
                except Exception as e:
                    with open('page_error.txt', 'a+', encoding='utf-8') as file:
                        file.write(f'{link} --- {page} --- {e}\n')

        await asyncio.gather(*tasks)
        await asyncio.sleep(10)

        to_write_file('result')

        print('\n--------------- Start parse error --------------')

        reparse_tasks = []
        reparse_count = 0
        while os.path.exists('error_log.txt') and reparse_count < 7:
            with open('error_log.txt', encoding='utf-8') as file:
                reparse_items = file.readlines()
                reparse_items = [i.split(" -")[0].strip() for i in reparse_items if i.strip()]
            print(f'>>>>>>>> Total error reparse - {len(reparse_items)}')
            os.remove('error_log.txt')
            for item in reparse_items:
                task = asyncio.create_task(get_item_data(item, session))
                reparse_tasks.append(task)
            await asyncio.gather(*reparse_tasks)


def main():
    asyncio.run(get_gather_data())
    to_write_file(filepath='result', final_result=True)



if __name__ == "__main__":
    a = time.time()
    main()
    print()
    print(time.time() - a)
