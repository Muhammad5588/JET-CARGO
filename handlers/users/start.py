import re
from aiogram.filters                import CommandStart
from aiogram.types                  import Message, CallbackQuery
from handlers.users.additional.admin import show_admin_panel
from loader                         import dp, bot
from data.Async_sqlDataBase         import data_db as db
from keyboards.inline.admin_page    import builder_admin
from aiogram.fsm.context          import FSMContext

from utils.formatters import format_verification_status
from utils.keyboards import main_menu_keyboard, welcome_keyboard
from utils.texts import get_text
    
@dp.message(CommandStart()) 
async def command_start_handler(message: Message, command: CommandStart, state: FSMContext) -> None:
    if message.chat.type == 'private':
        args = command.args or ''
        me = await bot.get_me()
        
        # Agar deep link bor bo'lsa
        if args and not(message.chat.id in await db.admin_view()):
            match = re.match(r"UMTS-[A-Za-z0-9]{12}$", args)
            if match:
                code = match.group(0)
                baseCode = await db.check_code(code)
                if baseCode:
                    await db.delete_code(code)
                    await db.admin_plus(message.chat.id)
                else:
                    await message.reply("Mavjud bo'lmagan kod.")
        
        # Umumiy start jarayoni
        if message.chat.id == (await db.admin_view())[0]:
            await message.answer(
                text=f"{message.from_user.mention_html()} -- <b>⚜️Admin aka⚜️</b> Assalom-u alaykum Bot xizmatingizda!\n🆔: <code>{message.chat.id}</code>", 
                reply_markup=builder_admin.as_markup()
            )
            
            await show_admin_panel(message, state)
            return
        
        if message.chat.id in await db.admin_view():
            await show_admin_panel(message, state)
            return
        
        if not await db.is_user(message.chat.id):
            await db.user_plus(message.chat.id)

        user_id = message.from_user.id
        is_registered = await db.is_user_registered(user_id)

        if is_registered:
            user = await db.get_user_by_telegram_id(user_id)
            lang = user['language']

            await state.update_data(language=lang, user_id=user['id'])

            # Status xabari
            status_text = format_verification_status(user['verification_status'], lang)

            if user['verification_status'] == 'approved':
                status_msg = get_text(lang, 'status_approved')
                # Faqat tasdiqlangan foydalanuvchilar uchun asosiy menyu
                await message.answer(
                    get_text(lang, 'welcome_registered',
                            fullname=user['fullname'],
                            client_code=user['client_code'],
                            phone=user['phone'],
                            status=status_text,
                            status_message=status_msg),
                    reply_markup=main_menu_keyboard(lang, await db.is_admin(user_id))
                )
            elif user['verification_status'] == 'rejected':
                status_msg = get_text(lang, 'status_rejected', reason=user['rejection_reason'] or "—")
                # Rad etilgan foydalanuvchilar uchun qayta ro'yxatdan o'tish
                await message.answer(
                    get_text(lang, 'welcome_registered',
                            fullname=user['fullname'],
                            client_code=user['client_code'],
                            phone=user['phone'],
                            status=status_text,
                            status_message=status_msg),
                    reply_markup=ReplyKeyboardRemove()
                )
                await message.answer("Iltimos, qayta ro'yxatdan o'ting.", reply_markup=welcome_keyboard(lang))
            else:
                status_msg = get_text(lang, 'status_pending')
                # Kutilayotgan foydalanuvchilar uchun faqat status
                from aiogram.types import ReplyKeyboardRemove
                await message.answer(
                    get_text(lang, 'welcome_registered',
                            fullname=user['fullname'],
                            client_code=user['client_code'],
                            phone=user['phone'],
                            status=status_text,
                            status_message=status_msg),
                    reply_markup=ReplyKeyboardRemove()
                )
        else:
            # Yangi foydalanuvchi
            data = await state.get_data()
            lang = data.get('language', 'uz')
            bot_title = await bot.get_me()
            await message.answer(
                get_text(lang,  'welcome_new', bot_name=bot_title.first_name),
                reply_markup=welcome_keyboard(lang)
            )

@dp.callback_query(lambda c: c.data == 'check')
async def callback_query_handler(call: CallbackQuery) -> None:
    await call.answer()
    me = await bot.get_me()
    chat_id = call.message.chat.id
    
    if not await db.is_user(chat_id):
        await db.user_plus(chat_id)
    
