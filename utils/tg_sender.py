from aiogram import Bot
from aiogram.types.input_file import FSInputFile

async def tg_send_files(chat_id, files: list[str], subject=None):
    bot = Bot('7283003827:AAF0Ii9JO8uOcURHS89j51Y8TJICar7RXFs')
    if subject:
        await bot.send_message(chat_id, subject)
    for file in files:
        file = FSInputFile(file)
        await bot.send_document(chat_id, file)
    await bot.session.close()
