from datetime import datetime
from io import StringIO
from aiogram.types               import CallbackQuery, FSInputFile, BufferedInputFile
from aiogram.fsm.context         import FSMContext
from data.Async_sqlDataBase      import data_db as db
from handlers.users.generateUniqueid import generate_unique_code
from loader                      import dp, bot
from keyboards.inline.admin_page import (
    builder_admin, copy_share, num_btn, 
    reklama_btn_one, reklama_btn_two, 
    cancel_post_btn, num_btn_admin, 
    control_entitiy, majburiy_subs_on_off,
    hamkorlik
    )
from keyboards.inline.user_page  import back, delete_keyboard, edit_keyboard
import time
from states.AdminStates import EditUserDataStates
from states.all_states           import for_admin
import pytz

from utils.keyboards import back_keyboard, user_management_inline_keyboard

tashkent_tz = pytz.timezone("Asia/Tashkent")
START_TIME = time.time()

async def process_channel_pagination(message, call, btn_txt, user_id):      #reklama beradigan bolimni paginationi
    if "##" in btn_txt:
        parts = btn_txt.split("##")
        action = parts[1]
    else:
        parts = btn_txt.split("_kanal")
        action = parts[1]
    
    if len(parts) > 1 and (action == 'max_channel' or action == 'min_channel') and parts[0].isdigit():
        id_num = int(parts[0])

        if action == "max_channel":
            k = id_num + 1
            b = id_num + 8
            bound_check = await db.is_max_channel(user_id)
            bound_message = "🛎️ Siz so'ngi sahifadasiz!"
        elif action == "min_channel":
            k = id_num - 8
            b = id_num - 1
            bound_check = await db.is_min_channel(user_id)
            bound_message = "🛰 Siz 1-sahifadasiz"
        else:
            await call.answer(text=f"💀 Siz bosgan tugmada xatolik chiqdi! - {action}", show_alert=True)
            return

        if id_num == int(bound_check):
            await call.answer(text=bound_message, show_alert=True)
        else:
            await call.answer()
            if await db.admin_status_view(user_id):
                information = "Qaysi kanalni <b>O'chirib</b> tashlamoqchisiz❓"
                information2 = "<i>❗️ Siz hamkor kanallarni o'chira olmaysiz</i>"
            else:
                information = "Qaysi kanalga <b>Reklama</b> bermoqchisiz❓"
                information2 = "<i>❗️ Sizda hamkor kanallar mavjud emas</i>"

            for_btn = []
            malumotlar = str()
            channels = await db.view_list_channel(user_id, k, b)
            for i in channels:
                channel = await bot.get_chat(i[1])
                invite_link = channel.invite_link
                for_btn.append(i[0])
                malumotlar += f"\n{i[0]} - <b><a href='{invite_link}'>{channel.title}</a></b>\n➖➖➖➖➖➖➖➖"

            if await db.exist_user_hamkorlik(user_id) and not await db.admin_status_view(user_id):
                malumotlar2 = str()
                partner_channels = await db.view_list_admin_partner(user_id, k, b)
                for i2 in partner_channels:
                    channel1 = await bot.get_chat(i2[1])
                    invite_link1 = await channel1.export_invite_link()
                    for_btn.append(i2[0])
                    malumotlar2 += f"\n{i2[0]} - <b><a href='{invite_link1}'>{channel1.title}</a></b>\n➖➖➖➖➖➖➖➖"
                await message.edit_text(
                    text=f"{information}\n<b>💎 Sizning kanallaringiz:</b>\n{malumotlar}\n<b>🤝 Hamkor kanallar:</b>\n{malumotlar2}", 
                    reply_markup=num_btn(for_btn), 
                    disable_web_page_preview=True
                )
            else:
                await message.edit_text(
                    text=f"{information}\n{malumotlar}\n{information2}", 
                    reply_markup=num_btn(for_btn), 
                    disable_web_page_preview=True
                )
    else:
        await call.answer(text=f"💀 Siz bosgan tugmada xatolik chiqdi! - {parts[0]}", show_alert=True)

async def process_admin_pagination(call, btn_txt):          # adminlardan malumot oladigan pagination
    if "__" in btn_txt:
        parts = btn_txt.split("__")
        action = parts[1]
    else:
        parts = btn_txt.split("info_")
        action = parts[1]
    
    if len(parts) > 1 and (action == 'max_admin' or action == 'min_admin') and parts[0].isdigit():
        id_num = int(parts[0])

        if action == "max_admin":
            k = id_num + 1
            b = id_num + 8
            bound_check = await db.is_max()
            bound_message = "🛎️ Siz so'ngi sahifadasiz!"
        elif action == "min_admin":
            k = id_num - 8
            b = id_num - 1
            bound_check = await db.is_min()
            bound_message = "🛰 Siz 1-sahifadasiz"
        else:
            await call.answer(text=f"💀 Siz bosgan tugmada xatolik chiqdi! - {action}", show_alert=True)
            return

        if id_num == int(bound_check):
            await call.answer(text=bound_message, show_alert=True)
        else:
            await call.answer()
            for_btn_admin = []
            malumotlar_admin = str()
            username = str()
            for a in await db.view_list_admin(k, b):
                admin_info = await bot.get_chat(a[1])
                for_btn_admin.append(a[0])
                if not admin_info.username:
                    malumotlar_admin += f"\n{a[0]} - <b>{admin_info.first_name}</b> , 🆔: <code>{admin_info.id}</code>\n➖➖➖➖➖➖➖➖"
                else:
                    username = admin_info.username
                    malumotlar_admin += f"\n{a[0]} - <b><a href='https://t.me/{username}'>{admin_info.first_name}</a></b> , 🆔: <code>{admin_info.id}</code>\n➖➖➖➖➖➖➖➖"
            
            await call.message.edit_text(
                f"🕸️ Agar siz <b>admin haqida ma'lumot</b> yoki <b>adminlikdan bo'shatmoqchi</b> bo'sangiz quyidagilardan birini tanlang:💨\n{malumotlar_admin}",
                reply_markup=num_btn_admin(for_btn_admin),
                disable_web_page_preview=True
            )
    else:
        await call.answer(text=f"💀 Siz bosgan tugmada xatolik chiqdi! - {parts[0]}", show_alert=True)

async def process_hamkor_pagination(call, btn_txt):          # adminlardan malumot oladigan pagination
    if "-min-admin" in btn_txt:
        parts = btn_txt.split("_hamkor-")
        action = parts[1]
    else:
        parts = btn_txt.split("%")
        action = parts[1]
    
    if len(parts) > 1 and (action == 'max-admin' or action == 'min-admin') and parts[0].isdigit():
        id_num = int(parts[0])

        if action == "max-admin":
            k = id_num + 1
            b = id_num + 8
            bound_check = await db.is_max()
            bound_message = "🛎️ Siz so'ngi sahifadasiz!"
        elif action == "min-admin":
            k = id_num - 8
            b = id_num - 1
            bound_check = await db.is_min()
            bound_message = "🛰 Siz 1-sahifadasiz"
        else:
            await call.answer(text=f"💀 Siz bosgan tugmada xatolik chiqdi! - {action}", show_alert=True)
            return

        if id_num == int(bound_check):
            await call.answer(text=bound_message, show_alert=True)
        else:
            await call.answer()
            for_btn_admin = []
            malumotlar_admin = str()
            username = str()
            for a in await db.view_list_admin(k, b):
                admin_info = await bot.get_chat(a[1])
                for_btn_admin.append(a[0])
                if not admin_info.username:
                    malumotlar_admin += f"\n{a[0]} - <b>{admin_info.first_name}</b> , 🆔: <code>{admin_info.id}</code>\n➖➖➖➖➖➖➖➖"
                else:
                    username = admin_info.username
                    malumotlar_admin += f"\n{a[0]} - <b><a href='https://t.me/{username}'>{admin_info.first_name}</a></b> , 🆔: <code>{admin_info.id}</code>\n➖➖➖➖➖➖➖➖"
            
            await call.message.edit_text(
                f"🕸️ Agar siz <b>Adminlardan birini Hamkor</b> qilmoqchi bo'sangiz quyidagilardan birini tanlang:💨\n{malumotlar_admin}",
                reply_markup=num_btn_admin(for_btn_admin, "hamkor"),
                disable_web_page_preview=True
            )
    else:
        await call.answer(text=f"💀 Siz bosgan tugmada xatolik chiqdi! - {parts[0]}", show_alert=True)

async def process_hamkor_minus_pagination(call, btn_txt):          # adminlardan malumot oladigan pagination
    if "!!min-admin" in btn_txt:
        parts = btn_txt.split("_removeHamkor!!")
        action = parts[1]
    else:
        parts = btn_txt.split("&&")
        action = parts[1]
    
    if len(parts) > 1 and (action == 'max-admin' or action == 'min-admin') and parts[0].isdigit():
        id_num = int(parts[0])

        if action == "max-admin":
            k = id_num + 1
            b = id_num + 8
            bound_check = await db.is_min_max_hamkorlik(call.message.chat.id)[1]
            bound_message = "🛎️ Siz so'ngi sahifadasiz!"
        elif action == "min-admin":
            k = id_num - 8
            b = id_num - 1
            bound_check = await db.is_min_max_hamkorlik(call.message.chat.id)[0]
            bound_message = "🛰 Siz 1-sahifadasiz"
        else:
            await call.answer(text=f"💀 Siz bosgan tugmada xatolik chiqdi! - {action}", show_alert=True)
            return

        if id_num == int(bound_check):
            await call.answer(text=bound_message, show_alert=True)
        else:
            await call.answer()
            for_btn_admin = []
            malumotlar_admin = str()
            username = str()
            for a in await db.vkm_list_admin_partner(call.message.chat.id, k, b):
                admin_info = await bot.get_chat(a[1])
                for_btn_admin.append(a[0])
                if not admin_info.username:
                    malumotlar_admin += f"\n{a[0]} - <b>{admin_info.first_name}</b> , 🆔: <code>{admin_info.id}</code>\n➖➖➖➖➖➖➖➖"
                else:
                    username = admin_info.username
                    malumotlar_admin += f"\n{a[0]} - <b><a href='https://t.me/{username}'>{admin_info.first_name}</a></b> , 🆔: <code>{admin_info.id}</code>\n➖➖➖➖➖➖➖➖"
            
            await call.message.edit_text(
                f"🕸️ Agar siz <b>Adminlardan birini Hamkor</b> qilmoqchi bo'sangiz quyidagilardan birini tanlang:💨\n{malumotlar_admin}",
                reply_markup=num_btn_admin(for_btn_admin, "hamkor"),
                disable_web_page_preview=True
            )
    else:
        await call.answer(text=f"💀 Siz bosgan tugmada xatolik chiqdi! - {parts[0]}", show_alert=True)

async def process_channel_del_pagination(message, call, btn_txt, user_id):  # kanallarni ochirish paginatoni
    parts = btn_txt.split("_minus")
    action = parts[1]

    if len(parts) > 1 and (action == 'min_channel' or action == 'max_channel') and parts[0].isdigit():
        id_num = int(parts[0])

        if action == "max_channel":
            k = id_num + 1
            b = id_num + 8
            bound_check = await db.is_max_channel(user_id)
            bound_message = "🛎️ Siz so'ngi sahifadasiz!"
        elif action == "min_channel":
            k = id_num - 8
            b = id_num - 1
            bound_check = await db.is_min_channel(user_id)
            bound_message = "🛰 Siz 1-sahifadasiz"
        else:
            await call.answer(text=f"💀 Siz bosgan tugmada xatolik chiqdi! - {action}", show_alert=True)
            return

        if id_num == int(bound_check):
            await call.answer(text=bound_message, show_alert=True)
        else:
            await call.answer()
            if await db.admin_status_view(user_id):
                information = "Qaysi kanalni <b>O'chirib</b> tashlamoqchisiz❓"
                information2 = "<i>❗️ Siz hamkor kanallarni o'chira olmaysiz</i>"
            else:
                information = "Qaysi kanalga <b>Reklama</b> bermoqchisiz❓"
                information2 = "<i>❗️ Sizda hamkor kanallar mavjud emas</i>"
            
            for_btn = []
            malumotlar = str()
            for i in await db.view_list_channel(user_id, k, b):
                channel = await bot.get_chat(i[1])
                invite_link = channel.invite_link
                for_btn.append(i[0])
                malumotlar += f"\n{i[0]} - <b><a href='{invite_link}'>{channel.title}</a></b>\n➖➖➖➖➖➖➖➖"
            
            if await db.exist_user_hamkorlik(user_id) and not await db.admin_status_view(user_id):
                malumotlar2 = str()
                for i2 in await db.view_list_admin_partner(user_id, k, b):
                    channel1 = await bot.get_chat(i2[1])
                    invite_link1 = await channel1.export_invite_link()
                    for_btn.append(i2[0])
                    malumotlar2 += f"\n{i2[0]} - <b><a href='{invite_link1}'>{channel1.title}</a></b>\n➖➖➖➖➖➖➖➖"
                await message.edit_text(text=f"{information}\n<b>💎 Sizning kanallaringiz:</b>\n{malumotlar}\n<b>🤝 Hamkor kanallar:</b>\n{malumotlar2}", reply_markup=num_btn(for_btn), disable_web_page_preview=True)
            else:
                await message.edit_text(text=f"{information}\n{malumotlar}\n{information2}", reply_markup=num_btn(for_btn), disable_web_page_preview=True)
    else:
        await call.answer(text=f"💀 Siz bosgan tugmada xatolik chiqdi! - {parts[0]}", show_alert=True)

def convert_uptime(uptime):                             # Statistika uchun 
    hours = int(uptime // 3600)
    minutes = int((uptime % 3600) // 60)
    return hours, minutes

async def controll():                                 # kanalni turlash
    try:
        if 2 > await db.chanel_count():
            return True
        else:
            return False
    except:
        return False


@dp.callback_query(lambda c: c.data)
async def user_panel(call: CallbackQuery, state: FSMContext):
    me = await bot.get_me()
    btn_txt = call.data
    message = call.message
    user_id = call.message.chat.id
    print("$$$$", btn_txt)
    print(user_id)
    if await db.is_admin(user_id):              # admin SECTION
        
        if btn_txt == "admin_plus":                 # tayyor lkn username orqali admin qo'shmaydi
            await message.delete()
            if not await db.is_owner(user_id):
                await call.answer(text = "🐌 Botga adminlarni faqat Bot egasi qo'shishi mumkin!", show_alert = True)
                return
            
            uid = generate_unique_code()
            await db.add_adminCode(user_id, uid)
            await call.answer()
            await message.answer(text = f"👨‍✈️ Adminlikka tayinlamoqchi bo'lgan odamning <b>ID(🆔) raqam</b> ini kiriting, yoki ushbu kodni unga yuboring: /null", reply_markup = copy_share(uid, me.username))
            await state.set_state(for_admin.for_admin_plus)

        elif btn_txt == "force_subs":                                   # majburiy obunaga kanal qoshish
            if not await db.is_owner(user_id):
                await call.answer(text="❗️ Majburiy obunaga kanallarni faqat Bot egasi qo'sha oladi", show_alert=True)
                return
            
            await call.answer()
            await message.delete()
            await db.admin_status(user_id, "post")
            
            malumotlar_force = []
            for_btn_force = []
            
            for i in await db.vkm_stili(user_id):
                if not await db.is_majburiy_channel(i[0]):
                    channel = await bot.get_chat(i[1])
                    invite_link = channel.invite_link
                    for_btn_force.append(i[0])
                    malumotlar_force.append(f"\n<b>🔪 {i[0]} - </b><a href='{invite_link}'>{channel.title}</a>\n➖➖➖➖➖➖➖➖")
            
            if malumotlar_force:
                malumotlar_force_str = "".join(malumotlar_force)
                await bot.send_message(
                    chat_id=user_id, 
                    text=f"🧱 <b>Majburiy obunaga</b> kanal qo'shish uchun quyidagilardan birini tanlang:{malumotlar_force_str}", 
                    reply_markup=num_btn(for_btn_force, 'force'), 
                    disable_web_page_preview=True
                )
            else:
                await bot.send_message(
                    chat_id=user_id,
                    text="❗️ Qo'shish uchun mavjud bo'lmagan kanallar topilmadi. yoki hamma kanallar qo'shib bo'lindi~",
                    disable_web_page_preview=True
                )

        elif btn_txt == "force_obuna":                  # majburiy obuna paneli 
            await message.delete()  
            await call.answer()     
            if not await db.majburiy_subs_view():
                await db.status_force(0)
            await message.answer(text = f"⚙ Majburiy obuna Parametrlari:\n{'<b>Majburiy obuna: 🟢</b>' if await db.status_force() else f'<b>Majburiy obuna: 🔴</b>'}\n📢 <i>Majburiy obunaga ulangan kanallar soni: </i><code>{await db.count_majburiy()}</code>", reply_markup = majburiy_subs_on_off.as_markup())

        elif btn_txt == "force_subs_minus":                 # majburiy obunadan kanal o'chirish
            if not await db.is_owner(user_id):
                await call.answer(text="❗️ Majburiy obunaga kanallarni faqat Bot egasi o'chira oladi", show_alert=True)
                return
            
            await call.answer()
            await message.delete()
            await db.admin_status(user_id, "post")
            
            malumotlar_force = []
            for_btn_force = []
            
            for i in await db.vkm_stili(user_id, 'force_minus'):
                channel = await bot.get_chat(i[1])
                invite_link = channel.invite_link
                for_btn_force.append(i[0])
                malumotlar_force.append(f"\n<b>🔪 {i[0]} - </b><a href='{invite_link}'>{channel.title}</a>\n➖➖➖➖➖➖➖➖")
        
            if malumotlar_force:
                malumotlar_force_str = "".join(malumotlar_force)
                await bot.send_message(
                    chat_id=user_id, 
                    text=f"🧱 <b>Majburiy obuna</b>dan kanal o'chirish uchun quyidagilardan birini tanlang:{malumotlar_force_str}", 
                    reply_markup=num_btn(for_btn_force, 'force_m'), 
                    disable_web_page_preview=True
                )
            else:
                await bot.send_message(
                    chat_id=user_id,
                    text="❗️ O'chirish uchun kanallar topilmadi.",
                    disable_web_page_preview=True
                )

        elif btn_txt == "subs_off_on":              # Majburiy obunani o'chirib yoqish
            if await db.is_owner(user_id):
                if await db.majburiy_subs_view():
                    await call.answer()
                    if await db.status_force() == 1:
                        await db.status_force(0)
                    else:
                        await db.status_force(1)
                    await message.edit_text(text = f"⚙ Majburiy obuna Parametrlari:{' <b>Majburiy obuna: 🟢</b>' if await db.status_force() else ' <b>Majburiy obuna: 🔴</b>'}", reply_markup = majburiy_subs_on_off.as_markup())            
                    return
                await call.answer(text = "💭 Siz majburiy obunani yoqib qo'yolmaysiz sababi Majburiy obuna uchun kanal qo'shilmagan ❗️", show_alert = True)
            else:
                await call.answer(text = "💭 Siz majburiy obunani yoqib o'chirolmaysiz sababi Bot egasi emassiz ❗️", show_alert = True)

        elif btn_txt == "kanal_plus":               # kanallarni qoshish
            await call.answer()
            await message.delete()
            await db.admin_status(user_id)
            await message.answer(text = "➕ Qo'shmoqchi bo'lgan kanalingizning 🔗 <b>Havolasini yoki 🆔 raqam</b>ini kiriting:", reply_markup = cancel_post_btn.as_markup())
            await state.set_state(for_admin.for_channel_add)

        elif btn_txt == "kanal_minus":              # kANALLARNI DELETE QILISH
            await call.answer()
            await message.delete()
            if await db.is_add_channel(user_id):    
                await db.admin_status(user_id)
                for_btn = []
                malumotlar = str()
                m = "minus"
                for i in await db.vkm_stili(user_id):
                    channel = await bot.get_chat(i[1])
                    invite_link = channel.invite_link
                    for_btn.append(i[0])
                    malumotlar += f"\n{i[0]} - <b><a href = '{invite_link}'>{channel.title}</a></b>\n➖➖➖➖➖➖➖➖"
                await bot.send_message(chat_id = user_id, text = f"""Qaysi kanalni <b>O'chirib</b> tashlamoqchisiz❓\n{malumotlar}""", reply_markup = num_btn(for_btn, m), disable_web_page_preview=True)
                return
            await message.answer(text = "❗️ Siz botga kanal qo'shmagansiz\n❗️Hamkor kanallarni ham o'chira olmaysiz.")

            
        elif btn_txt == "adminlar":                     # ADMINLAR va adminlar haqida malumot va adminlarni bo'shatish
            await call.answer()
            for_btn_admin = []
            malumotlar_admin = str()
            username = str()
            for i in await db.vkm_stili_admin():
                admin_info = await bot.get_chat(i[1])
                for_btn_admin.append(i[0])
                if not admin_info.username:
                    malumotlar_admin += f"\n{i[0]} - <b>{admin_info.first_name}</b> , 🆔: <code>{admin_info.id}</code>\n➖➖➖➖➖➖➖➖"
                else:
                    username = admin_info.username
                    malumotlar_admin += f"\n{i[0]} - <b><a href = 'https://t.me/{username}'>{admin_info.first_name}</a></b> , 🆔: <code>{admin_info.id}</code>\n➖➖➖➖➖➖➖➖"
            await message.answer(text = f"🕸️ Agar siz <b>admin haqida ma'lumot</b> yoki <b>adminlikdan bo'shatmoqchi</b> bo'sangiz quyidagilardan birini tanlang:💨\n{malumotlar_admin}", reply_markup = num_btn_admin(for_btn_admin), disable_web_page_preview = True)

        elif btn_txt == "adminlarga_xabar":                 # Hamma adminlarga xabar yuborish
            await call.answer(text = "📌 Hozir beradigan xabaringiz hamma adminlarga yuboriladi", show_alert = True)
            await state.set_state(for_admin.for_admin_message)
            await message.answer(text = "🧮 Marhamat Xabarni kiriting: /null", reply_markup = cancel_post_btn.as_markup())

        elif btn_txt == "send":                                   # adminga xabar confirm btn
            await call.answer()
            data = await state.get_data()
            admin_msg = data['admin_msg']
            entity = data['entity']
            if (entity.lower() != "none"):
                entiy = entity.replace("[MessageEntity(", "",).replace(")]", "").replace("'", "").replace(",", "").strip()
            else:
                entiy = None
            q = 0
            w = 0
            for admins in await db.admin_view():
                try:
                    await bot.send_message(chat_id = admins, text = f"{admin_msg}\n➖➖➖➖➖\n🆔: {user_id}", entities = control_entitiy(entiy), parse_mode = None, disable_web_page_preview= True)
                    w += 1
                except Exception as e:
                    print(e)
                    q += 1
            await message.edit_reply_markup()
            await message.answer(f"📌 Bu xabarni <b>{w} ta</b> admin qabul qildi! va <b>{q} ta</b> adminga yubora olmadik.", reply_markup = builder_admin.as_markup())

        elif btn_txt == "reklama":                  # reklama qismi
            await call.answer()
            if await controll():
                await message.answer(text = f"Reklamani qayerga bermoqchisiz.❓\n📢 Ulangan kanallar soni: <code>{await db.chanel_count()}</code>", reply_markup = reklama_btn_one())
            else:
                await message.answer(text = f"Reklamani qayerga bermoqchisiz.❓\n📢 Ulangan kanallar soni: <code>{await db.chanel_count()}</code>", reply_markup = reklama_btn_two())

        elif btn_txt == "one_channel":                              # 1TA KANALDA POST
            await call.answer()
            await db.for_post_single(user_id)
            await db.admin_status(user_id, "post")
            await message.delete()
            if await db.is_add_channel(user_id) or await db.exist_user_hamkorlik(user_id):
                for_btn = []
                malumotlar = str()

                for i in await db.vkm_stili(user_id):
                    channel = await bot.get_chat(i[1])
                    invite_link = channel.invite_link
                    for_btn.append(i[0])
                    malumotlar += f"\n{i[0]} - <b><a href = '{invite_link}'>{channel.title}</a></b>\n➖➖➖➖➖➖➖➖"
                
                if await db.exist_user_hamkorlik(user_id):
                    malumotlar2 = str()
                    for i2 in await db.admin_partner(user_id):
                        channel1 = await bot.get_chat(i2[1])
                        invite_link1 = await channel1.export_invite_link()
                        for_btn.append(i2[0])
                        malumotlar2 += f"\n{i2[0]} - <b><a href = '{invite_link1}'>{channel1.title}</a></b>\n➖➖➖➖➖➖➖➖"
                    await bot.send_message(chat_id = user_id, text = f"Qaysi kanalga <b>Reklama</b> bermoqchisiz❓\n<b>💎 Sizning kanallaringiz:</b>\n{malumotlar}\n<b>🤝 Hamkor kanallar:</b>\n{malumotlar2}", reply_markup = num_btn(for_btn), disable_web_page_preview=True)
                else:
                    if await db.is_owner(user_id):
                        await bot.send_message(chat_id = user_id, text = f"Qaysi kanalga <b>Reklama</b> bermoqchisiz❓\n{malumotlar}", reply_markup = num_btn(for_btn), disable_web_page_preview=True)
                        return
                    await bot.send_message(chat_id = user_id, text = f"Qaysi kanalga <b>Reklama</b> bermoqchisiz❓\n{malumotlar}\n<i>❗️ Sizda hamkor kanallar mavjud emas</i>", reply_markup = num_btn(for_btn), disable_web_page_preview=True)
            else:
                await message.answer("🤣 <b>Siz botga post uchun kanal qo'shmagansiz</b>")

        elif btn_txt == "all_channel":              # Hamma kanallarda post
            if await db.is_owner(user_id):
                if await db.is_add_channel(user_id):
                    await call.answer()
                    await db.for_post_multiple(user_id)
                    await state.set_state(for_admin.reklama_start)
                    await message.edit_text(text = "Yangi postni yoki E'loningizni kanalga tashlash uchun <b>Qulaylik uchun Tayyor post tashlang</b>❕ yoki rasmdan boshlab post yasang:\nJarayonni to'xtatish: /null", reply_markup = cancel_post_btn.as_markup())
                    return
                await call.answer(text = "💂‍♀️ Siz hali botga kanal ulamagansiz!", show_alert = True) 
                return
            await call.answer(text = "💂‍♀️ Hamma kanallarga faqat bot egasi post yubora oladi", show_alert = True) 

        elif btn_txt == "confirm_forward":                  ## confirm_forward reklama
            await call.answer()
            await message.delete()
            try:
                if await db.for_post_is_multiple(user_id) == 'multi':
                    channels = await db.channel_view() 
                    c = 0
                    for channel  in channels:
                        c += 1
                        await bot.forward_message(chat_id = channel, from_chat_id = await db.for_ads_view(user_id)[1], message_id = await db.for_ads_view(user_id)[0])
                    await message.answer(f"Post {c} ta ulangan kanallarda muvaffaqiyatli chop etildi ✅", disable_web_page_preview=True)
                elif await db.for_post_is_multiple(user_id) == 'single':
                    await bot.forward_message(chat_id = await db.for_ads_view(user_id)[2], from_chat_id = await db.for_ads_view(user_id)[1], message_id = await db.for_ads_view(user_id)[0])
                    channel = await bot.get_chat(await db.for_ads_view(user_id)[2])
                    invite_link = channel.invite_link
                    await message.answer(f"<a href='{invite_link}'>Post 1 ta kanalda muvaffaqiyatli chop etildi ✅</a>", disable_web_page_preview=True)
                else:
                    k = 0
                    bloked = str()
                    m = 0
                    is_blocked = False
                    for users in await db.user_view():
                        try:
                            await bot.forward_message(chat_id = users, from_chat_id = await db.for_ads_view(user_id)[1], message_id = await db.for_ads_view(user_id)[0])
                            m += 1
                        except Exception as e:
                            is_blocked = True
                            ins = await bot.get_chat(users)
                            bloked += f"Ismi: {ins.first_name},\nUsername: {ins.username if ins.username else 'Username topilmadi!'},\nID: {users},\nBio: {ins.bio}\n\n===    ====    ===    ===    ===\n\n"
                            k += 1
                            print(e)
                            pass
                    if is_blocked:
                        file = StringIO()
                        file.write(bloked)
                        current_time = datetime.now(tashkent_tz)
                        soat = current_time.strftime("%Y-%m-%d %H:%M:%S")
                        await message.answer_document(document=BufferedInputFile(file = file.getvalue().encode("utf-8"), filename = f"Qora royhat.txt"), caption = f"Blok qilganlar Ro'yhati {soat}\nBotning <b>{k} ta</b> foydalanuvchisi qora ro'yhatda!\nPost <b>{m} ta</b> foydalanuvchilar orasida muvaffaqiyatli chop etildi ✅")
                await state.clear()
                await message.answer(text = f"{message.chat.first_name} -- <b>⚜️Admin aka⚜️</b> Bot xizmatlari!", reply_markup = builder_admin.as_markup())

            except Exception as e:
                await message.answer(f"Afsuski postni chop etish muvaffaqiyatsizlikka uchradi.😔\n\n<code>{e}</code>")
                print(e)
                pass

        elif btn_txt == "confirm_make_ads":        ##     confirm qo'lda reklama tayyorlash'
            await call.answer()
            msg = await message.edit_reply_markup()
            # await message.delete()
            try:
                if await db.is_type_post(user_id) == "video":
                    if await db.for_post_is_multiple(user_id) == 'multi':
                        channels = await db.channel_view() 
                        c = 0
                        for channel  in channels:
                            c += 1
                            await msg.send_copy(chat_id = channel)  # hamma kanallarda
                        await message.answer(f"Post {c} ta ulangan kanallarda muvaffaqiyatli chop etildi ✅")
                    elif await db.for_post_is_multiple(user_id) == 'single':
                        try:
                            await msg.send_copy(chat_id = await db.for_post_view(user_id)[3])  # confirmation make own ads  shu qismi va tugmacha qoshish qismi !!!
                            channel = await bot.get_chat(await db.for_post_view(user_id)[3])
                            invite_link = channel.invite_link
                            await message.answer(f"<a href='{invite_link}'>Post 1 ta kanalda muvaffaqiyatli chop etildi ✅</a>", disable_web_page_preview=True)
                        except Exception as e:
                            print(e)
                            await message.answer(f"Kanal uchun yasalgan postni chop etishda xatolik.\n\n<code>{e}</code>")
                    else:
                        try:
                            k = 0
                            m = 0
                            bloked = str()
                            is_blocked = False
                            for users in await db.user_view():
                                try:
                                    await msg.send_copy(chat_id = users)
                                    m += 1
                                except Exception as e:
                                    is_blocked = True
                                    k += 1
                                    ins = await bot.get_chat(users)
                                    bloked += f"Ismi: {ins.first_name},\nUsername: {ins.username if ins.username else 'Username topilmadi!'},\nID: {users},\nBio: {ins.bio}\n\n===    ====    ===    ===    ===\n\n"
                                    print(e)
                                    pass
                            if is_blocked:
                                file = StringIO()
                                file.write(bloked)
                                current_time = datetime.now(tashkent_tz)
                                soat = current_time.strftime("%Y-%m-%d %H:%M:%S")
                                await message.answer_document(document=BufferedInputFile(file = file.getvalue().encode("utf-8"), filename = f"Qora royhat.txt"), caption = f"Blok qilganlar Ro'yhati {soat}\nBotning <b>{k} ta</b> foydalanuvchisi qora ro'yhatda!\nPost <b>{m} ta</b> foydalanuvchilar orasida muvaffaqiyatli chop etildi ✅")
                            await state.clear()
                        except Exception as e:
                            print(e)
                            await message.answer(f"Afsuski postni chop etish muvaffaqiyatsizlikka uchradi.😔\n\n<code>{e}</code>")
                            pass
                elif await db.is_type_post(user_id) == "photo":
                    if await db.for_post_is_multiple(user_id) == 'multi':
                        channels = await db.channel_view()
                        c = 0
                        for channel  in channels:
                            c += 1
                            await msg.send_copy(chat_id = channel)  # hamma kanallarda
                        await message.answer(f"Post {c} ta ulangan kanallarda muvaffaqiyatli chop etildi ✅")
                    elif await db.for_post_is_multiple(user_id) == 'single':
                        try:
                            await msg.send_copy(chat_id = await db.for_post_view(user_id)[3])  # confirmation make own ads  shu qismi va tugmacha qoshish qismi !!!
                            channel = await bot.get_chat(await db.for_post_view(user_id)[3])
                            invite_link = channel.invite_link
                            await message.answer(f"<a href='{invite_link}'>Post 1 ta kanalda muvaffaqiyatli chop etildi ✅</a>", disable_web_page_preview=True)
                        except Exception as e:
                            print(e)
                            await message.answer(f"Kanal uchun yasalgan postni chop etishda xatolik.\n\n<code>{e}</code>")
                            pass
                    else:
                        try:
                            k = 0
                            m = 0
                            bloked = str()
                            is_blocked = False
                            for users in await db.user_view():
                                try:
                                    await msg.send_copy(chat_id = users)
                                    m += 1
                                except Exception as e:
                                    is_blocked = True
                                    k += 1
                                    ins = await bot.get_chat(users)
                                    bloked += f"Ismi: {ins.first_name},\nUsername: {ins.username if ins.username else 'Username topilmadi!'},\nID: {users},\nBio: {ins.bio}\n\n===    ====    ===    ===    ===\n\n"
                                    print(e)
                                    pass
                                
                            if is_blocked:    
                                file = StringIO()
                                file.write(bloked)
                                current_time = datetime.now(tashkent_tz)
                                soat = current_time.strftime("%Y-%m-%d %H:%M:%S")
                                await message.answer_document(document=BufferedInputFile(file = file.getvalue().encode("utf-8"), filename = f"Qora royhat.txt"), caption = f"Blok qilganlar Ro'yhati {soat}\nBotning <b>{k} ta</b> foydalanuvchisi qora ro'yhatda!\nPost <b>{m} ta</b> foydalanuvchilar orasida muvaffaqiyatli chop etildi ✅")
                    
                            await state.clear()
                        except Exception as e:
                            print(e)
                            await message.answer(f"Afsuski postni chop etish muvaffaqiyatsizlikka uchradi.😔\n\n<code>{e}</code>")
                            pass
                    
                elif await db.is_type_post(user_id) == "document":
                    if await db.for_post_is_multiple(user_id) == 'multi':
                        channels = await db.channel_view()
                        c = 0
                        for channel  in channels:
                            c += 1
                            await msg.send_copy(chat_id = channel)  # hamma kanallarda
                        await message.answer(f"Post {c} ta ulangan kanallarda muvaffaqiyatli chop etildi ✅")
                    elif await db.for_post_is_multiple(user_id) == 'single':
                        try:
                            await msg.send_copy(chat_id = await db.for_post_view(user_id)[3])  # confirmation make own ads  shu qismi va tugmacha qoshish qismi !!!
                            channel = await bot.get_chat(await db.for_post_view(user_id)[3])
                            invite_link = channel.invite_link
                            await message.answer(f"<a href='{invite_link}'>Post 1 ta kanalda muvaffaqiyatli chop etildi ✅</a>", disable_web_page_preview=True)
                        except Exception as e:
                            print(e)
                            await message.answer(f"Kanal uchun yasalgan postni chop etishda xatolik.\n\n<code>{e}</code>")
                    else:
                        try:
                            k = 0
                            m = 0
                            bloked = str()
                            is_blocked = False
                            for users in await db.user_view():
                                try:
                                    await msg.send_copy(chat_id = users)
                                    m += 1
                                except Exception as e:
                                    is_blocked = True
                                    k += 1
                                    ins = await bot.get_chat(users)
                                    bloked += f"Ismi: {ins.first_name},\nUsername: {ins.username if ins.username else 'Username topilmadi!'},\nID: {users},\nBio: {ins.bio}\n\n===    ====    ===    ===    ===\n\n"
                                    print(e)
                                    pass
                            if is_blocked:
                                file = StringIO()
                                file.write(bloked)
                                current_time = datetime.now(tashkent_tz)
                                soat = current_time.strftime("%Y-%m-%d %H:%M:%S")
                                await message.answer_document(document=BufferedInputFile(file = file.getvalue().encode("utf-8"), filename = f"Qora royhat.txt"), caption = f"Blok qilganlar Ro'yhati {soat}\nBotning <b>{k} ta</b> foydalanuvchisi qora ro'yhatda!\nPost <b>{m} ta</b> foydalanuvchilar orasida muvaffaqiyatli chop etildi ✅")

                            await state.clear()
                        except Exception as e:
                            print(e)
                else:
                    try:
                        if await db.is_type_post(user_id) == "text":
                            if await db.for_post_is_multiple(user_id) == "multi":
                                channels = await db.channel_view() 
                                c = 0
                                for channel  in channels:
                                    c += 1
                                    await msg.send_copy(chat_id = channel)  # hamma kanallarda
                                await message.answer(f"Post {c} ta ulangan kanallarda muvaffaqiyatli chop etildi ✅")
                            elif await db.for_post_is_multiple(user_id) == 'single':
                                try:
                                    await msg.send_copy(chat_id = await db.for_post_view(user_id)[3])  # confirmation make own ads  shu qismi va tugmacha qoshish qismi !!!
                                    channel = await bot.get_chat(await db.for_post_view(user_id)[3])
                                    invite_link = channel.invite_link
                                    await message.answer(f"<a href='{invite_link}'>Post 1 ta kanalda muvaffaqiyatli chop etildi ✅</a>", disable_web_page_preview=True)
                                except Exception as e:
                                    print(e)
                                    await message.answer(f"Kanal uchun yasalgan postni chop etishda xatolik.\n\n<code>{e}</code>")
                            
                            else:
                                try:
                                    k = 0
                                    m = 0
                                    bloked = str()
                                    is_blocked = False
                                    for users in await db.user_view():
                                        try:
                                            await msg.send_copy(chat_id = users)
                                            m += 1
                                        except Exception as e:
                                            is_blocked = True
                                            k += 1
                                            ins = await bot.get_chat(users)
                                            bloked += f"Ismi: {ins.first_name},\nUsername: {ins.username if ins.username else 'Username topilmadi!'},\nID: {users},\nBio: {ins.bio}\n\n===    ====    ===    ===    ===\n\n"
                                            print(e)
                                            pass
                                        
                                    if is_blocked:
                                        file = StringIO()
                                        file.write(bloked)
                                        current_time = datetime.now(tashkent_tz)
                                        soat = current_time.strftime("%Y-%m-%d %H:%M:%S")
                                        await message.answer_document(document=BufferedInputFile(file = file.getvalue().encode("utf-8"), filename = f"Qora royhat.txt"), caption = f"Blok qilganlar Ro'yhati {soat}\nBotning <b>{k} ta</b> foydalanuvchisi qora ro'yhatda!\nPost <b>{m} ta</b> foydalanuvchilar orasida muvaffaqiyatli chop etildi ✅")
                    
                                    await state.clear()
                                except Exception as e:
                                    print(e)
                    except Exception as e:
                        await message.answer(f"Kanal uchun yasalgan postni chop etishda xatolik.\n\n<code>{e}</code>")
                        pass
                await message.answer(text = f"{message.chat.first_name} -- <b>⚜️Admin aka⚜️</b> Bot xizmatlari!", reply_markup = builder_admin.as_markup())


            except Exception as e:
                    await message.answer(f"Afsuski postni chop etish muvaffaqiyatsizlikka uchradi.😔\n\n<code>{e}</code>")
                    print(e)
                    pass

        elif btn_txt == "add_btn":              ##  REKLAMAGA tugmachalar qo'shish
            await call.answer()
            await message.answer_video(video = "https://t.me/baza_java_strong/257", caption = "➕ Yangi tugma qo'shish uchun quyidagi videoda ko'rsatilgandek qiling!👆\nOrasida bo'sh joy qolmasin! - Admin-https://t.me/java_strong kabi\n<b>‼️ Tugmalarni kiritganda post shu zahoti chop etiladi.⚠</b>\n/null", reply_markup = cancel_post_btn.as_markup())
            await state.set_state(for_admin.for_btn)    #  salom = https, qalay = https

        elif btn_txt == "in_bot":           # Bot ichida reklama
            await call.answer()
            await db.for_post_bot(user_id)
            await state.set_state(for_admin.reklama_start)
            await message.edit_text(text = "Yangi postni yoki E'loningizni kanalga tashlash uchun <b>Qulaylik uchun Tayyor post tashlang</b>❕ yoki rasmdan boshlab post yasang:\nJarayonni to'xtatish: /null", reply_markup = cancel_post_btn.as_markup())

        elif btn_txt == "delete_admin":                                 # Adminlarni o'chirish
            try:
                if await db.is_owner(user_id) or str(user_id) == str(await db.get_malumot_admin(await db.save_info_view(user_id))):
                    if str(await db.owner_view()) == str(await db.get_malumot_admin(await db.save_info_view(user_id))):
                        await call.answer(text = "🙅‍♂️ Bot egasi hech qanchon oddiy statusga tushmaydi!", show_alert = True)
                        return
                    if str(user_id) == str(await db.get_malumot_admin(await db.save_info_view(user_id))) or not(await db.is_owner(user_id)):
                        await call.answer(text = "😂 Siz o'zingizni muvaffaqiyatli Adminlikdan chiqardingiz. 🤣", show_alert = True)
                    else:
                        await call.answer(text = "🧬 Admin muvaffaqiyatli o'chirib tashlandi.", show_alert = True)
                    await db.del_admin(await db.save_info_view(user_id))
                else:
                    await call.answer(text = "🙊 Kechirasiz, Adminlarni faqat Bot egasi bo'shata oladi!", show_alert = True)
                await message.edit_reply_markup()
            except:
                await call.answer(text = "🙊 Kechirasiz, Adminlikdan bo'shatishda xatolik chiqdi! yoki allaqachon adminlikdan bo'shatilgan!", show_alert = True)

        elif btn_txt == "hamkorlik":
            await call.answer()
            await message.edit_text(text = "🛠 Hamkorlik parametri:", reply_markup = hamkorlik.as_markup())
            
        elif btn_txt == "add_hamkor":
            await call.answer()
            for_btn_admin = []
            malumotlar_admin = []
            
            for i in await db.vkm_stili_admin():
                admin_id, admin_name = i[1], i[0]
                if user_id == admin_id or await db.exist_two_of_us(user_id, admin_id):
                    continue
                
                admin_info = await bot.get_chat(admin_id)
                username = admin_info.username if admin_info.username else ''
                admin_link = f"<a href='https://t.me/{username}'>{admin_info.first_name}</a>" if username else admin_info.first_name
                admin_details = f"\n{admin_name} - <b>{admin_link}</b>, 🆔: <code>{admin_info.id}</code>\n➖➖➖➖➖➖➖➖"
                
                for_btn_admin.append(admin_name)
                malumotlar_admin.append(admin_details)
            
            if malumotlar_admin:
                await message.answer(
                    text=f"🕸️ Agar siz <b>Adminlardan birini Hamkor</b> qilmoqchi bo'lsangiz quyidagilardan birini tanlang:💨\n{''.join(malumotlar_admin)}",
                    reply_markup=num_btn_admin(for_btn_admin, "hamkor"),
                    disable_web_page_preview=True
                )
            else:
                await message.answer(
                    text="🕸️ Sizda <b>hamma adminlar hamkorlik qilyapti</b> yoki <b>adminlar</b> mavjud emas ❗️"
                )

        elif btn_txt == "remove_hamkor":
            await call.answer()
            for_btn_admin = []
            malumotlar_admin = []
            
            for i in await db.admin_partner_view(user_id):
                admin_id, admin_name = i[1], i[0]
                                
                admin_info = await bot.get_chat(admin_id)
                username = admin_info.username if admin_info.username else ''
                admin_link = f"<a href='https://t.me/{username}'>{admin_info.first_name}</a>" if username else admin_info.first_name
                admin_details = f"\n{admin_name} - <b>{admin_link}</b>, 🆔: <code>{admin_info.id}</code>\n➖➖➖➖➖➖➖➖"
                
                for_btn_admin.append(admin_name)
                malumotlar_admin.append(admin_details)
            
            if malumotlar_admin:
                await message.answer(
                    text=f"🕸️ Agar siz <b>Adminlardan birini Hamkorlikdan o'chirmoqchi</b> bo'lsangiz quyidagilardan birini tanlang:💨\n{''.join(malumotlar_admin)}",
                    reply_markup=num_btn_admin(for_btn_admin, "hamkor_m"),
                    disable_web_page_preview=True
                )
            else:
                await message.answer(
                    text="🕸️ Sizda <b>hamkorlar yo'q</b>❗️"
                )

        elif btn_txt == "confirm_refuse":                       # Confirm REFUSE
            await call.answer()
            try:
                await state.clear()
            except Exception as e:
                print(e)
                pass
            await call.answer(text = "Post rad etildi", show_alert = True)
            await message.edit_reply_markup()
            await message.answer(text = f"{message.chat.first_name} -- <b>⚜️Admin aka⚜️</b> Bot xizmatlari!", reply_markup = builder_admin.as_markup())

        elif btn_txt == "statistika":                           # Statistika
            await call.answer()
            _uptime = time.time() - START_TIME
            _hours, _minutes = convert_uptime(_uptime)
            last24 = await db.last24_user_view()
            await message.edit_text(text=f"""👥 Botdagi obunachilar:  {await db.user_count()} ta\n\n🔜 Oxirgi 24 soatda: {last24[0]} ta obunachi qo'shildi\n🔝 Oxirgi 1 oyda: {last24[1]} ta obunachi qo'shildi\n📆 Bot ishga tushganiga: {_hours} soat va {_minutes} daqiqa bo'ldi ({int(_hours)%24} kun)\n\n📊  @{me.username} statistikasi\n\nReklama uchun:👉 @java_strong""", reply_markup=back.as_markup())

        elif btn_txt == "base":                          # bot bazasi
            if not await db.is_owner(user_id):
                await call.answer(text = "🗿 Botning bazasini faqat Bot egasi yuklab olishi mumkin!", show_alert = True)
                return
            await call.answer()
            try:
                await bot.send_document(chat_id=user_id, document=FSInputFile(path='data/database.sqlite3', filename='database.sqlite3'))
            except Exception as e:
                await message.answer(text = f"<b>⚠ Diqqat (error) !</b>\n{e}")
                print(e)
                pass

        elif btn_txt == "back" or btn_txt == "orqaga":          # Orqaga tugmasi
            await call.answer()
            await message.edit_text(text = f"{message.chat.first_name} -- <b>⚜️Admin aka⚜️</b> Assalom-u alaykum Bot xizmatingizda!", reply_markup = builder_admin.as_markup())
            


        elif btn_txt.startswith("back:"):          # Orqaga tugmasi
            await call.answer()
            btn_txt = btn_txt.split("back:")[1]
            await message.edit_reply_markup(reply_markup=user_management_inline_keyboard(int(btn_txt), "uz"))
            

                                                # pagination left and right
        
        elif btn_txt == '0':
            await call.answer()
            await call.message.delete()
            
        elif "__" in btn_txt or "info_" in btn_txt:
            await process_admin_pagination(call, btn_txt)
            
        elif "##" in btn_txt or "_kanal" in btn_txt: # kanallar uchun max pagination tugmasi
            await process_channel_pagination(message, call, btn_txt, user_id)

        elif "_minus" in btn_txt: # kanallar uchun min pagination tugmasi
            await process_channel_del_pagination(message, call, btn_txt, user_id)

        elif ("_force@max_channel" in btn_txt and btn_txt.split("_force@")[1] == "max_channel") or ("_force@min_channel" in btn_txt and btn_txt.split("_force@")[1] == "min_channel"):
            direction = btn_txt.split("_force@")[1]
            id_part = btn_txt.split("_force@")[0]

            if id_part.isdigit():
                id_num = int(id_part)
                if direction == "max_channel":
                    k = int(id_num) + 1
                    b = int(id_num) + 8
                    check_func = await db.is_max_channel
                    end_message = "🛎️ Siz so'ngi sahifadasiz!"
                elif direction == "min_channel":
                    k = int(id_num) - 1
                    b = int(id_num) - 8
                    check_func = await db.is_min_channel
                    end_message = "🛎️ Siz birinchi sahifadasiz!"

                if not (check_func() == id_num):
                    await call.answer()
                    information = "🧱 <b>Majburiy obuna</b>dan kanal o'chirish uchun quyidagilardan birini tanlang:"
                    for_btn = []
                    malumotlar = str()
                    for i in await db.view_list_majburiy(k, b):
                        channel = await bot.get_chat(i[1])
                        invite_link = channel.invite_link
                        for_btn.append(i[0])
                        malumotlar += f"\n{i[0]} - <b><a href = '{invite_link}'>{channel.title}</a></b>\n➖➖➖➖➖➖➖➖"
                    await message.edit_text(text=f"{information}\n{malumotlar}", reply_markup=num_btn(for_btn, "force"), disable_web_page_preview=True)
                else:
                    await call.answer(text=end_message, show_alert=True)
            else:
                await call.answer(text=f"💀 Siz bosgan tugmada xatolik chiqdi! - {id_part}", show_alert=True)

        elif "_forcement@" in btn_txt:
            command, action = btn_txt.split("_forcement@")
            
            if command.isdigit():
                id_num = int(command)
                
                if action == "min_channel":
                    k = int(id_num) - 1
                    b = int(id_num) - 8
                    bound_check = await db.is_min_majburiy()
                    bound_message = "🛰 Siz 1-sahifadasiz"
                elif action == "max_channel":
                    k = int(id_num) + 1
                    b = int(id_num) + 8
                    bound_check = await db.is_max_majburiy()
                    bound_message = "🛎️ Siz so'ngi sahifadasiz"
                else:
                    await call.answer(text=f"💀 Siz bosgan tugmada xatolik chiqdi! - {command}", show_alert=True)
                    return

                if id_num == int(bound_check):
                    await call.answer(text=bound_message, show_alert=True)
                else:
                    await call.answer()
                    information = "🧱 <b>Majburiy obuna</b>dan kanal o'chirish uchun quyidagilardan birini tanlang:"
                    for_btn = []
                    malumotlar = str()
                    
                    for i in await db.view_list_majburiy(k, b):
                        channel = await bot.get_chat(i[1])
                        invite_link = channel.invite_link
                        for_btn.append(i[0])
                        malumotlar += f"\n{i[0]} - <b><a href='{invite_link}'>{channel.title}</a></b>\n➖➖➖➖➖➖➖➖"
                    
                    await message.edit_text(
                        text=f"{information}\n{malumotlar}", 
                        reply_markup=num_btn(for_btn, "force_m"), 
                        disable_web_page_preview=True
                    )
            else:
                await call.answer(text=f"💀 Siz bosgan tugmada xatolik chiqdi! - {command}", show_alert=True)

        elif ("%max-admin" in btn_txt) or ("_hamkor-min-admin" in btn_txt):
            await process_hamkor_pagination(call, btn_txt)
            
        elif ("&&max-admin" in btn_txt) or ("_removeHamkor!!min-admin" in btn_txt):
            await process_hamkor_minus_pagination(call, btn_txt)
            


        elif btn_txt.startswith("edit:"):
            btn_txt = btn_txt.split("edit:")[1]
            await call.answer()
            await message.edit_reply_markup(reply_markup=edit_keyboard(int(btn_txt)).as_markup())
            
        elif btn_txt.startswith("delete:"):
            btn_txt = btn_txt.split("delete:")[1]
            await call.answer()
            await message.edit_reply_markup(reply_markup=delete_keyboard(int(btn_txt)).as_markup())
            
        elif btn_txt.startswith("confirm_delete:"):
            btn_txt = btn_txt.split("confirm_delete:")[1]
            try:
                await call.answer("✅ Foydalanuvchi muvaffaqiyatli o'chirildi.", show_alert=True)
                await db.delete_user_by_row_id(int(btn_txt))
                await message.edit_reply_markup(reply_markup=None)
            except Exception as e:
                await call.answer(f"❌ Foydalanuvchini o'chirishda xatolik yuz berdi. {e}", show_alert=True)
                print(e)
                pass

        elif btn_txt.startswith("edit_"):
            edit_type = btn_txt.split("edit_")[1]
            user_id_to_edit = btn_txt.split(":")[-1]
            await call.answer()
            await state.set_state(EditUserDataStates.editing_user_data)
            await state.update_data(edit_user_id=int(user_id_to_edit), edit_type=edit_type)
            await message.edit_reply_markup(reply_markup=None)
            await message.answer("Iltimos, yangi ma'lumotni kiriting:", reply_markup=back_keyboard())

    
            
            
#----------------------------    USER SECTION --------------------------


    # else: