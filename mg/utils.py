import asyncio
from fake_useragent import UserAgent
from bs4 import BeautifulSoup as bs

USER_AGENT = UserAgent()

ajax_headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "user-agent": USER_AGENT.random,
    'X-Requested-With': 'XMLHttpRequest',
}
headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "user-agent": USER_AGENT.random
}
count_c = 1


async def get_price_by_id(session, item_id, isbn):
    try:
        async with session.get(url=f"https://www.dkmg.ru/tovar/{item_id}", headers=headers) as response:
            soup = bs(await response.text(), 'lxml')
            price = soup.find_all("div", class_="product_item_price")[1].text.strip().split('.')[0]
            print(f'{item_id} - {price}')
            return price
    except Exception as e:
        with open('get_price_by_id.txt', 'a+') as f:
            f.write(f'{item_id} --- {e}\n')


async def get_item_id(session, item, array, semaphore):
    global count_c
    isbn = item
    await asyncio.sleep(2)
    try:
        async with semaphore:
            async with session.get(
                    f'https://www.dkmg.ru/ajax/ajax_search.php?term={isbn}&Catalog_ID=0&Series_ID=&Publisher_ID=&Year_Biblio=',
                    headers=ajax_headers) as response:
                await asyncio.sleep(2)
                resp = await response.json(content_type='text/html', encoding='utf-8-sig')
                item_id = resp[0]['value'].split('/')[-1].strip()
                if item_id != '#':
                    price = await get_price_by_id(session, item_id, isbn)
                    array[item]["Цена"] = price
                print(f'\r{count_c}', end='')
                count_c += 1
    except Exception as e:
        with open('get_item_id.txt', 'a+') as f:
            f.write(f'{isbn} --- {e}\n')
