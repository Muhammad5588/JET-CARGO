import os
from dotenv import load_dotenv

load_dotenv()


async def get_admins():
    """Get admin list from database"""
    from data.Async_sqlDataBase import data_db as db
    return await db.admin_view()



DB_FILE = os.getenv('DB_FILE', 'data/database.sqlite3')

# ==================== BOT KONFIGURATSIYASI ====================

TOKEN = os.getenv("TOKEN")

# Guruh IDs
VERIFICATION_GROUP_ID = int(os.getenv('VERIFICATION_GROUP_ID', '0'))  # Tasdiq uchun guruh
VERIFIED_GROUP_ID = int(os.getenv('VERIFIED_GROUP_ID', '0'))          # Tasdiqlangan mijozlar
FEEDBACK_GROUP_ID = int(os.getenv('FEEDBACK_GROUP_ID', '0'))          # Feedback guruh


# ==================== FAYL YO'LLARI ====================

# Template rasmlar
PASSPORT_TEMPLATE = 'templates/pasport raqam.jpg'
PINFL_TEMPLATE = 'templates/pinfluz.jpg'
CHINA_ADDRESS_TEMPLATE = 'templates/china_address_template.jpg'

# Passport photos directory
PASSPORT_PHOTOS_DIR = 'data/passport_photos'

# Feedback fayl (backup uchun)
FEEDBACK_FILE = 'data/feedback.txt'

# Log fayl
LOG_FILE = 'logs/bot.log'


# ==================== BOT KONSTANTALARI ====================

# Client code boshlang'ich qiymati
CLIENT_CODE_START = int(os.getenv('CLIENT_CODE_START', 0))
CLIENT_CODE_PREFIX = os.getenv('CLIENT_CODE_PREFIX', "")
ADMIN_PPROFILE_USERNAME = os.getenv('ADMIN_PPROFILE_USERNAME', "")
CONTACT_PHONE_NUMBER = os.getenv('CONTACT_PHONE_NUMBER', "+998901234567")
PUBLIC_CHANNEL_LINK = os.getenv('PUBLIC_CHANNEL_LINK', "")
MANZIL = os.getenv('MANZIL', "Toshkent shahar")
ISH_VAQTI = os.getenv('ISH_VAQTI', "9:00 - 18:00")


# Pasport muddati (yillar)
PASSPORT_EXPIRY_WARNING_MONTHS = 6  # 6 oy qolganda ogohlantirish

# Qabul qilinadigan pasport prefikslari
VALID_PASSPORT_PREFIXES = ['AA', 'AB', 'AD', 'AE']
VALID_KARAKALPAK_PREFIX = 'K'  # K bilan boshlanuvchi barcha harflar

# PINFL birinchi raqamlari
VALID_PINFL_FIRST_DIGITS = ['3', '4', '5', '6']

# ==================== XITOY SKLAD ADRESI ====================

CHINA_ADDRESS_TEMPLATE_TEXT = """
🇨🇳 XITOY SKLAD MANZILI

收货人：{client_code}
电话：18161955318
西安市 雁塔区 丈八沟街道
高新区丈八六路49号103室中京仓库 ({client_code})
"""

# ==================== VERIFICATION STATUSI ====================

class VerificationStatus:
    PENDING = 'pending'      # Kutilmoqda
    APPROVED = 'approved'    # Tasdiqlangan
    REJECTED = 'rejected'    # Rad etilgan

# ==================== PASSPORT TYPES ====================

class PassportType:
    ID_CARD = 'id_card'      # Biometrik (2 ta rasm)
    BOOKLET = 'booklet'      # Kitobli (1 ta rasm)

# ==================== LOGGING ====================

LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = 'INFO'

# ==================== PAPKALARNI YARATISH ====================

def ensure_directories():
    """Kerakli papkalarni yaratish"""
    import os
    
    directories = [
        'data',
        'data/passport_photos',
        'templates',
        'logs'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

# ==================== YORDAMCHI FUNKSIYALAR ====================


def generate_client_code(user_id: int) -> str:
    """Client code generatsiya qilish"""
    return f"{CLIENT_CODE_PREFIX}{CLIENT_CODE_START + user_id:04d}"
