import os
import time
import datetime
from dotenv import load_dotenv
import schedule
from loguru import logger
import pandas.io.formats.excel
from bs4 import BeautifulSoup as bs
from fake_useragent import UserAgent
import aiohttp
import asyncio
import pandas as pd
from tg_sender import tg_send_files

pandas.io.formats.excel.ExcelFormatter.header_style = None

BASE_URL = "https://bookbridge.ru"
USER_AGENT = UserAgent()

cookies = {
    "ASPRO_MAX_USE_MODIFIER": "Y",
    "BITRIX_SM_SALE_UID": "7967bf36fc7c5d5e22b4600e4f7dae21",
    "_ym_uid": "1724661849534829824",
    "BX_USER_ID": "763c7ee549f842ec42314fdbb95c00b7",
    "BITRIX_SM_AG_SMSE_H": "9781035130788%7C9781380069023%7C9781035100293_U1%7C9780521000581%7C9780230452732_U1%7C9780230438002%7C9780521123006_U1%7C9781380065957%7C9788466810609%7C9780141361673",
    "searchbooster_v2_user_id": "glNjupFeTeGqkFusruIRM_y1PB0QuX93qk80IBtFfq8%7C9.21.16.14",
    "ageCheckPopupRedirectUrl": "%2Fv2-mount-input",
    "PHPSESSID": "RqvU5MgwhswvXg7Y0s11B6WDQzCKCIH1",
    "BITRIX_SM_GUEST_ID": "1914444",
    "_ym_debug": "null",
    "_ym_isad": "2",
    "_ym_visorc": "w",
    "BITRIX_CONVERSION_CONTEXT_s1": "%7B%22ID%22%3A2%2C%22EXPIRE%22%3A1730581140%2C%22UNIQUE%22%3A%5B%22conversion_visit_day%22%5D%7D",
    "MAX_VIEWED_ITEMS_s1": "%7B%22346113%22%3A%5B%221730548668644%22%2C%222527796%22%5D%7D",
    "_ym_d": "1730549712",
    "BITRIX_SM_LAST_VISIT": "02.11.2024%2015%3A15%3A12",
}

headers = {
    "Accept": "*/*",
    "Accept-Language": "ru,en;q=0.9",
    "BX-ACTION-TYPE": "get_dynamic",
    "BX-CACHE-BLOCKS": '{"4i19eW":"68b329da9893","basketitems-component-block":"d41d8cd98f00","header-auth-block1":"d41d8cd98f00","mobile-basket-with-compare-block1":"d41d8cd98f00","header-auth-block2":"d41d8cd98f00","header-basket-with-compare-block1":"d41d8cd98f00","header-auth-block3":"d41d8cd98f00","header-basket-with-compare-block2":"d41d8cd98f00","header-basket-with-compare-block3":"d41d8cd98f00","header-auth-block4":"d41d8cd98f00","dv_346113":"87e7cc8bdbc9","qepX1R":"d41d8cd98f00","OhECjo":"d41d8cd98f00","6zLbbW":"14b226de416e","KSBlai":"d41d8cd98f00","area":"d41d8cd98f00","des":"d41d8cd98f00","viewed-block":"d41d8cd98f00","footer-subscribe":"d41d8cd98f00","8gJilP":"d41d8cd98f00","basketitems-block":"d41d8cd98f00","bottom-panel-block":"d41d8cd98f00"}',
    "BX-CACHE-MODE": "HTMLCACHE",
    "BX-REF": "",
    "Connection": "keep-alive",
    # 'Cookie': 'ASPRO_MAX_USE_MODIFIER=Y; BITRIX_SM_SALE_UID=7967bf36fc7c5d5e22b4600e4f7dae21; _ym_uid=1724661849534829824; BX_USER_ID=763c7ee549f842ec42314fdbb95c00b7; BITRIX_SM_AG_SMSE_H=9781035130788%7C9781380069023%7C9781035100293_U1%7C9780521000581%7C9780230452732_U1%7C9780230438002%7C9780521123006_U1%7C9781380065957%7C9788466810609%7C9780141361673; searchbooster_v2_user_id=glNjupFeTeGqkFusruIRM_y1PB0QuX93qk80IBtFfq8%7C9.21.16.14; ageCheckPopupRedirectUrl=%2Fv2-mount-input; PHPSESSID=RqvU5MgwhswvXg7Y0s11B6WDQzCKCIH1; BITRIX_SM_GUEST_ID=1914444; _ym_debug=null; _ym_isad=2; _ym_visorc=w; BITRIX_CONVERSION_CONTEXT_s1=%7B%22ID%22%3A2%2C%22EXPIRE%22%3A1730581140%2C%22UNIQUE%22%3A%5B%22conversion_visit_day%22%5D%7D; MAX_VIEWED_ITEMS_s1=%7B%22346113%22%3A%5B%221730548668644%22%2C%222527796%22%5D%7D; _ym_d=1730549712; BITRIX_SM_LAST_VISIT=02.11.2024%2015%3A15%3A12',
    "Referer": "https://bookbridge.ru/catalog/angliyskiy/uchebnaya_literatura/doshkolnoe_obrazovanie_i_nachalnaya_shkola/346113/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 YaBrowser/24.7.0.0 Safari/537.36",
    "X-Bitrix-Composite": "get_dynamic",
    "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "YaBrowser";v="24.7", "Yowser";v="2.5"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}

count = 1


async def get_item_data(session, item, error_items, semaphore):
    async with semaphore:
        try:
            async with session.get(
                item["link"], headers=headers, cookies=cookies
            ) as resp:
                await asyncio.sleep(3)
                response = await resp.json(content_type=None)
                dynamic_block = response.get("dynamicBlocks")
                if not dynamic_block:
                    item["in_stock"] = "del"
                    return
                page_text = dynamic_block[10]["CONTENT"].strip()
                soup = bs(page_text, "html.parser")
                quantity_element = soup.find("span", class_="plus dark-color")
                stock_quantity = "del"
                if quantity_element:
                    stock_quantity = quantity_element.get("data-max")
                global count
                print(f"\r{count}", end="")
                count += 1
            item["in_stock"] = stock_quantity
        except Exception as e:
            item["in_stock"] = "2"
            error_items.append(item)
            today = datetime.date.today().strftime("%d-%m-%Y")
            with open("error.txt", "a+") as f:
                f.write(f"{today} --- {item['link']} --- {e}\n")


async def get_gather_data():
    df = pd.read_excel("compare/bb_new_stock_dev.xlsx", converters={"article": str})
    df = df.where(df.notnull(), None)
    all_items_list = df.to_dict("records")
    error_items_list = []
    semaphore = asyncio.Semaphore(5)
    tasks = []
    async with aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(ssl=False, limit=50, limit_per_host=10),
        trust_env=True,
    ) as session:
        for item in all_items_list:
            if not item["link"]:
                item["in_stock"] = "del"
                continue
            task = asyncio.create_task(
                get_item_data(session, item, error_items_list, semaphore)
            )
            tasks.append(task)

        await asyncio.gather(*tasks)

        # Start reparse error
        error_tasks = []
        reparse_count = 0
        while error_items_list and reparse_count < 4:
            print()
            logger.warning("Start reparse error")
            reparse_count += 1
            new_items_list = error_items_list.copy()
            error_items_list.clear()
            for item in new_items_list:
                task = asyncio.create_task(
                    get_item_data(session, item, error_items_list, semaphore)
                )
                error_tasks.append(task)
            await asyncio.gather(*error_tasks)
            all_items_list.extend(new_items_list)

    print()
    logger.success("Finished parser successfully")
    global count
    count = 1

    await asyncio.sleep(30)
    logger.info("preparing files for sending")
    abs_path = os.path.abspath(os.path.dirname(__file__))
    df_result = pd.DataFrame(all_items_list)
    df_result.drop_duplicates(keep="last", inplace=True, subset="article")
    df_result.loc[df_result["in_stock"] != "del"].to_excel(
        f"{abs_path}/compare/bb_new_stock_dev.xlsx", index=False
    )
    df_without_del = df_result.loc[df_result["in_stock"] != "del"][
        ["article", "in_stock"]
    ]
    df_del = df_result.loc[df_result["in_stock"] == "del"][["article"]]
    del_path = f"{abs_path}/compare/bb_del.xlsx"
    without_del_path = f"{abs_path}/compare/bb_new_stock.xlsx"
    df_without_del.to_excel(without_del_path, index=False)
    df_del.to_excel(del_path, index=False)

    await asyncio.sleep(10)
    logger.info("Start sending files")
    await tg_send_files([without_del_path, del_path], subject="бб")


def main():
    logger.info("Start parsing BookBridge.ru")
    asyncio.run(get_gather_data())


def super_main():
    load_dotenv("../.env")
    schedule.every().day.at("20:00").do(main)

    while True:
        schedule.run_pending()


if __name__ == "__main__":
    start_time = time.time()
    main()
    # super_main()
    print(f"\n{time.time() - start_time}")
