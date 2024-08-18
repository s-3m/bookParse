import asyncio
from fake_useragent import UserAgent

USER_AGENT = UserAgent()

ajax_headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "user-agent": USER_AGENT.random,
    'X-Requested-With': 'XMLHttpRequest',
}


async def get_item_id(session, item):
    isbn = item['article'][:-2]
    await asyncio.sleep(5)
    # try:
    async with session.get(
            f'https://www.dkmg.ru/ajax/ajax_search.php?term={isbn}&Catalog_ID=0&Series_ID=&Publisher_ID=&Year_Biblio=',
            headers=ajax_headers) as response:
        await asyncio.sleep(10)
        resp = await response.json(content_type='text/html', encoding='utf-8')
        item_id = resp[0]['value'].split('/')[-1].strip()
    return item_id
