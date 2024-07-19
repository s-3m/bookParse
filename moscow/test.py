import time

from bs4 import BeautifulSoup as bs
from pprint import pprint
from fake_useragent import UserAgent
import aiohttp
import asyncio
import pandas as pd

BASE_URL = "https://www.moscowbooks.ru/"
USER_AGENT = UserAgent()
headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "user-agent": USER_AGENT.random
}

result = []
count = 1


async def get_item_data(session, link):
    global count
    item_data = {}
    try:
        async with session.get(link, headers=headers) as response:
            await asyncio.sleep(4)
            soup = bs(await response.text(), "lxml")
            need_element = soup.find_all('script')
            a = need_element[1].text.split(' = ')[1].replace('false', 'False').replace('true', 'True')
            need_data_dict = eval(a[:-1])['Products'][0]
            stock = need_data_dict['Stock']
            articul = link.split('/')[-2]
            isbn = 'Нет ISBN'
            all_details = soup.find_all('dl', class_='book__details-item')
            for detail in all_details:
                detail = detail.find_all('dt')
                if detail[0].text.strip() == 'ISBN:':
                    isbn = detail[1].text.strip()

            item_data['Артикул'] = articul + '.0'
            item_data['ISBN'] = isbn
            item_data['Наличие'] = stock

            print(f'\r{count}', end='')
            count = count + 1

            result.append(item_data)

    except Exception as e:
        with open('erorr.txt', 'a+') as file:
            file.write(f'{link} ------ {e}')


async def get_gather_data():
    tasks = []
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), trust_env=True) as session:
        response = await session.get(f'{BASE_URL}/books/', headers=headers)
        response_text = await response.text()
        soup = bs(response_text, "lxml")
        max_pagination = soup.find('ul', class_='pager__list').find_all('li')[-2].text
        tasks = []
        # for page in range(1, int(max_pagination) + 1):
        for page in range(1, 21):
            try:
                page_response = await session.get(f'{BASE_URL}/books/?page={page}', headers=headers)
                page_html = await page_response.text()
                soup = bs(page_html, "lxml")
                all_books_on_page = soup.find_all('div', class_='catalog__item')
                all_items = [book.find('a')['href'] for book in all_books_on_page]
                for i in all_items:
                    link = f'{BASE_URL}{i}' if not i.startswith('/') else f'{BASE_URL}{i[1:]}'
                    task = asyncio.create_task(get_item_data(session, link))
                    tasks.append(task)
            except Exception as e:
                with open('error_page.txt', 'a+') as file:
                    file.write(f"{page} + - + {e}")

        await asyncio.gather(*tasks)


def main():
    asyncio.run(get_gather_data())
    df = pd.DataFrame(result)
    df.to_excel('result.xlsx', index=False)


if __name__ == "__main__":
    start_time = time.time()
    main()
    pprint(time.time() - start_time)
