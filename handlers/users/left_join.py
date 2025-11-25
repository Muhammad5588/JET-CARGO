from aiogram import F
from aiogram.types import Message
from loader import dp
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramBadRequest

@dp.message(F.chat.type == ChatType.SUPERGROUP, F.new_chat_members)
async def new_member(message: Message):
    try:
        await message.delete()
    except TelegramBadRequest as e:
        print(f"Xabarni o'chirishda xatolik yuz berdi: {e}")

@dp.message(F.chat.type == ChatType.SUPERGROUP, F.left_chat_member)
async def left_member(message: Message):
    try:
        await message.delete()
    except TelegramBadRequest as e:
        print(f"Xabarni o'chirishda xatolik yuz berdi: {e}")