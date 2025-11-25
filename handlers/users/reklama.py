import asyncio
import logging
from io import StringIO
from datetime import datetime
from typing import Optional, Dict, List, Tuple

import pytz
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.types import ContentType, BufferedInputFile

from loader import dp, bot
from data.Async_sqlDataBase import data_db as db
from states.all_states import for_admin
from keyboards.inline.admin_page import (
    builder_admin, btn_create, str_to_dict, control_entitiy,
    cancel_and_del, cancel_post_btn, numbee, confirm_forward, confirm_make_ads
)

logger = logging.getLogger(__name__)
tashkent_tz = pytz.timezone("Asia/Tashkent")

# Constants
STOP_COMMAND = "/null"
SUCCESS_MSG = "✅ Post muvaffaqiyatli chop etildi."
BLOCKED_USERS_FILENAME = "Qora royhat.txt"

@dp.callback_query(numbee.filter())
async def callbacks_num_change_fab(callback: types.CallbackQuery, callback_data: numbee, state: FSMContext) -> None:
    """Kanal tanlash va admin operatsiyalari"""
    message = callback.message
    btn_id = callback_data.id
    logger.debug(f"Callback pressed: {btn_id}")

    if "_kanal" in btn_id and btn_id.split("_")[0].isdigit() and btn_id.split("_")[1] == "kanal":                                  ##   Kanal tanlash
        await callback.answer()
        btn_id = int(btn_id.split("_")[0])
        chan = await db.get_malumot(btn_id)
        await db.choosen_channel(message.chat.id,chan)
        await state.set_state(for_admin.reklama_start)
        await message.edit_text(text = "Yangi postni yoki E'loningizni kanalga tashlash uchun <b>Qulaylik uchun Tayyor post tashlang</b>❕ yoki rasmdan boshlab post yasang:\nJarayonni to'xtatish: /null", reply_markup = cancel_post_btn.as_markup())

    elif "info" in btn_id:
        await callback.answer()
        await message.delete()
        btn_id = int(btn_id.split("info")[0])
        await db.save_info(btn_id, callback.message.chat.id)
        admin_id = await db.get_malumot_admin(btn_id)
        admin_info = await bot.get_chat(admin_id)
        if await db.is_add_channel(admin_id):
            malumot_channels = str()
            for kanals in await db.channel_view_byID(admin_id):
                kanal = await bot.get_chat(kanals)
                title = kanal.title
                link = kanal.invite_link
                malumot_channels += f"\n<a href = '{link}'>{title}</a>\n➖➖➖➖➖➖"
        else:
            malumot_channels = "<i>❗️ Bu foydalanuvchi kanal qo'shmagan.</i>"
        if not admin_info.photo is None:
            user_profile_photos = await bot.get_user_profile_photos(admin_id)
            photo = user_profile_photos.photos[0][-1]  # Correct way to access the photo
            await message.answer_photo(photo=photo.file_id, caption = f"🫴 Ismi: <b>{admin_info.first_name}</b>\n🦄 Username: <b>@{admin_info.username if admin_info.username else 'Username mavjud emas.'}</b>\n🧩 Biografiya: <b>{admin_info.bio if admin_info.bio else 'Biografiya yozilmagan.'}</b>\n🆔 ID: <b>{admin_info.id}\nFoydalanuvchining kanallari:</b>{malumot_channels}", reply_markup = cancel_and_del.as_markup())
            return
        await message.answer(text = f"🫴 Ismi: <b>{admin_info.first_name}</b>\n🦄 Username: <b>@{admin_info.username if admin_info.username else 'Username mavjud emas.'}</b>\n🧩 Biografiya: <b>{admin_info.bio if admin_info.bio else 'Biografiya yozilmagan.'}</b>\n🆔 ID: <b>{admin_info.id}\nFoydalanuvchining kanallari:</b>{malumot_channels}", reply_markup = cancel_and_del.as_markup(), disable_web_page_preview = True)

    elif "_minus" in btn_id and btn_id.split("_")[0].isdigit() and btn_id.split("_")[1] == "minus":
        await callback.answer()
        btn_id = int(btn_id.split("_")[0])
        chan = await db.get_malumot(btn_id)
        channel = await bot.get_chat(chan)
        await db.remove_channel(btn_id)
        invite_link = await channel.export_invite_link()
        await message.delete()
        await message.answer(text = f"<b>Siz</b> <a href='{invite_link}'>{channel.title}</a> <b>kanalini o'chirib tashladingiz 🩸</b>", reply_markup = builder_admin.as_markup(), disable_web_page_preview = True)

    elif ("_force@" in btn_id):
        btn_id = int(btn_id.split("_force@")[0])
        if await db.is_channel("1280", btn_id):
            if await db.is_majburiy_channel(btn_id):
                await callback.answer(text = "🐡 Ushbu kanal allaqachon Majburiy obuna kanallari orasida mavjud.", show_alert = True)
                return
            await db.add_majburiy_channel(btn_id)
            await callback.answer(text = f"🥳 Tabriklayman siz ushbu kanalni majburiy obuna kanallari orasiga qo'shdingiz!", show_alert = True)
            await message.edit_text(text = "🥳 <b>Tabriklayman siz ushbu kanalni majburiy obuna kanallari orasiga qo'shdingiz!!</b>", reply_markup = builder_admin.as_markup())
        else:
            await callback.answer(text = "🪛 Xato kod kiritdingiz va u 🧦 bazadan topilmadi\n🔂 Qayta kiriting.", show_alert = True)

    elif ("_forcement@" in btn_id):
        btn_id = int(btn_id.split("_forcement@")[0])
        if await db.is_between_majburiy(btn_id):
            await message.delete()
            await callback.answer("🎳 Ushbu kanal majburiy obuna kanallari orasidan o'chirildi!", show_alert = True)
            await db.remove_majburiy_channel(btn_id)
            if not await db.majburiy_subs_view():
                await db.status_force(0)
            return
        await callback.answer(text = "🪛 Xato kod kiritdingiz va u 🧦 bazadan topilmadi\n🔂 Qayta kiriting.", show_alert = True)

    elif "_hamkor" in btn_id:
        btn_id = int(btn_id.split("_")[0])
        admin_id = await db.get_malumot_admin(btn_id)
        chat_id = message.chat.id
        admin_ismi = await bot.get_chat(admin_id)
        admin2_ismi = await bot.get_chat(chat_id)
        if not chat_id == admin_id:
            await message.delete()
            try:
                await db.plus_partner(chat_id, admin_id)
                await callback.answer(text = f"🪖 Siz {admin_ismi.first_name} ni hamkorlaringiz orasiga qo'shdingiz!", show_alert = True)
                await bot.send_video(chat_id = admin_id, video = "https://t.me/baza_java_strong/259")
                if admin2_ismi.username:
                    await bot.send_message(
                        chat_id=admin_id,
                        text=(
                            f"🤝 <b>Yangi Hamkorlik!</b>\n\n"
                            f"👤 Siz <a href='https://t.me/{admin2_ismi.username}'>{admin2_ismi.first_name}</a> ning <b>Hamkori</b> bo‘ldingiz.\n"
                            f"🆔 Hamkor ID: <code>{chat_id}</code>"
                        ),
                        disable_web_page_preview=True
                    )

                    return
                await bot.send_message(
                    chat_id=admin_id,
                    text=(
                        f"🥳 <b>Tabriklaymiz!</b>\n\n"
                        f"👤 Siz <b>{admin2_ismi}</b> ning <b>Hamkori</b> bo‘ldingiz!\n"
                        f"🆔 Hamkor ID: <code>{chat_id}</code>"
                    ),
                    disable_web_page_preview=True
                )
                return
            except Exception as e:
                await message.answer(f"Ushbu foydalanuvchi qora royhatda!\n\n<code>{e}</code>")
                pass
        await callback.answer(text = "Siz o'zingizni hamkor qila olmaysiz!", show_alert = True)
        
    elif "_removeHamkor" in btn_id:
        await message.delete()
        btn_id = int(btn_id.split("_")[0])
        admin_id = await db.get_malumot_hamkorlik(btn_id)
        chat_id = message.chat.id
        admin_ismi = await bot.get_chat(admin_id)
        if await db.is_exist_id(btn_id):
            await db.remove_partner(btn_id)
            await callback.answer(text = f"�� Siz {admin_ismi.first_name} ni hamkorlaringiz orasidan o'chirdingiz!", show_alert = True)
            return
        await callback.answer(text = f"Bu ID raqam bazadan topilmadi!", show_alert = True)
        
                

async def is_forwarded_message(message: types.Message) -> bool:                         # Forward yoki yoqligini tekshirish 
    if message.forward_from or message.forward_from_chat:
        return True
    else:
        return False


@dp.message(for_admin.reklama_start)            # Reklamani qabul qilish qismi
async def reklama_start(message: types.Message, state: FSMContext):
    msg = message.text
    user_id = message.chat.id
    if (message.content_type != ContentType.ANIMATION) or (message.content_type != ContentType.STICKER):
        if await is_forwarded_message(message):                                     ####  Message Forward
            try:
                if not message.forward_from:                                    ## shaxsiy chatdan forward qilmaydi
                    message_idx = message.forward_origin.message_id
                    forward_from_chat_id = message.forward_from_chat.id
                    if await db.for_post_is_multiple(user_id) == 'multi':
                        await bot.forward_message(chat_id = user_id, from_chat_id = forward_from_chat_id, message_id = message_idx)
                        await message.answer(text = f"Shu postni hamma kanallarga yubormoqchimisiz?", reply_markup = confirm_forward.as_markup())
                        await db.for_ads(user_id,message_idx,forward_from_chat_id,None)
                        await state.clear()
                        
                    elif await db.for_post_is_multiple(user_id) == 'single':
                        await db.for_ads(user_id,message_idx,forward_from_chat_id,await db.choosen_channel_view(user_id))
                        channel = await bot.get_chat(await db.choosen_channel_view(user_id))
                        invite_link = await channel.export_invite_link()
                        await bot.forward_message(chat_id = user_id, from_chat_id = forward_from_chat_id, message_id = message_idx)
                        await message.answer(text = f"Shu postni <a href='{invite_link}'>{channel.title}</a> ga yubormoqchimisiz?", reply_markup = confirm_forward.as_markup())
                        await state.clear()
                    else:
                        await db.for_ads_bot(user_id,message_idx,forward_from_chat_id)
                        await bot.forward_message(chat_id = user_id, from_chat_id = forward_from_chat_id, message_id = message_idx)
                        await message.answer(text = f"Shu postni <b>bot obunachilariga</b> yubormoqchimisiz?", reply_markup = confirm_forward.as_markup())
                        await state.clear()
                else:
                    await message.reply(text = "‼️ <b>Bot faqat ommaviy kanallar va guruhlardan reklamani forward qiladi.</b>\nBu xabar shaxsiy chatlardan kelgan...\n🆕 Boshqa postni ommaviy kanallardan forward qiling !\nJarayonni to'xtatish: /null", reply_markup = cancel_post_btn.as_markup())
            except Exception as e:
                logger.error(f"Forward error: {e}", exc_info=True)
                await message.reply(f"🫥 Boshqa post yuboring.\nBu postni forward qilib bo'lmaydi!\n\n<code>{e}</code>")
        else:                                                       ##    Reklama yasash
            if  (message.content_type != ContentType.ANIMATION) and (message.content_type != ContentType.STICKER):
                photo = message.photo
                document = message.document
                video = message.video
                txt = message.text
                caption = message.caption
                caption_entitiy = message.caption_entities
                if photo:
                    if caption is None:                                                 #  Caption bo'lmasa'
                        await state.update_data(photo_id = photo[-1].file_id)
                        await message.reply(text = "Rasm saqlandi ✅\n<b>📝 Rasm tagidagi xabarni kiriting:(caption)</b>\nJarayonni to'xtatish: /null", reply_markup = cancel_post_btn.as_markup())
                        await state.set_state(for_admin.for_caption)
                    else:                                                                 # Tayyoe post captionli
                        await state.clear()
                        await db.for_post_with_caption(user_id, photo[-1].file_id, caption, f"{caption_entitiy}", "photo")
                        await message.reply_photo(photo = photo[-1].file_id, caption = caption, caption_entities = caption_entitiy, parse_mode = None,reply_markup = confirm_make_ads.as_markup())

                elif document:
                    if caption is None:                                                 #  Caption bo'lmasa'
                        await state.update_data(document_id = document.file_id)
                        await message.reply(text = "Documnet saqlandi ✅\n<b>📝 Document tagidagi xabarni kiriting:(caption)</b>\nJarayonni to'xtatish: /null", reply_markup = cancel_post_btn.as_markup())
                        await state.set_state(for_admin.for_caption)
                    else:                                                                 # Tayyoe post captionli
                        await state.clear()
                        await db.for_post_with_caption(user_id, document.file_id, caption, f"{caption_entitiy}", "document")
                        await message.reply_document(document = document.file_id, caption = caption, caption_entities = caption_entitiy, parse_mode = None,reply_markup = confirm_make_ads.as_markup())
                elif video:
                    if caption is None:                                                 #  Caption bo'lmasa'
                        await state.update_data(video_id = video.file_id)
                        await message.reply(text = "Video saqlandi ✅\n<b>📝 Video tagidagi xabarni kiriting:(caption)</b>\nJarayonni to'xtatish: /null", reply_markup = cancel_post_btn.as_markup())
                        await state.set_state(for_admin.for_caption)
                    else:                                                                 # Tayyoe post captionli
                        await state.clear()
                        await db.for_post_with_caption(user_id, video.file_id, caption, f"{caption_entitiy}", "video")
                        await message.reply_video(video = video.file_id, caption = caption, caption_entities = caption_entitiy, parse_mode = None,reply_markup = confirm_make_ads.as_markup())
                else:
                    if msg.lower() == "/null":                      # STOP
                        await message.delete()
                        await state.clear()
                        await message.answer(text = f"{message.chat.first_name} -- <b>⚜️Admin aka⚜️</b> Assalom-u alaykum Bot xizmatingizda!", reply_markup = builder_admin.as_markup())

                        return
                    await state.update_data(text = txt, enty = f"{message.entities}")
                    await db.for_elon(user_id, txt, f"{message.entities}", "text")
                    await message.reply(text = "📝 Xabar saqlandi ✅")
                    await message.answer(text = txt, entities = message.entities, parse_mode = None, reply_markup = confirm_make_ads.as_markup())
                    await state.clear()
                # await message.reply("Posting xabari.")
    else:
        try:
            if msg.lower() == "/null":                      # STOP
                await message.delete()
                await state.clear()
                await message.answer(text = f"{message.chat.first_name} -- <b>⚜️Admin aka⚜️</b> Assalom-u alaykum Bot xizmatingizda!", reply_markup = builder_admin.as_markup())
                return
        except Exception as e:
            logger.error(f"Stop command error: {e}", exc_info=True)


@dp.message(for_admin.for_caption)                                           # own make ads   CAPTION
async def for_caption(message: types.Message, state: FSMContext):
    msg = message.text
    user_id = message.chat.id
    data = await state.get_data()
    if message.content_type == ContentType.TEXT:
        if msg.lower() == "/null":                                  # STOP
            await message.delete()
            await state.clear()
            await message.answer(text = f"{message.chat.first_name} -- <b>⚜️Admin aka⚜️</b> Assalom-u alaykum Bot xizmatingizda!", reply_markup = builder_admin.as_markup())

            return
        if 'video_id' in data:                                  # VIDEO
            try:
                await message.answer_video(video = data["video_id"], caption = msg, caption_entities = message.entities, parse_mode = None,reply_markup = confirm_make_ads.as_markup())
                await db.for_post(user_id, data["video_id"], msg, str(message.entities), await db.choosen_channel_view(user_id), "video")
                await state.clear()
            except Exception as e:
                logger.error(f"Video caption error: {e}", exc_info=True)
                await state.clear()
        elif "photo_id" in data:                                        # PHOTO
            try:
                await message.answer_photo(photo = data["photo_id"], caption = msg, caption_entities = message.entities, parse_mode = None,reply_markup = confirm_make_ads.as_markup())
                await db.for_post(user_id, data["photo_id"], msg, str(message.entities), await db.choosen_channel_view(user_id), "photo")
                await state.clear()
            except Exception as e:
                logger.error(f"Video caption error: {e}", exc_info=True)
                await state.clear()
        elif "document_id" in data:                                                         # DOCUMENT 
            try:
                await message.answer_document(document = data["document_id"], caption = msg, caption_entities = message.entities, parse_mode = None,reply_markup = confirm_make_ads.as_markup())
                await db.for_post(user_id, data["document_id"], msg, str(message.entities), await db.choosen_channel_view(user_id), "document")
                await state.clear()
            except Exception as e:
                logger.error(f"Video caption error: {e}", exc_info=True)
                await state.clear()
    else:
        await message.reply(text="‼️ Video tagidagi xabar(Caption) faqat matn ko'rinishida bo'ladi\n<b>📝 Matn ko'rinishida yuboring:</b>\nJarayonni to'xtatish: /null", reply_markup = cancel_post_btn.as_markup())


async def is_link(msg: str,number_btn):                     # tugmalarga kelgan havola link ekanligini tekshirish
    try:
        for i in range(number_btn):
            try:
                havola: str = msg.split(", ")[i - 1].split(" - ")[1]
                if not(havola.lower().startswith("https://") or havola.lower().startswith("http://") or havola.lower().startswith("@")):
                    return False
                return True
            except:
                return False
    except:
        return False


@dp.message(for_admin.for_btn)
async def for_plus_btn(message: types.Message, state: FSMContext):          # Tugma qoshish joyi
    msg = message.text
    user_id = message.chat.id
    post_msg = "✅ Post muvaffaqiyatli chop etildi."
    if msg == "/null":
        await message.delete()
        await state.clear()
        await message.answer(text = f"{message.chat.first_name} -- <b>⚜️Admin aka⚜️</b> Assalom-u alaykum Bot xizmatingizda!", reply_markup = builder_admin.as_markup())

        return
    number_btn = len(msg.split(","))
    if await is_link(msg,number_btn):
        lugat = str_to_dict(msg)
        if await db.is_type_post(user_id) == "video":                                  # VIDEO
            try:
                post_data = await db.for_post_view(user_id)
                if await db.for_post_is_multiple(user_id) == "multi":
                    if post_data[2] != "None":
                        entiy = post_data[2].replace("[MessageEntity(", "",).replace(")]", "").replace("'", "").replace(",", "").strip()
                    else:
                        entiy = None
                    channels = await db.channel_view() 
                    c = 0
                    for channel  in channels:
                        c += 1                                                  # hamma kanallarda
                        await bot.send_video(chat_id = channel, video = post_data[0], caption = post_data[1], caption_entities = control_entitiy(entiy), parse_mode = None, reply_markup = btn_create(lugat))
                    await message.answer(f"Post {c} ta ulangan kanallarda muvaffaqiyatli chop etildi ✅")
                    await state.clear()
                elif await db.for_post_is_multiple(user_id) == 'single':
                    if post_data[2] != "None":
                        entiy = post_data[2].replace("[MessageEntity(", "",).replace(")]", "").replace("'", "").replace(",", "").strip()
                    else:
                        entiy = None
                    await bot.send_video(chat_id = post_data[3], video = post_data[0], caption = post_data[1], caption_entities = control_entitiy(entiy), parse_mode = None,reply_markup = btn_create(lugat))
                    channel = await bot.get_chat(post_data[3])
                    invite_link = await channel.export_invite_link()
                    await message.answer(f"<a href='{invite_link}'>Post 1 ta kanalda muvaffaqiyatli chop etildi ✅</a>", disable_web_page_preview=True)
                    await state.clear()
                else:
                    # Broadcast to all users with parallel execution
                    if post_data[2] != "None":
                        entiy = post_data[2].replace("[MessageEntity(", "",).replace(")]", "").replace("'", "").replace(",", "").strip()
                    else:
                        entiy = None

                    users_list = await db.user_view()
                    blocked_users: List[Tuple[int, str]] = []

                    async def send_to_user(user_id: int) -> bool:
                        """Send video to single user, return True if success"""
                        try:
                            await bot.send_video(
                                chat_id=user_id,
                                video=post_data[0],
                                caption=post_data[1],
                                caption_entities=control_entitiy(entiy),
                                parse_mode=None,
                                reply_markup=btn_create(lugat)
                            )
                            return True
                        except Exception as e:
                            logger.warning(f"User {user_id} blocked: {e}")
                            try:
                                user_info = await bot.get_chat(user_id)
                                blocked_users.append((
                                    user_id,
                                    f"Ismi: {user_info.first_name},\nUsername: {user_info.username or 'Username topilmadi!'},\nID: {user_id},\nBio: {user_info.bio or 'Bio yozilmagan'}\n\n===    ====    ===    ===    ===\n\n"
                                ))
                            except Exception as bio_error:
                                logger.error(f"Could not get user info {user_id}: {bio_error}")
                            return False

                    # Send to all users in parallel (max 50 concurrent)
                    tasks = [send_to_user(user_id) for user_id in users_list]
                    results = await asyncio.gather(*tasks, return_exceptions=True)

                    successful = sum(1 for r in results if r is True)
                    m = successful
                    k = len(blocked_users)

                    if blocked_users:
                        bloked = "".join([info for _, info in blocked_users])
                        file = StringIO()
                        file.write(bloked)
                        current_time = datetime.now(tashkent_tz)
                        soat = current_time.strftime("%Y-%m-%d %H:%M:%S")
                        await message.answer_document(
                            document=BufferedInputFile(file=file.getvalue().encode("utf-8"), filename=BLOCKED_USERS_FILENAME),
                            caption=f"Blok qilganlar Ro'yhati {soat}\nBotning <b>{k} ta</b> foydalanuvchisi qora ro'yhatda!\nPost <b>{m} ta</b> foydalanuvchilar orasida muvaffaqiyatli chop etildi ✅"
                        )
                    else:
                        await message.reply(SUCCESS_MSG)

                    await state.clear()
            except Exception as e:
                logger.error(f"Post sending error: {e}", exc_info=True)
                await message.answer(text=f"Kanal uchun yasalgan postni chop etishda xatolik.\n\n<code>{e}</code>")
                await state.clear()
            await message.answer(text = f"{message.chat.first_name} -- <b>⚜️Admin aka⚜️</b> Assalom-u alaykum Bot xizmatingizda!", reply_markup = builder_admin.as_markup())

        elif await db.is_type_post(user_id) == "photo":     # PHOTO
            try:
                if await db.for_post_is_multiple(user_id) == 'multi':
                    post_data = await db.for_post_view(user_id)
                    if post_data[2] != "None":
                        entiy = post_data[2].replace("[MessageEntity(", "",).replace(")]", "").replace("'", "").replace(",", "").strip()
                    else:
                        entiy = None
                    channels = await db.channel_view() 
                    c = 0
                    for channel in channels:
                        c += 1
                        await bot.send_message(chat_id = channel, text = post_data[1], entities = control_entitiy(entiy), parse_mode = None,reply_markup = btn_create(lugat))
                    await message.answer(f"Post {c} ta ulangan kanallarda muvaffaqiyatli chop etildi ✅")
                    await state.clear()
                elif await db.for_post_is_multiple(user_id) == 'single':
                    post_data = await db.for_post_view(user_id)
                    if post_data[2] != "None":
                        entiy = post_data[2].replace("[MessageEntity(", "",).replace(")]", "").replace("'", "").replace(",", "").strip()
                    else:
                        entiy = None
                    await bot.send_message(chat_id = post_data[3], text = post_data[1], entities = control_entitiy(entiy), parse_mode = None,reply_markup = btn_create(lugat))
                    channel = await bot.get_chat(post_data[3])
                    invite_link = await channel.export_invite_link()
                    await message.answer(f"<a href='{invite_link}'>Post 1 ta kanalda muvaffaqiyatli chop etildi ✅</a>", disable_web_page_preview=True)
                    await state.clear()
                else:
                    post_data = await db.for_post_view(user_id)
                    if post_data[2] != "None":
                        entiy = post_data[2].replace("[MessageEntity(", "",).replace(")]", "").replace("'", "").replace(",", "").strip()
                    else:
                        entiy = None
                    k = 0
                    bloked = str()
                    m = 0
                    is_blocked = False
                    for users in await db.user_view():
                        try:
                            await bot.send_photo(chat_id = users, photo= post_data[0],  caption = post_data[1], caption_entities = control_entitiy(entiy), parse_mode = None, reply_markup = btn_create(lugat))
                            m += 1
                        except Exception as e:
                            print(e)
                            is_blocked = True
                            k += 1
                            ins = await bot.get_chat(users)
                            bloked += f"Ismi: {ins.first_name},\nUsername: {ins.username if ins.username else 'Username topilmadi!'},\nID: {users},\nBio: {ins.bio}\n\n===    ====    ===    ===    ===\n\n"
                            pass
                    if is_blocked:
                        file = StringIO()
                        file.write(bloked)
                        current_time = datetime.now(tashkent_tz)
                        soat = current_time.strftime("%Y-%m-%d %H:%M:%S")
                        await message.answer_document(document=BufferedInputFile(file = file.getvalue().encode("utf-8"), filename = f"Qora royhat.txt"), caption = f"Blok qilganlar Ro'yhati {soat}\nBotning <b>{k} ta</b> foydalanuvchisi qora ro'yhatda!\nPost <b>{m} ta</b> foydalanuvchilar orasida muvaffaqiyatli chop etildi ✅")
                    else:
                        await message.reply(post_msg)
                    await state.clear()
            except Exception as e:
                logger.error(f"Post sending error: {e}", exc_info=True)
                await message.answer(text=f"Kanal uchun yasalgan postni chop etishda xatolik.\n\n<code>{e}</code>")
                await state.clear()
            await message.answer(text = f"{message.chat.first_name} -- <b>⚜️Admin aka⚜️</b> Assalom-u alaykum Bot xizmatingizda!", reply_markup = builder_admin.as_markup())



        elif await db.is_type_post(user_id) == "document":                                                         # DOCUMENT
            try:
                post_data = await db.for_post_view(user_id)
                if await db.for_post_is_multiple(user_id) == 'multi':
                    if post_data[2] != "None":
                        entiy = post_data[2].replace("[MessageEntity(", "",).replace(")]", "").replace("'", "").replace(",", "").strip()
                    else:
                        entiy = None
                    channels = await db.channel_view() 
                    c = 0
                    for channel in channels:
                        c += 1                                                  # hamma kanallarda
                        await bot.send_document(chat_id = channel, document = post_data[0], caption = post_data[1], caption_entities = control_entitiy(entiy), parse_mode = None,reply_markup = btn_create(lugat))
                    await message.answer(f"Post {c} ta ulangan kanallarda muvaffaqiyatli chop etildi ✅")
                elif await db.for_post_is_multiple(user_id) == 'single':
                    if post_data[2] != "None":
                        entiy = post_data[2].replace("[MessageEntity(", "",).replace(")]", "").replace("'", "").replace(",", "").strip()
                    else:
                        entiy = None
                    await bot.send_document(chat_id = post_data[3], document = post_data[0], caption = post_data[1], caption_entities = control_entitiy(entiy), parse_mode = None,reply_markup = btn_create(lugat))
                    channel = await bot.get_chat(post_data[3])
                    invite_link = await channel.export_invite_link()
                    await message.answer(f"<a href='{invite_link}'>Post 1 ta kanalda muvaffaqiyatli chop etildi ✅</a>", disable_web_page_preview=True)
                    await state.clear()
                else:
                    if post_data[2] != "None":
                        entiy = post_data[2].replace("[MessageEntity(", "",).replace(")]", "").replace("'", "").replace(",", "").strip()
                    else:
                        entiy = None
                    k = 0
                    bloked = str()
                    m = 0
                    is_blocked = False

                    for users in await db.user_view():
                        try:
                            await bot.send_document(chat_id = users, document = post_data[0], caption = post_data[1], caption_entities = control_entitiy(entiy), parse_mode = None,reply_markup = btn_create(lugat))
                            m += 1
                        except Exception as e:
                            print(e)
                            is_blocked = True
                            k += 1
                            ins = await bot.get_chat(users)
                            bloked += f"Ismi: {ins.first_name},\nUsername: {ins.username if ins.username else 'Username topilmadi!'},\nID: {users},\nBio: {ins.bio}\n\n===    ====    ===    ===    ===\n\n"
                            pass
                    if is_blocked:
                        file = StringIO()
                        file.write(bloked)
                        current_time = datetime.now(tashkent_tz)
                        soat = current_time.strftime("%Y-%m-%d %H:%M:%S")
                        await message.answer_document(document=BufferedInputFile(file = file.getvalue().encode("utf-8"), filename = f"Qora royhat.txt"), caption = f"Blok qilganlar Ro'yhati {soat}\nBotning <b>{k} ta</b> foydalanuvchisi qora ro'yhatda!\nPost <b>{m} ta</b> foydalanuvchilar orasida muvaffaqiyatli chop etildi ✅")
                    else:
                        await message.reply(post_msg)
                    await state.clear()
            except Exception as e:
                logger.error(f"Post sending error: {e}", exc_info=True)
                await message.answer(text=f"Kanal uchun yasalgan postni chop etishda xatolik.\n\n<code>{e}</code>")
                await state.clear()
            await message.answer(text = f"{message.chat.first_name} -- <b>⚜️Admin aka⚜️</b> Assalom-u alaykum Bot xizmatingizda!", reply_markup = builder_admin.as_markup())


        else:
            try:
                if await db.for_post_is_multiple(user_id) == 'multi':
                    post_data = await db.for_post_view(user_id)
                    if post_data[2] != "None":
                        entiy = post_data[2].replace("[MessageEntity(", "",).replace(")]", "").replace("'", "").replace(",", "").strip()
                    else:
                        entiy = None
                    channels = await db.channel_view() 
                    c = 0
                    for channel in channels:
                        c += 1
                        await bot.send_photo(chat_id = channel, photo = post_data[0], caption = post_data[1], caption_entities = control_entitiy(entiy), parse_mode = None,reply_markup = btn_create(lugat))
                    await message.answer(f"Post {c} ta ulangan kanallarda muvaffaqiyatli chop etildi ✅")
                    await state.clear()
                elif await db.for_post_is_multiple(user_id) == 'single':
                    post_data = await db.for_post_view(user_id)
                    if post_data[2] != "None":
                        entiy = post_data[2].replace("[MessageEntity(", "",).replace(")]", "").replace("'", "").replace(",", "").strip()
                    else:
                        entiy = None
                    await bot.send_photo(chat_id = post_data[3], photo = post_data[0], caption = post_data[1], caption_entities = control_entitiy(entiy), parse_mode = None,reply_markup = btn_create(lugat))
                    channel = await bot.get_chat(post_data[3])
                    invite_link = await channel.export_invite_link()
                    await message.answer(f"<a href='{invite_link}'>Post 1 ta kanalda muvaffaqiyatli chop etildi ✅</a>", disable_web_page_preview=True)
                    await state.clear()
                else:
                    post_data = await db.for_post_view(user_id)
                    if post_data[2] != "None":
                        entiy = post_data[2].replace("[MessageEntity(", "",).replace(")]", "").replace("'", "").replace(",", "").strip()
                    else:
                        entiy = None
                    k = 0
                    bloked = str()
                    m = 0
                    is_blocked = False
                    
                    for users in await db.user_view():
                        try:
                            await bot.send_message(chat_id = users, text = post_data[1], entities = control_entitiy(entiy), parse_mode = None,reply_markup = btn_create(lugat))
                            m += 1
                        except Exception as e:
                            is_blocked = True
                            print(e)
                            k += 1
                            ins = await bot.get_chat(users)
                            bloked += f"Ismi: {ins.first_name},\nUsername: {ins.username if ins.username else 'Username topilmadi!'},\nID: {users},\nBio: {ins.bio}\n\n===    ====    ===    ===    ===\n\n"
                            pass
                            
                    if is_blocked:
                        file = StringIO()
                        file.write(bloked)
                        current_time = datetime.now(tashkent_tz)
                        soat = current_time.strftime("%Y-%m-%d %H:%M:%S")
                        await message.answer_document(document=BufferedInputFile(file = file.getvalue().encode("utf-8"), filename = f"Qora royhat.txt"), caption = f"Blok qilganlar Ro'yhati {soat}\nBotning <b>{k} ta</b> foydalanuvchisi qora ro'yhatda!\nPost <b>{m} ta</b> foydalanuvchilar orasida muvaffaqiyatli chop etildi ✅")
                    else:
                        await message.reply(post_msg)
                    await state.clear()
            except Exception as e:
                logger.error(f"Post sending error: {e}", exc_info=True)
                await message.answer(text=f"Kanal uchun yasalgan postni chop etishda xatolik.\n\n<code>{e}</code>")
                await state.clear()
            await message.answer(text = f"{message.chat.first_name} -- <b>⚜️Admin aka⚜️</b> Assalom-u alaykum Bot xizmatingizda!", reply_markup = builder_admin.as_markup())

    else:
        await message.reply(text = "<i>❗️ Siz videoda ko'rsatilgan formatda tugmalar kiritmadingiz.</i> Qayta urinib ko'ring!\n<b>⭐ Namuna:</b>\n<code>Admin - https://t.me/java_strong, Admin2 - @X_java_strong</code>", disable_web_page_preview = True)
