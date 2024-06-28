import os.path
import time
from pprint import pprint

from fake_useragent import UserAgent
from bs4 import BeautifulSoup as bs
import aiohttp
import asyncio
import pandas as pd
from uuid import uuid4

BASE_URL = 'https://instrument.ru'
USER_AGENT = UserAgent()
headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,"
              "application/signed-exchange;v=b3;q=0.9",
    "user-agent": USER_AGENT.random
}

df = pd.read_excel('Matrix.xlsx')
file_data = df.to_dict(orient='records')

item_list = [(str(i['Код артикула'])[:-2], i['Ссылка на товар']) for i in file_data]

# pprint(item_list)
# pprint(file_data[55])

error = []


async def get_item_data(session, item):
    # if os.path.exists(f'./results/denzel/{item[0]}'):
    #     return
    await asyncio.sleep(5)
    try:
        response = await session.get(item[1], headers=headers)
        soup = bs(await response.text(), 'lxml')
        try:
            img_area = soup.find('div', class_='swiper-wrapper detail-vert-swiper__wrapper').find_all('picture')
            article = soup.find('div', class_='detail__article').find('p').text
            img_list = [i.find('source').attrs['data-srcset'] for i in img_area]
            for number, value in enumerate(img_list):
                response = await session.get(BASE_URL + value, headers=headers)
                content = await response.content.read()
                path = f'./results/matrix1/{article}'
                os.makedirs(path, exist_ok=True)
                with open(f'{path}/{article}_{number + 1}.jpg', 'wb') as file:
                    file.write(content)
        except AttributeError as e:
            with open('matrix1_error.txt', 'a+') as file:
                file.write(f'{item[1]}\n{e}\n')
    except Exception as e:
        error.append({'Ссылка': item[1]})


async def get_gather_data():
    tasks = []
    print(len(item_list))
    async with aiohttp.ClientSession(trust_env=True) as session:
        for item_link in item_list:
            task = asyncio.create_task(get_item_data(session, item_link))
            tasks.append(task)

        await asyncio.gather(*tasks)


def main():
    asyncio.run(get_gather_data())
    df = pd.DataFrame(error)
    df.to_excel('error.xlsx')


if __name__ == '__main__':
    a = time.time()
    main()
    print(time.time() - a)
