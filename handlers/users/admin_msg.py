from aiogram.fsm.context         import FSMContext
from states.all_states           import for_admin
from aiogram.types               import Message, ContentType
from loader                      import dp
from keyboards.inline.admin_page import cancel_post_btn, confirm_admin_msg



@dp.message(for_admin.for_admin_message)
async def write_msg(message: Message, state: FSMContext):
    msg = message.text
    entiy = message.entities
    if (message.content_type == ContentType.TEXT):
        await state.clear()
        await message.answer("🧪 Xabar saqlandi")
        await state.set_data({"admin_msg": msg, "entity": f"{entiy}"})
        await message.reply(text = msg, entities = entiy, parse_mode = None, reply_markup = confirm_admin_msg(), disable_web_page_preview = True)
    else:
        await message.answer("🥊 Faqat <b>matn</b> ko'rinishidagi xabarlar qabul qilinadi!\n🔄 <i>Qayta kiriting!</i>", reply_markup = cancel_post_btn.as_markup())