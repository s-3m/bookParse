import asyncio
from aiogram import Bot
from aiogram.types.input_file import FSInputFile
import os
from aiogram.types.input_media_document import InputMediaDocument

async def tg_send_files(files:list[str], subject):
    bot = Bot('7283003827:AAHqOwPGHoWvBPQlH9UKZ92HNkfi1Lsugbw')
    files_list = []
    for file in files:
        file = FSInputFile(file)
        file = InputMediaDocument(media=file, caption=subject)
        files_list.append(file)
    await bot.send_media_group('563670335', files_list)
    await bot.session.close()

if __name__ == '__main__':
    a = []
    for dirpath, _, filenames in os.walk('mg/compare'):
        for f in filenames:
            a.append(os.path.abspath(os.path.join(dirpath, f)))

    asyncio.run(tg_send_files(a, 'test'))
