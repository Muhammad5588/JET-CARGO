from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CopyTextButton
from aiogram.filters.callback_data import CallbackData
from enum import Enum

class aktin(Enum):
    orqaga = "↩️"
    null_not = "❌"
    oldinga = "↪️"


class numbee(CallbackData, prefix = "vkm"):
    id: str

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

def num_btn(num_list, taype=None) -> InlineKeyboardMarkup:
    if not num_list:
        # If num_list is empty, return an empty InlineKeyboardMarkup
        return InlineKeyboardMarkup()

    buyruq_turi = {
        None: "_kanal",
        "minus": "_minus",
        "force": "_force@",
        "force_m": "_forcement@"
    }.get(taype, "_plus")

    btn = InlineKeyboardBuilder()
    first = None

    for i in num_list:
        i_str = str(i)
        if not first:
            first = f"{i_str}{buyruq_turi}"
        is_kanal = f"{i_str}{buyruq_turi}"
        btn.button(
            text=i_str, callback_data=numbee(id=is_kanal)
        )

    btn.adjust(4)

    # Ensure num_list is not empty before using its elements
    if num_list:
        max_channel = f"{num_list[-1]}{buyruq_turi}max_channel"
        min_channel = f"{first}min_channel"

        btn.row(
            InlineKeyboardButton(text=aktin.orqaga, callback_data=min_channel),
            InlineKeyboardButton(text=aktin.null_not, callback_data="0"),
            InlineKeyboardButton(text=aktin.oldinga, callback_data=max_channel)
        )
    
    return btn.as_markup()
def num_btn_admin(num_list, taype=None) -> InlineKeyboardMarkup:
    if not num_list:
        # If num_list is empty, return an empty InlineKeyboardMarkup
        return InlineKeyboardMarkup()

    buyruq_turi = {
        None: ["info", "__max_admin", "_min_admin"],
        "hamkor": ["_hamkor", "%max-admin", "-min-admin"],
        "hamkor_m": ["_removeHamkor", "&&max-admin", "!!min-admin"]
    }.get(taype)

    
    btn = InlineKeyboardBuilder()
    first = None
    # print(num_list)
    for i in num_list:
        i = str(i)
        if not first:
            first = i + f"{buyruq_turi[0]}"
        is_kanal = i + f"{buyruq_turi[0]}"
        btn.button(
            text=i, callback_data=numbee(id=is_kanal)
        )
    
    btn.adjust(4)
    max = i + f"{buyruq_turi[1]}"
    firstly = first + f"{buyruq_turi[2]}"
    # if len(num_list) >= 8:
    btn.row(InlineKeyboardButton(text=aktin.orqaga, callback_data=firstly),
    InlineKeyboardButton(text=aktin.null_not, callback_data="0"),
    InlineKeyboardButton(text=aktin.oldinga, callback_data=max))
    return btn.as_markup()

builder_admin = InlineKeyboardBuilder()
builder_admin.button(text="➕ Admin qo'shish", callback_data="admin_plus") 
builder_admin.button(text="➖ Adminlikdan bo'shatish", callback_data="adminlar") # Adminni olib tashlash faqat ozi qoshgan adminlarni olib tashlay oladigan qilinadi va bu ownerga tegishli emas va limit qoyiladi eng kopi bn 3 tagacha admin qoshish mkn
builder_admin.button(text="➕ Kanal qo'shish", callback_data="kanal_plus")  # kanal qoshishda adminning usernamesi yoki id si va shuningdek kanalning id si yoki kanal usernamesi orqali qoshiladi va limit qoyiladi eng kopi bn 3 tagacha kanal ulashga ruxsat
builder_admin.button(text="➖ Kanalni chiqarish", callback_data="kanal_minus") # Hamma adminlar o'zi qoshgan kanalni chiqarib tashlay oladi va qolganlani ulagan kanali boshqa boshqa adminlarga korinmaydi va bu ownerga taluqli emas
builder_admin.button(text="🔩 Majburiy obuna", callback_data="force_obuna")
builder_admin.button(text="📝 Adminlarga Xabar", callback_data="adminlarga_xabar") # bu hamma adminlarga xabar yuboradi bitta state bo'ladi va yuboradi
builder_admin.button(text="🤝 Hamkorlik", callback_data="hamkorlik") # admin ozining kanaliga bot orqali admin qiladi yani partner qiladi va uni o'chirib tashlashi ham mkn 2- tugma orqali
# builder_admin.button(text="💾 Ma'lumotlar bazasi", callback_data="malumotlar")
# builder_admin.button(text="📁 Bot Logs", callback_data="logs")
builder_admin.button(text="📝 Reklama Jo'natish", callback_data="reklama")
builder_admin.button(text="📊 Statistika", callback_data="statistika")
builder_admin.button(text="📅 Bazani olish", callback_data="base")
builder_admin.adjust(2)



majburiy_subs_on_off = InlineKeyboardBuilder()
majburiy_subs_on_off.button(text = "🔩 Kanal qo'shish", callback_data = "force_subs")
majburiy_subs_on_off.button(text = "💪 Kanal chiqarish", callback_data = "force_subs_minus")
majburiy_subs_on_off.button(text = "💥 Majburiy obunalarni o'chirish/yoqish", callback_data = "subs_off_on")
majburiy_subs_on_off.adjust(2)
majburiy_subs_on_off.row(InlineKeyboardButton(text = "Orqaga ↪", callback_data = "orqaga")),

confirm_forward = InlineKeyboardBuilder()
confirm_forward.button(text = "Chop etish 📤", callback_data = "confirm_forward")
confirm_forward.button(text = "Rad Etish ❌", callback_data = "confirm_refuse")


confirm_make_ads = InlineKeyboardBuilder()
confirm_make_ads.button(text = "⏹ Tugma qo'shish", callback_data = "add_btn")
confirm_make_ads.button(text = "Chop etish 📤", callback_data = "confirm_make_ads")
confirm_make_ads.button(text = "Rad Etish ❌", callback_data = "confirm_refuse")
confirm_make_ads.adjust(2)

cancel_post_btn = InlineKeyboardBuilder()
cancel_post_btn.button(text = "Rad Etish ❌", callback_data = "confirm_refuse")



cancel_and_del = InlineKeyboardBuilder()
cancel_and_del.button(text = "👋 Adminlikdan bo'shatish", callback_data = "delete_admin")
cancel_and_del.button(text = "Rad Etish ❌", callback_data = "confirm_refuse")

hamkorlik = InlineKeyboardBuilder()
hamkorlik.button(text = "Hamkor qilish", callback_data = "add_hamkor")
hamkorlik.button(text = "Hamkorlikdan olib tashlash", callback_data = "remove_hamkor")
hamkorlik.button(text = "Rad Etish ❌", callback_data = "confirm_refuse")

hamkorlik.adjust(2)

def reklama_btn_one():
    reklama = InlineKeyboardBuilder()
    reklama.button(text = "📢 Kanalga", callback_data = "one_channel")
    reklama.button(text = "🤖 Bot ichida", callback_data = "in_bot")
    reklama.adjust(2)
    return reklama.as_markup()

def reklama_btn_two():
    reklama = InlineKeyboardBuilder()
    reklama.button(text = "📢 Kanalga", callback_data = "one_channel")
    reklama.button(text = "🤖 Bot ichida", callback_data = "in_bot")
    reklama.button(text = "📢 Kanallarga", callback_data = "all_channel")
    reklama.adjust(2)
    return reklama.as_markup()

def str_to_dict(message: str):                            # Tugmalarni lug'ar shakliga otkiradi
    lugat = {}
    # Elementlarni vergul va bo'sh joy bo'yicha bo'ling
    elementlar = message.split(', ')

    for element in elementlar:
        try:
            kalit, qiymat = element.split(' - ')
        except ValueError:
            continue
        lugat[kalit.strip()] = qiymat.strip()
    
    return lugat

def control_entitiy(matn):                       # Entitiesni qolda convert qilish
    if not(matn is None):
        lugat = {}
        # Bo'shliqlar va vergullar bo'yicha bo'lingan elementlarni oling
        elementlar = matn.replace(',', '').split()
        for element in elementlar:
            try:
                kalit, qiymat = element.split('=')
            except:
                kalit, qiymat = element.split('=', 1)
            # Qiymatni aniqlang
            if qiymat.isdigit():
                qiymat = int(qiymat)
            elif qiymat.lower() == 'none':
                qiymat = None
            lugat[kalit] = qiymat
        return [lugat]  # Natijani ro'yxat ichida qaytarish
    else:
        return None

def confirm_admin_msg():                    # adminlarga yuboruvchi Confirm
    admin = InlineKeyboardBuilder()
    admin.button(text = "🐣 Adminlarga yuborish", callback_data = "send")
    admin.button(text = "Rad Etish ❌", callback_data = "confirm_refuse")
    admin.adjust(2)
    return admin.as_markup()


def btn_create(lugat: dict):                          # tugma yaratish
    uzunligi = len(lugat)
    create = InlineKeyboardBuilder()
    if uzunligi <= 3:
        for k,v in lugat.items():
            if v.startswith("@"):
                v = v.replace("@", "https://t.me/")
            create.button(
                text = k, url = v
            )
        create.adjust(2)
        return create.as_markup()
    
    elif uzunligi < 5:
        for k,v in lugat.items():
            if v.startswith("@"):
                v = v.replace("@", "https://t.me/")
            create.button(
                text = k, url = v
            )
        create.adjust(3)
        return create.as_markup()

    else:
        for k,v in lugat.items():
            if v.startswith("@"):
                v = v.replace("@", "https://t.me/")
            create.button(
                text = k, url = v
            )
        create.adjust(4)
        return create.as_markup()

def copy_share(code, bot_username):    
    inside = InlineKeyboardBuilder()
    full_link = f"https://t.me/{bot_username}?start={code}"
    
    # Copy tugmasi uchun CopyTextButton obyekti yaratish kerak
    copy_button = InlineKeyboardButton(
        text="📝 Nusxalash", 
        copy_text=CopyTextButton(text=full_link)
    )
    
    # Share tugmasi oddiy url bilan
    share_button = InlineKeyboardButton(
        text="📤 Ulashish", 
        url=f"https://t.me/share/url?url={full_link}&text=Havola ustiga bosing va Admin bo'ling!"
    )
    refuse_button = InlineKeyboardButton(
        text = "Rad Etish ❌", 
        callback_data = "confirm_refuse"
    )
    
    inside.add(copy_button, share_button, refuse_button)
    inside.adjust(2)
    return inside.as_markup()