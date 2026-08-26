import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils import executor

API_TOKEN = 'YOUR_TELEGRAM_BOT_API_TOKEN'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

async def send_alert(message: str):
    await bot.send_message(chat_id='YOUR_CHAT_ID', text=message, parse_mode=ParseMode.HTML)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
