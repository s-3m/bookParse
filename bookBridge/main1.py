from fake_useragent import UserAgent
from bs4 import BeautifulSoup as bs
import aiohttp
import asyncio
import pandas as pd
from selenium_data import get_selenium_page
import datetime
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "https://bookbridge.ru"
USER_AGENT = UserAgent()
headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "user-agent": USER_AGENT.random
}

count = 1

result = []

def get_item_data(item, session, main_category):
    global count
    print(count)
    count = count + 1
    res_dict = {}
    link = f'{BASE_URL}{item}'
    item_text_page = get_selenium_page(link)

    soup = bs(item_text_page, 'html.parser')
    # soup = bs(await response.text(), 'lxml')

    try:
        title = soup.find('h1').text
        res_dict['Наименование'] = title.strip()
    except:
        title = "Нет названия"
        res_dict['Наименование'] = title.strip()

    res_dict['Категория'] = main_category
    # try:
    #     bread_crumbs = soup.find('div', class_='breadcrumbs').find_all('a')
    #     cat_list = [i.text.strip() for i in bread_crumbs]
    #     # res_dict['Язык'] = cat_list[0]
    #     for i in range(1, len(cat_list)):
    #         res_dict[f'Категория {i}'] = cat_list[i].strip()
    # except:
    #     res_dict['Язык'] = ""
    #     res_dict['Категория 1'] = ""

    try:
        article = soup.find('div', class_='article').find_all('span')[1].text.strip()
        res_dict['Артикул'] = article
    except:
        res_dict['Артикул'] = 'Нет артикула'

    try:
        photo_link = soup.find(class_="product-detail-gallery__picture")['data-src']
        photo_path = BASE_URL + photo_link
        res_dict['Ссылка на фото'] = photo_path
    except:
        res_dict['Ссылка на фото'] = ''

    try:
        price = soup.find(class_='shadowed-block').find_all('span', class_='price_value')
        res_dict['Цена'] = price[0].text.strip()
        res_dict['Действующая цена'] = price[0].text.strip()
        if len(price) > 1:
            res_dict['Цена со скидкой'] = price[1].text.strip()
            res_dict['Действующая цена'] = price[1].text.strip()
    except:
        res_dict['Цена'] = 'Цена не указана'

    try:
        quantity = soup.find(class_='shadowed-block').find(class_='item-stock').find(class_='value').text.strip()
        res_dict['Наличие'] = quantity
    except:
        res_dict['Наличие'] = 'Наличие не указано'

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
        pass

    return res_dict
async def get_page_data(session, items, main_category):

    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(get_item_data, item, session, main_category) for item in items]
        result_future = [f.result()for f in futures]
    for i in result_future:
        result.append(i)

async def get_gather_data():

    all_need_links = []

    async with aiohttp.ClientSession() as session:
        response = await session.get(f'{BASE_URL}/catalog', headers=headers)
        response_text = await response.text()
        soup = bs(response_text, "lxml")
        all_lang = soup.find("div", class_="catalog_section_list").find_all('li')
        all_lang = [i.find('a')['href']for i in all_lang]

        for lang in all_lang:
            response = await session.get(f'{BASE_URL}{lang}', headers=headers)
            soup = bs(await response.text(), "lxml")
            all_cat = soup.find_all("div", class_="section-compact-list__info")
            all_need_cat = [i.find('a')['href'] for i in all_cat]
            all_need_links.extend(all_need_cat)

        tasks = []

        for link in all_need_links[:2]:
            await asyncio.sleep(1)
            response = await session.get(f'{BASE_URL}{link}', headers=headers)
            soup = bs(await response.text(), "lxml")
            try:
                pagination = soup.find("div", class_="nums").find_all('a')[-1].text
                for page in range(1, 6):
                    # for page in range(1, int(pagination) + 1):
                    # await get_page_data(link, session, page)

                    async with session.get(f'{BASE_URL}{link}?PAGEN_1={page}', headers=headers) as response:
                        soup = bs(await response.text(), 'lxml')
                        page_items = soup.find_all('div', class_='item-title')
                        items = [item.find('a')['href'] for item in page_items]
                        main_category = soup.find('h1').text.strip()

                    task = asyncio.create_task(get_page_data(session, items, main_category))
                    tasks.append(task)
            except AttributeError:
                continue

        await asyncio.gather(*tasks)




def main():
    asyncio.run(get_gather_data())
    df = pd.DataFrame(result)
    df.to_excel('result1.xlsx', index=False)

if __name__ == "__main__":
    a = datetime.datetime.now()
    main()
    print(datetime.datetime.now() - a)