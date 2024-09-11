import asyncio
import time

from aiogram import Bot
from aiogram.types.input_file import FSInputFile
import os

async def tg_send_files(chat_id, files: list[str], subject=None):
    bot = Bot('7283003827:AAF0Ii9JO8uOcURHS89j51Y8TJICar7RXFs')
    if subject:
        await bot.send_message(chat_id, subject)
    for file in files:
        file = FSInputFile(file)
        await bot.send_document(chat_id, file)
    await bot.session.close()


if __name__ == '__main__':
    while True:
        if os.path.exists('price_three.xlsx'):
            time.sleep(20)
            asyncio.run(tg_send_files(chat_id='259811443', files=["result.xlsx",
                                                                  "add.xlsx",
                                                                  "del.xlsx",
                                                                  'price_one.xlsx',
                                                                  'price_two.xlsx',
                                                                  'price_three.xlsx',
                                                                  'not_in_sale.xlsx',
                                                                  "error.txt"],
                                      subject='Результаты готовы:'))
            time.sleep(60)
            break
        time.sleep(600)
