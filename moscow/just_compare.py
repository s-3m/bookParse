import asyncio
import os

import aiohttp
import pandas as pd
from pandas.io.formats import excel
from fake_useragent import UserAgent
from bs4 import BeautifulSoup as bs
import time
import schedule

from email_me import send_email
from selenium_data import get_book_data

BASE_URL = "https://www.moscowbooks.ru/"
USER_AGENT = UserAgent()
headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "user-agent": USER_AGENT.random
}

excel.ExcelFormatter.header_style = None
count = 1


async def to_check_item(article, session, past_day_result, to_del):
    global count
    link = f'{BASE_URL}/book/{article[:-2]}'
    # await asyncio.sleep(10)
    try:
        response = await session.get(link, headers=headers)
        response_text = await response.text()
        soup = bs(response_text, 'lxml')
        age_control = soup.find('input', id='age_verification_form_mode')
        script_index = 1
        if age_control:
            closed_page = get_book_data(link)
            soup = bs(closed_page, "lxml")
            script_index = 5

        if not soup.find('div', class_='book__buy'):
            del past_day_result[article]
            to_del.append(article)
        else:
            need_element = soup.find_all('script')
            a = need_element[script_index].text.split('MbPageInfo = ')[1].replace('false', 'False').replace(
                'true', 'True')
            need_data_dict = eval(a[:-1])['Products'][0]
            stock = need_data_dict['Stock']
            past_day_result[article] = {'Наличие': stock}

        print(f'\r{count}', end='')
        count += 1
    except Exception as e:
        with open('just_compare_error.txt', 'a+') as f:
            f.write(f'{link} ------ {e}\n')


async def reparse_error(session, past_day_result, to_del):
    reparse_count = 0
    error_file = 'just_compare_error.txt'
    try:
        while True:
            if not os.path.exists(error_file) or reparse_count > 10:
                break
            else:
                print('----------------------Start error parsing---------------------------')
                with open(error_file, 'r') as file:
                    error_links_list = [i.split(' ------ ')[0] for i in file.readlines()]
                    article_list = [link.split('/')[-2] + '.0' for link in error_links_list]
                    os.remove(error_file)
                if error_links_list:
                    for article in article_list:
                        await to_check_item(article, session, past_day_result, to_del)
                reparse_count += 1
    except:
        pass


async def get_compare():
    tasks = []
    to_del = []
    past_day_result = pd.read_excel('new_stock.xlsx', converters={'Артикул': str}).set_index('Артикул').to_dict(
        'index')
    article_list = list(past_day_result.keys())
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), trust_env=True) as session:
        for article in article_list:
            await to_check_item(article, session, past_day_result, to_del)
        await reparse_error(session, past_day_result, to_del)

    df = pd.DataFrame().from_dict(past_day_result, 'index')
    df.index.name = 'Артикул'
    df.index = df.index.astype(str)
    df.to_excel('new_stock.xlsx')

    del_df = pd.DataFrame({'Артикул': to_del})
    del_df.to_excel('del.xlsx', index=False)


def main():
    asyncio.run(get_compare())
    time.sleep(10)
    send_email()


def super_main():
    schedule.every().day.at('06:00').do(main)

    while True:
        schedule.run_pending()


if __name__ == '__main__':
    super_main()
