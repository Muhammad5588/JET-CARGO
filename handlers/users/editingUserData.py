

from loader import dp, bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.filters import StateFilter
from data.Async_sqlDataBase import data_db as db
from states.AdminStates import EditUserDataStates



@dp.message(StateFilter(EditUserDataStates.editing_user_data))
async def process_edit_user_data(message: Message, state: FSMContext):
    data = await state.get_data()
    edit_user_id = data.get("edit_user_id", None)
    edit_type = data.get("edit_type", "")
    new_data = message.text.strip()

    if not new_data:
        await message.answer("❌ Iltimos, yangi ma'lumotni kiriting.")
        return
    
    if new_data.lower() == "⬅️ orqaga" or new_data.lower() == "⬅️ назад":
        await message.answer("❌ Tahrirlash bekor qilindi.")
        await state.clear()
        return


    edit_type = edit_type.split(":")[0] # to get the actual type without user_id
    # Foydalanuvchi ma'lumotlarini yangilash
    response = await db.edit_user_data(edit_user_id, edit_type, new_data)

    await message.answer(response)
    await state.clear()
