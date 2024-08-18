import pandas.io.formats.excel
from bs4 import BeautifulSoup as bs
from pprint import pprint
from fake_useragent import UserAgent
import aiohttp
import asyncio
from pprint import pprint
import pandas as pd

pandas.io.formats.excel.ExcelFormatter.header_style = None

USER_AGENT = UserAgent()
headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "user-agent": USER_AGENT.random
}


async def get_item_data(session, item, page):
    await asyncio.sleep(10)
    link = item['link']
    item_data = item['data']

    async with session.get(f"{link}?PAGEN_1={page}", headers=headers) as response:
        soup = bs(await response.text(), "lxml")
        all_items = soup.find('div', class_='section-list').find_all('div', class_='section-list__cols')[1:]
        for item in all_items:
            data_dict = {
                'Article': '',
                'Part number': '',
                'Photo link': '',
                'Model name': '',
                'Description': '',
                'Human price': '',
                'Company price': ''
            }
            try:
                item_datas = item.find_all('div', class_='section-list__cell')[:-2]
                prices = item_datas[5].text.strip().split('\n')
                human_price = prices[0].split('р')[0].strip()
                company_price = prices[-1].split('р')[0].strip()
            except IndexError:
                human_price = 'Цену уточняйие'
                company_price = 'Цену уточняйие'
            data_dict['Item link'] = 'https://srv-trade.ru' + item_datas[3].find('a').get('href')
            data_dict['Article'] = item_datas[0].text.strip()
            data_dict['Part number'] = item_datas[1].text.strip()
            try:
                data_dict['Photo link'] = 'https://srv-trade.ru' + item_datas[2].find('a').get('href')
            except AttributeError:
                data_dict['Photo link'] = 'Нет фото'
            data_dict['Model name'] = item_datas[3].text.strip()
            data_dict['Description'] = item_datas[4].text.strip()
            data_dict['Human price'] = human_price
            data_dict['Company price'] = company_price
            item_data.append(data_dict)


async def get_gather_data():
    tasks = []
    links_list = {'setevoe_oborudovanie_huawei':
                      {'link': 'https://srv-trade.ru/catalog/setevoe_oborudovanie/setevoe_oborudovanie_huawei/',
                       'data': []},
                  'setevoe_oborudovanie_juniper':
                      {'link': 'https://srv-trade.ru/catalog/setevoe_oborudovanie/setevoe_oborudovanie_juniper/',
                       'data': []},
                  'setevoe_oborudovanie_h3c':
                      {'link': 'https://srv-trade.ru/catalog/setevoe_oborudovanie/setevoe_oborudovanie_h3c/',
                       'data': []},
                  'videokarty_professionalnye_nvidia_i_amd':
                      {'link': 'https://srv-trade.ru/catalog/videokarty_professionalnye_nvidia_i_amd/',
                       'data': []},
                  'servery_huawei':
                      {'link': 'https://srv-trade.ru/catalog/servery_huawei/',
                       'data': []},
                  'servery_lenovo':
                      {'link': 'https://srv-trade.ru/catalog/servery_lenovo/',
                       'data': []},
                  'servery_ibm':
                      {'link': 'https://srv-trade.ru/catalog/servery_ibm/',
                       'data': []},
                  'servery_hewlett_packard_enterprise_hp':
                      {'link': 'https://srv-trade.ru/catalog/servery_hewlett_packard_enterprise_hp/',
                       'data': []},
                  'servery_dell':
                      {'link': 'https://srv-trade.ru/catalog/servery_dell/',
                       'data': []},
                  'lentochnye_ustroystva':
                      {'link': 'https://srv-trade.ru/catalog/lentochnye_ustroystva',
                       'data': []},
                  'oborudovanie_moxa':
                      {'link': 'https://srv-trade.ru/catalog/oborudovanie_moxa/',
                       'data': []}}

    async with (aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session):
        for item in links_list:
            print(f'----- Start {item} -----')
            await asyncio.sleep(4)
            async with session.get(links_list[item]['link'], headers=headers) as response:
                soup = bs(await response.text(), 'lxml')
                pagination = soup.find('div', class_='pagination').find_all('a')[-2].text.strip()
                for page in range(1, int(pagination) + 1):
                    print(f'---------------- Start {item} - page {page} -----------------')
                    await asyncio.sleep(4)
                    task = asyncio.create_task(get_item_data(session, links_list[item], page))
                    tasks.append(task)
        await asyncio.gather(*tasks)

        for i in links_list:
            df = pd.DataFrame(links_list[i]['data'])
            df.to_excel(f'{i}.xlsx', index=False)


def main():
    asyncio.run(get_gather_data())


if __name__ == '__main__':
    main()
