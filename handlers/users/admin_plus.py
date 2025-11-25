from aiogram.fsm.context         import FSMContext
from data.Async_sqlDataBase      import data_db as db
from states.all_states           import for_admin
from aiogram                     import types
from loader                      import dp, bot
from keyboards.inline.admin_page import builder_admin, cancel_post_btn


@dp.message(for_admin.for_admin_plus)
async def add_admin(message: types.Message, state: FSMContext):
    msg = message.text
    user_id = message.chat.id
    if message.content_type == types.ContentType.TEXT:
    
        if msg == "/null":
            await message.delete()
            await state.clear()
            await message.answer(text = f"{message.chat.first_name} -- <b>⚜️Admin aka⚜️</b> Assalom-u alaykum Bot xizmatingizda!", reply_markup = builder_admin.as_markup())

        elif msg.isdigit():
            if int(msg) == int(user_id):
                await message.reply(text = "🪛 <b>Siz o'zingizni admin qila olmaysiz chunki o'ziz adminsiz.</b>\n🔂 <i>Qayta kiriting.</i>", reply_markup = cancel_post_btn.as_markup())
                return
            if not await db.is_admin(msg):
                try:
                    await message.reply(text = "🔌 Siz ushbu foydalanuvchini <b>Adminlar orasiga qo'shdingiz!</b>", reply_markup = builder_admin.as_markup())
                    await bot.send_video(chat_id = msg, video = "https://t.me/baza_java_strong/258")
                    await bot.send_message(chat_id = msg, text = "🥳 <b>Tabriklayman siz ushbu botda adminlik lavozimiga ko'tarildingiz!</b>", reply_markup = builder_admin.as_markup())
                    await db.admin_plus(msg)
                except Exception as e:
                    print(e)
                    await message.reply(text = f"🪒 <b>Bu ID raqamga tegishli foydalanuvchini Adminlar orasiga qo'sha olmadik sababi:</b> \n<code>{e}</code>")
                    pass

                await state.clear()
            else:
                await state.clear()
                await message.answer(text = f"🫢 Bu foydalanuvchi <b>Adminlar orasida mavjud!</b>", reply_markup = builder_admin.as_markup())
        else:
            await message.reply(text = "🛡 Siz kiritgan havola noto'g'ri formatda ❗️\n🔂 <i>Qayta kiriting:</i> /null", reply_markup = cancel_post_btn.as_markup())

    else:
        await message.reply(text = "🛡 Siz kiritgan havola noto'g'ri formatda ❗️\n🔂 <i>Qayta kiriting:</i> /null", reply_markup = cancel_post_btn.as_markup())