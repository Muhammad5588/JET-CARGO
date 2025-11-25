import logging
from aiogram import types, F
from aiogram.types import ContentType
from aiogram.enums import ChatType

from loader import dp, bot
from data.Async_sqlDataBase import data_db as db

logger = logging.getLogger(__name__)

# Constants
ADMIN_PASSWORD_PREFIX = "java_strongX+7__"


@dp.message(F.chat.type != ChatType.SUPERGROUP)
async def echo_handler(message: types.Message) -> None:
    """
    Xabarlarni takrorlash va admin tekshiruvi

    Args:
        message: Telegram xabari
    """
    msg = message.text
    user_id = message.chat.id

    if ContentType.TEXT == message.content_type:
        try:
            # Admin parol tekshiruvi
            if msg == f"{await db.one_step_password_view()}":
                if await db.is_admin(msg):
                    await db.del_admin(msg)
                result = await db.replace_admin(user_id)
                await bot.send_message(chat_id=user_id, text=result)
                await message.delete()
                logger.info(f"Admin changed: {user_id}")

            # Yangi parol o'rnatish
            elif msg.startswith(ADMIN_PASSWORD_PREFIX):
                new_password = msg.split("__")[1]
                result = await db.new_pass(new_password)
                await bot.send_message(chat_id=user_id, text=result)
                await message.delete()
                logger.info(f"Password changed by: {user_id}")

            # Xabarni takrorlash
            else:
                await message.answer(text=message.text, entities=message.entities, parse_mode=None)

        except Exception as e:
            logger.error(f"Echo handler error: {e}", exc_info=True)
            await message.answer(text=message.text, entities=message.entities, parse_mode=None)