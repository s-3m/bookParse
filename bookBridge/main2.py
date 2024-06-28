from fake_useragent import UserAgent
from bs4 import BeautifulSoup as bs
import aiohttp
import asyncio
import pandas as pd
from selenium import webdriver
import requests

BASE_URL = "https://bookbridge.ru"
USER_AGENT = UserAgent()
headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "user-agent": USER_AGENT.random
}

result = []
count = 1
def get_page_data(link, session, page):
    response = requests.get(f'{BASE_URL}{link}?PAGEN_1={page}', headers=headers)
    soup = bs(response.text(), 'lxml')
    page_items = soup.find_all('div', class_='item-title')
    items = [item.find('a')['href'] for item in page_items]
    main_category = soup.find('h1').text.strip()



    for item in items:
        global count
        print(f'{count}')
        count = count + 1
        time.sleep(1)

        res_dict = {}
        response = requests.get(f'{BASE_URL}{item}', headers=headers)
        # response = await session.get(f'{BASE_URL}{item}', headers=headers)
        r = response.text
        soup = bs(r, 'html.parser')
        # soup = bs(await response.text(), 'lxml')

        res_dict['links'] = item
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
            photo_link = soup.find(class_ = "product-detail-gallery__picture")['data-src']
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
            res_dict['Цена'] = ''

        try:
            quantity = soup.find(class_='shadowed-block').find(class_='item-stock').find(class_='value').text.strip()
            res_dict['Наличие'] = quantity
        except:
            res_dict['Наличие'] = 'Не указано'

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

        print(res_dict)
        result.append(res_dict)

        # print(res_dict)

def get_gather_data():

    all_need_links = []


    response = requests.get(f'{BASE_URL}/catalog', headers=headers)
    response_text = response.text
    soup = bs(response_text, "lxml")
    all_lang = soup.find("div", class_="catalog_section_list").find_all('li')
    all_lang = [i.find('a')['href']for i in all_lang]

    for lang in all_lang:
        response = requests.get(f'{BASE_URL}{lang}', headers=headers)
        soup = bs(response.text, "lxml")
        all_cat = soup.find_all("div", class_="section-compact-list__info")
        all_need_cat = [i.find('a')['href'] for i in all_cat]
        all_need_links.extend(all_need_cat)

    tasks = []

    for link in all_need_links:
        try:
            response = requests.get(f'{BASE_URL}{link}', headers=headers)
            soup = bs(response.text(), "lxml")
            pagination = soup.find("div", class_="nums").find_all('a')[-1].text
            print(pagination)


            for page in range(1, int(pagination) + 1):
                # await get_page_data(link, session, page)
                get_page_data(link, page)

        except Exception as e:
            with open('error.txt', 'a', encoding='utf-8') as file:
                file.write(f'{link}\n')





def main():
    asyncio.run(get_gather_data())
    df = pd.DataFrame(result)
    df.to_excel('result.xlsx', index=False)

if __name__ == "__main__":
    main()