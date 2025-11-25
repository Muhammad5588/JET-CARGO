from aiogram import BaseMiddleware
from aiogram.types import InlineKeyboardButton, Update
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loader import bot
from data.Async_sqlDataBase import data_db as db

DEFAULT_RATE_LIMIT = 0.1

class UserCheckMiddleware(BaseMiddleware):
    def __init__(self, limit=DEFAULT_RATE_LIMIT, key_prefix='antiflood_'):
        self.rate_limit = limit
        self.prefix = key_prefix
        super(UserCheckMiddleware, self).__init__()

    async def __call__(self, handler, event: Update, data: dict):
        if not await db.status_force() or event.message.chat.type != 'private' :
            return await handler(event, data)

        user_id = event.message.from_user.id if event.message else event.callback_query.from_user.id
        force = False
        buttons = []

        for x in await db.majburiy_subs_view():
            kanals = await bot.get_chat(x)
            try:
                res = await bot.get_chat_member(chat_id=x, user_id=user_id)
            except Exception:
                continue

            if res.status not in ['member', 'administrator', 'creator']:
                buttons.append(InlineKeyboardButton(text=f"{kanals.title}", url=f"{await kanals.export_invite_link()}"))
                force = True

        if force:
            builder = InlineKeyboardBuilder()
            builder.add(*buttons)
            builder.add(InlineKeyboardButton(text="Tasdiqlash ✅", callback_data="check"))
            builder.adjust(1)

            if await db.is_user(user_id):
                await db.del_user(user_id)

            await bot.send_message(
                chat_id=user_id,
                text="‼️ Bot to'liq ishlashi uchun kanallarga obuna bo'ling!",
                reply_markup=builder.as_markup()
            )
        else:
            return await handler(event, data)
