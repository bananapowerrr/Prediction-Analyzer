import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils import executor

from core.logger import get_logger

logger = get_logger(__name__)

API_TOKEN = 'YOUR_TELEGRAM_BOT_API_TOKEN'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


@dp.errors_handler()
async def errors_handler(update: types.Update, exception: Exception):
    """Перехват исключений на уровне задач диспетчера.

    Ловит любые ошибки, возникшие в обработчиках обновлений, логирует их
    и помечает как обработанные, чтобы диспетчер продолжил работу.
    """
    logger.exception(
        "Необработанное исключение в задаче диспетчера (update_id=%s): %s",
        getattr(update, "update_id", None),
        exception,
    )
    return True


async def send_alert(message: str):
    await bot.send_message(chat_id='YOUR_CHAT_ID', text=message, parse_mode=ParseMode.HTML)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
