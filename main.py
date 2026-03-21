import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# Токени аз @BotFather гирифтаатонро дар байни нохунакҳо гузоред
API_TOKEN = 'ИН_ҶО_ТОКЕН_ГУЗОРЕД'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.answer(f"Салом {message.from_user.first_name}! Ман боти шахсии Delta Force TJ ҳастам. Фармонро интизорам!")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

