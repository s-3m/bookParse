import time
from fake_useragent import UserAgent
from bs4 import BeautifulSoup as bs
import aiohttp
import asyncio
import pandas as pd
from utils import to_write_price_dict
from playwright.async_api import async_playwright

BASE_URL = "https://bookbridge.ru"
USER_AGENT = UserAgent()
headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "user-agent": USER_AGENT.random
}
df_price_one = pd.read_excel("One.xlsx").set_index('Артикул').to_dict('index')
df_price_two = pd.read_excel("Two.xlsx").set_index('Артикул').to_dict('index')
df_price_three = pd.read_excel("Three.xlsx").set_index('Артикул').to_dict('index')
sample = pd.read_excel("abc.xlsx", converters={"Артикул": str}).set_index('Артикул').to_dict('index')
count = 1
result = []

price_file_one = []
price_file_two = []
price_file_three = []

id_to_del = []
id_to_add = []


async def get_item_data(page_content, main_category, link):
    global count
    res_dict = {}

    try:
        soup = bs(page_content, 'html.parser')

        try:
            title = soup.find('h1').text
            res_dict['Наименование'] = title.strip()
        except:
            title = "Нет названия"
            res_dict['Наименование'] = title.strip()

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
            price = soup.find(class_='shadowed-block').find_all('span', class_='price_value')
            res_dict['Цена'] = price[0].text.strip()
            res_dict['Действующая цена'] = price[0].text.strip()
            if len(price) > 1:
                res_dict['Цена со скидкой'] = price[1].text.strip()
                res_dict['Действующая цена'] = price[1].text.strip()
        except:
            price = 'Цена не указана'
            res_dict['Цена'] = price

        try:
            quantity = soup.find(class_='shadowed-block').find(class_='item-stock').find(class_='value').text.strip()
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

        if article + '.0'.strip() in df_price_one:
            if len(price) > 1:
                to_write_price_dict(need_list=price_file_one, id=article, price=price[0].text.strip(),
                                    sale_price=price[1].text.strip())
            else:
                to_write_price_dict(need_list=price_file_one, id=article, price=price[0].text.strip())
        elif article + '.0'.strip() in df_price_two:
            if len(price) > 1:
                to_write_price_dict(need_list=price_file_two, id=article, price=price[0].text.strip(),
                                    sale_price=price[1].text.strip())
            else:
                to_write_price_dict(need_list=price_file_two, id=article, price=price[0].text.strip())
        elif article + '.0'.strip() in df_price_three:
            if len(price) > 1:
                to_write_price_dict(need_list=price_file_three, id=article, price=price[0].text.strip(),
                                    sale_price=price[1].text.strip())
            else:
                to_write_price_dict(need_list=price_file_three, id=article, price=price[0].text.strip())

        if article not in sample and quantity != 'Нет в наличии':
            id_to_add.append(res_dict)
        elif article in sample and quantity == 'Нет в наличии':
            id_to_del.append({"Артикул": article})

        print(f'\r{count}', end='')
        count = count + 1
        return res_dict

    except:
        with open('error_log.txt', 'a+', encoding='utf') as file:
            file.write(link + '\n')


async def get_page_data(items, main_category):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True, args=['--no-sandbox',
                                                                        '--ignore-certificate-errors',
                                                                        '--allow-running-insecure-content',
                                                                        '--disable-blink-features=AutomationControlled'
                                                                        ])
        context = await browser.new_context()
        page = await context.new_page()
        for item in items:
            link = BASE_URL + item
            await page.goto(link)
            page_content = await page.content()
            item_result = await get_item_data(page_content, main_category, link)
            result.append(item_result)


async def get_gather_data():
    all_need_links = []

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
        response = await session.get(f'{BASE_URL}/catalog', headers=headers)
        response_text = await response.text()
        soup = bs(response_text, "lxml")
        all_lang = soup.find("div", class_="catalog_section_list").find_all('li')
        all_lang = [i.find('a')['href'] for i in all_lang]

        for lang in all_lang[:1]:
            await asyncio.sleep(1)
            response = await session.get(f'{BASE_URL}{lang}', headers=headers)
            soup = bs(await response.text(), "lxml")
            all_cat = soup.find_all("div", class_="section-compact-list__info")
            all_need_cat = [i.find('a')['href'] for i in all_cat]
            all_need_links.extend(all_need_cat)

        tasks = []

        for link in all_need_links[:2]:
            await asyncio.sleep(5)
            response = await session.get(f'{BASE_URL}{link}', headers=headers)
            soup = bs(await response.text(), "lxml")
            try:
                pagination = soup.find("div", class_="nums").find_all('a')[-1].text
                all_cat_items = []

                for page in range(1, 4):
                    await asyncio.sleep(5)

                    async with session.get(f'{BASE_URL}{link}?PAGEN_1={page}', headers=headers) as response:
                        soup = bs(await response.text(), 'lxml')
                        page_items = soup.find_all('div', class_='item-title')
                        items = [item.find('a')['href'] for item in page_items]
                        # all_cat_items.extend(items)
                        main_category = soup.find('h1').text.strip()

                    task = asyncio.create_task(get_page_data(items, main_category))
                    tasks.append(task)
            except AttributeError:
                continue
        await asyncio.gather(*tasks)


def main():
    asyncio.run(get_gather_data())
    df = pd.DataFrame(result)
    df.to_excel('result2.xlsx', index=False)
    df_one = pd.DataFrame(price_file_one)
    df_one.to_excel('price_one.xlsx', index=False)
    df_one = pd.DataFrame(price_file_two)
    df_one.to_excel('price_two.xlsx', index=False)
    df_one = pd.DataFrame(price_file_three)
    df_one.to_excel('price_three.xlsx', index=False)

    df_add = pd.DataFrame(id_to_add)
    df_add.to_excel("Add.xlsx", index=False)
    df_del = pd.DataFrame(id_to_del)
    df_del.to_excel("Del.xlsx", index=False)


if __name__ == "__main__":
    a = time.time()
    main()
    print(time.time() - a)
