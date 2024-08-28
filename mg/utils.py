import asyncio
from fake_useragent import UserAgent

USER_AGENT = UserAgent()

ajax_headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "user-agent": USER_AGENT.random,
    'X-Requested-With': 'XMLHttpRequest',
}

count_c = 1
semaphore = asyncio.Semaphore(10)
async def get_item_id(session, item):
    global count_c
    global semaphore
    isbn = item['article'][:-2]
    await asyncio.sleep(2)
    try:
        async with semaphore:
            async with session.get(
                    f'https://www.dkmg.ru/ajax/ajax_search.php?term={isbn}&Catalog_ID=0&Series_ID=&Publisher_ID=&Year_Biblio=',
                    headers=ajax_headers) as response:
                await asyncio.sleep(2)
                resp = await response.json(content_type='text/html', encoding='utf-8-sig')
                item_id = resp[0]['value'].split('/')[-1].strip()
                print(f'\r{count_c}', end='')
                count_c += 1
            return item_id
    except:
        return None
