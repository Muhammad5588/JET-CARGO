"""
Auth Handlers - Ro'yxatdan o'tish va Login (Optimized)
"""
import os
import logging
from aiogram import F
from loader import dp, bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, FSInputFile, InputMediaPhoto

from data.config import (
    CLIENT_CODE_PREFIX,
    PASSPORT_TEMPLATE,
    PINFL_TEMPLATE,
    PassportType,
    VERIFICATION_GROUP_ID
)
from data.Async_sqlDataBase import data_db as db
from utils.validators import Validators
from utils.texts import get_text
from utils.keyboards import (
    welcome_keyboard,
    main_menu_keyboard,
    cancel_keyboard,
    passport_type_keyboard,
    confirm_keyboard,
    verification_inline_keyboard
)
from utils.formatters import format_phone_display

from states.AdminStates import RegistrationStates, LoginStates


logger = logging.getLogger(__name__)


# Helper: Guruhlarda keyboard yuborilmasligi uchun
def get_is_private(message: Message) -> bool:
    """Check if message is from private chat"""
    return message.chat.type == 'private'


# ==================== RO'YXATDAN O'TISH ====================

@dp.message(F.text.in_([
    get_text('uz', 'register'),
    get_text('ru', 'register')
]))
async def start_registration(message: Message, state: FSMContext):
    """Ro'yxatdan o'tishni boshlash"""
    data = await state.get_data()
    lang = data.get('language', 'uz')
    
    await state.set_state(RegistrationStates.entering_fullname)
    await message.answer(
        get_text(lang, 'enter_fullname'),
        reply_markup=cancel_keyboard(lang, get_is_private(message))
    )


@dp.message(RegistrationStates.entering_fullname, F.text)
async def process_fullname(message: Message, state: FSMContext):
    """F.I.O ni qabul qilish"""
    data = await state.get_data()
    lang = data.get('language', 'uz')
    
    if message.text == get_text(lang, 'cancel'):
        await state.clear()
        await message.answer(
            get_text(lang, 'operation_cancelled'),
            reply_markup=welcome_keyboard(lang, get_is_private(message))
        )
        return
    
    valid, msg, formatted = Validators.validate_fullname(message.text)
    
    if not valid:
        await message.answer(f"❌ {msg}\n\n{get_text(lang, 'enter_fullname')}")
        return
    
    await state.update_data(fullname=formatted)
    await state.set_state(RegistrationStates.entering_phone)
    
    await message.answer(
        get_text(lang, 'enter_phone'),
        reply_markup=cancel_keyboard(lang, get_is_private(message))
    )


@dp.message(RegistrationStates.entering_phone, F.text)
async def process_phone(message: Message, state: FSMContext):
    """Telefon raqamini qabul qilish"""
    data = await state.get_data()
    lang = data.get('language', 'uz')
    
    if message.text == get_text(lang, 'cancel'):
        await state.clear()
        await message.answer(
            get_text(lang, 'operation_cancelled'),
            reply_markup=welcome_keyboard(lang, get_is_private(message))
        )
        return
    
    valid, msg, phone = Validators.validate_phone(message.text)
    
    if not valid:
        await message.answer(f"❌ {msg}\n\n{get_text(lang, 'enter_phone')}")
        return
    
    await state.update_data(phone=phone)
    await state.set_state(RegistrationStates.selecting_passport_type)
    
    await message.answer(
        get_text(lang, 'select_passport_type'),
        reply_markup=passport_type_keyboard(lang, get_is_private(message))
    )


@dp.message(RegistrationStates.selecting_passport_type, F.text)
async def process_passport_type(message: Message, state: FSMContext):
    """Pasport turi tanlash"""
    data = await state.get_data()
    lang = data.get('language', 'uz')
    
    if message.text == get_text(lang, 'cancel'):
        await state.clear()
        await message.answer(
            get_text(lang, 'operation_cancelled'),
            reply_markup=welcome_keyboard(lang, get_is_private(message))
        )
        return
    
    if message.text == get_text(lang, 'passport_id_card'):
        await state.update_data(passport_type=PassportType.ID_CARD)
        await state.set_state(RegistrationStates.uploading_passport_front)
        
        await message.answer(
            get_text(lang, 'upload_passport_front'),
            reply_markup=cancel_keyboard(lang, get_is_private(message))
        )
    elif message.text == get_text(lang, 'passport_booklet'):
        await state.update_data(passport_type=PassportType.BOOKLET)
        await state.set_state(RegistrationStates.uploading_passport_booklet)
        
        await message.answer(
            get_text(lang, 'upload_passport_booklet'),
            reply_markup=cancel_keyboard(lang, get_is_private(message))
        )
    else:
        await message.answer(
            get_text(lang, 'invalid_command'),
            reply_markup=passport_type_keyboard(lang, get_is_private(message))
        )


@dp.message(RegistrationStates.uploading_passport_front, F.photo)
async def process_passport_front(message: Message, state: FSMContext):
    """Pasport old tomonini qabul qilish (ID card)"""
    data = await state.get_data()
    lang = data.get('language', 'uz')

    try:
        # Eng katta rasmni olish
        photo = message.photo[-1]

        # File ID ni saqlash (rasmni yuklamasdan)
        await state.update_data(
            passport_front_file_id=photo.file_id,
            passport_front_file_unique_id=photo.file_unique_id
        )
        await state.set_state(RegistrationStates.uploading_passport_back)

        await message.answer(
            get_text(lang, 'upload_passport_back'),
            reply_markup=cancel_keyboard(lang, get_is_private(message))
        )
    except Exception as e:
        logger.error(f"Pasport old tomoni yuklashda xatolik: {e}", exc_info=True)
        await message.answer(get_text(lang, 'error_photo'))


@dp.message(RegistrationStates.uploading_passport_back, F.photo)
async def process_passport_back(message: Message, state: FSMContext):
    """Pasport orqa tomonini qabul qilish (ID card)"""
    data = await state.get_data()
    lang = data.get('language', 'uz')

    try:
        photo = message.photo[-1]

        # File ID ni saqlash (rasmni yuklamasdan)
        await state.update_data(
            passport_back_file_id=photo.file_id,
            passport_back_file_unique_id=photo.file_unique_id
        )
        await state.set_state(RegistrationStates.entering_passport_number)

        # Template ni yuborish
        await send_passport_template(message, lang)

        await message.answer(
            get_text(lang, 'enter_passport_number'),
            reply_markup=cancel_keyboard(lang, get_is_private(message))
        )
    except Exception as e:
        logger.error(f"Pasport orqa tomoni yuklashda xatolik: {e}", exc_info=True)
        await message.answer(get_text(lang, 'error_photo'))


@dp.message(RegistrationStates.uploading_passport_booklet, F.photo)
async def process_passport_booklet(message: Message, state: FSMContext):
    """Pasport rasmini qabul qilish (Kitobli)"""
    data = await state.get_data()
    lang = data.get('language', 'uz')

    try:
        photo = message.photo[-1]

        # File ID ni saqlash (kitobli uchun front va back bir xil)
        await state.update_data(
            passport_front_file_id=photo.file_id,
            passport_back_file_id=photo.file_id,
            passport_front_file_unique_id=photo.file_unique_id,
            passport_back_file_unique_id=photo.file_unique_id
        )
        await state.set_state(RegistrationStates.entering_passport_number)

        # Template ni yuborish
        await send_passport_template(message, lang)

        await message.answer(
            get_text(lang, 'enter_passport_number'),
            reply_markup=cancel_keyboard(lang, get_is_private(message))
        )
    except Exception as e:
        logger.error(f"Pasport (kitobli) yuklashda xatolik: {e}", exc_info=True)
        await message.answer(get_text(lang, 'error_photo'))


async def send_passport_template(message: Message, lang: str):
    """Pasport template rasmni yuborish"""
    if os.path.exists(PASSPORT_TEMPLATE):
        try:
            await message.answer_photo(
                FSInputFile(PASSPORT_TEMPLATE),
                caption="📸 Pasport seriya va raqami SHU YERDA"
            )
        except Exception as e:
            logger.warning(f"Template yuborishda xatolik: {e}")


@dp.message(RegistrationStates.entering_passport_number, F.text)
async def process_passport_number(message: Message, state: FSMContext):
    """Pasport raqamini qabul qilish"""
    data = await state.get_data()
    lang = data.get('language', 'uz')
    
    if message.text == get_text(lang, 'cancel'):
        await state.clear()
        await message.answer(
            get_text(lang, 'operation_cancelled'),
            reply_markup=welcome_keyboard(lang, get_is_private(message))
        )
        return
    
    valid, msg, passport = Validators.validate_passport_number(message.text)
    
    if not valid:
        await message.answer(f"❌ {msg}")
        return
    
    await state.update_data(passport_number=passport)
    await state.set_state(RegistrationStates.entering_birth_date)
    
    await message.answer(
        get_text(lang, 'enter_birth_date'),
        reply_markup=cancel_keyboard(lang, get_is_private(message))
    )


@dp.message(RegistrationStates.entering_birth_date, F.text)
async def process_birth_date(message: Message, state: FSMContext):
    """Tug'ilgan sanani qabul qilish"""
    data = await state.get_data()
    lang = data.get('language', 'uz')
    
    if message.text == get_text(lang, 'cancel'):
        await state.clear()
        await message.answer(
            get_text(lang, 'operation_cancelled'),
            reply_markup=welcome_keyboard(lang, get_is_private(message))
        )
        return
    
    valid, msg, birth_date, warning, _ = Validators.validate_birth_date(message.text)
    
    if not valid:
        await message.answer(f"❌ {msg}")
        return
    
    await state.update_data(
        birth_date=birth_date
    )
    
    # Pasport muddati ogohlantiruvi
    if warning:
        await message.answer(warning)
    
    await state.set_state(RegistrationStates.entering_pinfl)
    
    # PINFL template
    if os.path.exists(PINFL_TEMPLATE):
        try:
            await message.answer_photo(
                FSInputFile(PINFL_TEMPLATE),
                caption="📸 PINFL SHU YERDA"
            )
        except Exception as e:
            logger.warning(f"PINFL template yuborishda xatolik: {e}")
    
    await message.answer(
        get_text(lang, 'enter_pinfl'),
        reply_markup=cancel_keyboard(lang, get_is_private(message))
    )


@dp.message(RegistrationStates.entering_pinfl, F.text)
async def process_pinfl(message: Message, state: FSMContext):
    """PINFL ni qabul qilish"""
    data = await state.get_data()
    lang = data.get('language', 'uz')
    
    if message.text == get_text(lang, 'cancel'):
        await state.clear()
        await message.answer(
            get_text(lang, 'operation_cancelled'),
            reply_markup=welcome_keyboard(lang, get_is_private(message))
        )
        return
    
    valid, msg, pinfl = Validators.validate_pinfl(message.text)
    
    if not valid:
        await message.answer(f"❌ {msg}")
        return
    
    await state.update_data(pinfl=pinfl)
    await state.set_state(RegistrationStates.entering_address)
    
    await message.answer(
        get_text(lang, 'enter_address'),
        reply_markup=cancel_keyboard(lang, get_is_private(message))
    )


@dp.message(RegistrationStates.entering_address, F.text)
async def process_address(message: Message, state: FSMContext):
    """Manzilni qabul qilish"""
    data = await state.get_data()
    lang = data.get('language', 'uz')
    
    if message.text == get_text(lang, 'cancel'):
        await state.clear()
        await message.answer(
            get_text(lang, 'operation_cancelled'),
            reply_markup=welcome_keyboard(lang, get_is_private(message))
        )
        return
    
    valid, msg, address = Validators.validate_address(message.text)
    
    if not valid:
        await message.answer(f"❌ {msg}")
        return
    
    await state.update_data(address=address)
    await state.set_state(RegistrationStates.confirming_registration)
    
    # Ma'lumotlarni ko'rsatish
    data = await state.get_data()
    
    await message.answer(
        get_text(lang, 'confirm_registration',
                fullname=data['fullname'],
                phone=format_phone_display(data['phone']),
                passport=data['passport_number'],
                birth_date=data['birth_date'],
                pinfl=data['pinfl'],
                address=data['address']),
        reply_markup=confirm_keyboard(lang, get_is_private(message))
    )


@dp.message(RegistrationStates.confirming_registration, F.text)
async def confirm_registration(message: Message, state: FSMContext):
    """Ro'yxatdan o'tishni tasdiqlash"""
    import asyncio
    
    data = await state.get_data()
    lang = data.get('language', 'uz')
    
    if message.text == get_text(lang, 'confirm'):
        # Foydalanuvchini saqlash
        success, msg, client_code = await db.register_user(message.from_user.id, data)

        if success:
            # User ni olish
            user = await db.get_user_by_telegram_id(message.from_user.id)

            # Verification guruhga yuborishni background taskda ishlatish
            asyncio.create_task(send_to_verification_group(user, data))

            await state.clear()
            await message.answer(
                get_text(lang, 'registration_submitted'),
                reply_markup=main_menu_keyboard(lang, is_private=get_is_private(message))
            )
        else:
            await message.answer(f"❌ Xatolik: {msg}")
    
    elif message.text == get_text(lang, 'cancel'):
        await state.clear()
        await message.answer(
            get_text(lang, 'operation_cancelled'),
            reply_markup=welcome_keyboard(lang, get_is_private(message))
        )


async def send_to_verification_group(user: dict, data: dict):
    """Ma'lumotlarni verification guruhga yuborish (rasmlar album ko'rinishida)"""
    try:
        # Matn tayyorlash (optimized formatting)
        text = (
            "🆕 YANGI RO'YXATDAN O'TUVCHI\n\n"
            f"👤 F.I.O: {user['fullname']}\n"
            f"📱 Telefon: {format_phone_display(user['phone'])}\n"
            f"🆔 Pasport: {user['passport_number']}\n"
            f"📅 Tug'ilgan: {user['birth_date']}\n"
            f"🔢 PINFL: {user['pinfl']}\n"
            f"📍 Manzil: {user['address']}\n\n"
            f"🔐 Mijoz kodi: {user['client_code']}\n"
            f"📅 Ro'yxat: {user['registered_at']}"
        )
        
        # Pasport rasmlarini album sifatida yuborish
        media_group = []
        passport_front = data.get('passport_front_file_id')
        passport_back = data.get('passport_back_file_id')
        
        if passport_front:
            # Birinchi rasmga caption qo'shish
            caption = "📸 Pasport" if passport_back == passport_front else "📸 Pasport (OLD)"
            media_group.append(
                InputMediaPhoto(
                    media=passport_front,
                    caption=caption
                )
            )
        
        # Orqa tomoni bor va old tomondan farqli bo'lsa (ID card uchun)
        if passport_back and passport_back != passport_front:
            media_group.append(
                InputMediaPhoto(
                    media=passport_back,
                    caption="📸 Pasport (ORQA)"
                )
            )
        
        # Album yuborish (agar rasmlar mavjud bo'lsa)
        if media_group:
            await bot.send_media_group(
                chat_id=VERIFICATION_GROUP_ID,
                media=media_group
            )
        
        # Ma'lumot va tugmalar bilan xabar yuborish
        msg = await bot.send_message(
            chat_id=VERIFICATION_GROUP_ID,
            text=text,
            reply_markup=verification_inline_keyboard(user['id'], 'uz')
        )
        
        # Verification queue ga qo'shish
        await db.add_to_verification_queue(user['id'], msg.message_id)
        
        logger.info(f"User {user['id']} ({user['fullname']}) verification guruhga yuborildi")
        
    except Exception as e:
        logger.error(f"Verification guruhga yuborishda xatolik (user: {user.get('id', 'unknown')}): {e}", exc_info=True)


# ==================== LOGIN ====================

@dp.message(F.text.in_([
    get_text('uz', 'login'),
    get_text('ru', 'login')
]))
async def start_login(message: Message, state: FSMContext):
    """Loginni boshlash"""
    data = await state.get_data()
    lang = data.get('language', 'uz')
    
    await state.set_state(LoginStates.entering_client_code)
    await message.answer(
        get_text(lang, 'enter_client_code', CLIENT_CODE_PREFIX=CLIENT_CODE_PREFIX),
        reply_markup=cancel_keyboard(lang, get_is_private(message))
    )


@dp.message(LoginStates.entering_client_code, F.text)
async def process_client_code(message: Message, state: FSMContext):
    """Mijoz kodini qabul qilish"""
    data = await state.get_data()
    lang = data.get('language', 'uz')
    
    if message.text == get_text(lang, 'cancel'):
        await state.clear()
        await message.answer(
            get_text(lang, 'operation_cancelled'),
            reply_markup=welcome_keyboard(lang, get_is_private(message))
        )
        return
    
    await state.update_data(temp_client_code=message.text.strip().upper())
    await state.set_state(LoginStates.entering_phone_verify)
    
    await message.answer(
        get_text(lang, 'enter_phone_verify'),
        reply_markup=cancel_keyboard(lang, get_is_private(message))
    )


@dp.message(LoginStates.entering_phone_verify, F.text)
async def process_phone_verify(message: Message, state: FSMContext):
    """Telefon raqamini tekshirish va login"""
    data = await state.get_data()
    lang = data.get('language', 'uz')
    
    if message.text == get_text(lang, 'cancel'):
        await state.clear()
        await message.answer(
            get_text(lang, 'operation_cancelled'),
            reply_markup=welcome_keyboard(lang, get_is_private(message))
        )
        return
    
    client_code = data['temp_client_code']
    user = await db.verify_login(client_code, message.text)
    
    if user:
        await state.clear()
        await state.update_data(language=user['language'], user_id=user['id'])
        
        await message.answer(
            get_text(user['language'], 'login_success', fullname=user['fullname']),
            reply_markup=main_menu_keyboard(user['language'], await db.is_admin(message.from_user.id))
        )
        try:
            await db.update_user_id(message.from_user.id, client_code)
        except Exception as e:
            logger.error(f"Error updating user ID or activating user: {e}")
        await db.activate_user(message.from_user.id)
    else:
        await message.answer(get_text(lang, 'login_failed'))
        await state.clear()
        bot_title = await bot.get_me()
        await message.answer(
            get_text(lang, 'welcome_new'),
            reply_markup=welcome_keyboard(lang, get_is_private(message), bot_name=bot_title.first_name)
        )