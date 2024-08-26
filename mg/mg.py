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


async def get_item_data(session, link, main_category):
    global semaphore
    try:
        item_data = {}
        async with semaphore:
            async with session.get(BASE_URL + link, headers=headers) as response:
                soup = bs(await response.text(), "lxml")
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

                item_id = soup.find('a', class_='btn_red wish_list_btn add_to_cart')['data-tovar']
                if not item_id:
                    item_id = ''
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
    except Exception as e:
        with open('error.txt', 'a+', encoding='utf-8') as f:
            f.write(f'{BASE_URL}{link} ----- {e}\n')


async def get_gather_data():
    tasks = []
    async with (aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session):
        response = await session.get(BASE_URL, headers=headers)
        response_text = await response.text()
        soup = bs(response_text, "lxml")
        cat_list = soup.find_all("h4")
        cat_list = [item.find('a')['href'] for item in cat_list[:8]]

        for cat_link in cat_list:
            try:
                response = await session.get(BASE_URL + cat_link, headers=headers)
                response_text = await response.text()
                soup = bs(response_text, 'lxml')
                pagin_max = int(soup.find("div", class_="navitem").find_all("a")[-2]['href'].split('=')[-1])
                main_category = soup.find("h1").text.split(' (')[0]
                print(f'\n---Делаю категорию - {main_category}---')

                for page_numb in range(1, pagin_max + 1):
                    print(f'----------------стр - {page_numb} из {pagin_max}-----------')
                    response = await session.get(f'{BASE_URL}{cat_link}?page={page_numb}')
                    await asyncio.sleep(5)
                    response_text = await response.text()
                    soup = bs(response_text, 'lxml')
                    items_on_page = soup.find_all('div', class_='product_img')
                    items_links = [item.find('a')['href'] for item in items_on_page]
                    for link in items_links:
                        task = asyncio.create_task(get_item_data(session, link, main_category))
                        tasks.append(task)
            except Exception as e:
                with open('cat_error.txt', 'a+') as f:
                    f.write(f'{BASE_URL}{cat_link} ----- {e}\n')
                    continue
        await asyncio.gather(*tasks)


def main():
    asyncio.run(get_gather_data())
    df = pd.DataFrame(result)
    df.to_excel('result.xlsx', index=False)

    df_add = pd.DataFrame(id_to_add)
    df_add.to_excel('add.xlsx', index=False)

    df_del = pd.DataFrame(id_to_del)
    df_del.to_excel('del.xlsx', index=False)

    df_one = pd.DataFrame().from_dict(df_price_one, orient='index')
    df_one.index.name = 'Артикул'
    df_one.to_excel('price_one.xlsx')

    df_two = pd.DataFrame().from_dict(df_price_two, orient='index')
    df_two.index.name = 'Артикул'
    df_two.to_excel('price_two.xlsx')

    df_three = pd.DataFrame().from_dict(df_price_three, orient='index')
    df_three.index.name = 'Артикул'
    df_three.to_excel('price_three.xlsx')

    df_not_in_sale = pd.DataFrame().from_dict(not_in_sale, orient='index')
    df_not_in_sale.index.name = 'Артикул'
    df_not_in_sale.to_excel('not_in_sale.xlsx')


if __name__ == "__main__":
    start_time = time.time()
    main()
    pprint(time.time() - start_time)
