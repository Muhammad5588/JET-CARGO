import asyncio
import aiosqlite
import pytz
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple
import os
import logging
from contextlib import asynccontextmanager
from utils.exel_importer import ExcelUserImporter
from utils.validators import Validators


# Import constants only when needed to avoid circular imports
CLIENT_CODE_PREFIX = os.getenv("CLIENT_CODE_PREFIX", "X")
CLIENT_CODE_START = int(os.getenv("CLIENT_CODE_START", "1000"))

class VerificationStatus:
    PENDING = 'pending'      # Kutilmoqda
    APPROVED = 'approved'    # Tasdiqlangan
    REJECTED = 'rejected'    # Rad etilgan


logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_NAME = "database.sqlite3"

tashkent_tz = pytz.timezone("Asia/Tashkent")



class ConnectionPool:
    """Connection pool for aiosqlite with size limit"""
    
    def __init__(self, database_path: str, pool_size: int = 15):
        self.database_path = database_path
        self.pool_size = pool_size
        self._pool = None
        self._created = 0
        self._lock = None
        self._event_loop = None
    
    def _ensure_initialized(self):
        """Ensure pool is initialized in current event loop"""
        current_loop = asyncio.get_event_loop()
        if self._event_loop is None or self._event_loop != current_loop:
            # Reset for new event loop
            self._event_loop = current_loop
            self._pool = asyncio.Queue(maxsize=self.pool_size)
            self._lock = asyncio.Lock()
            self._created = 0
    
    async def _create_connection(self):
        """Create a new database connection with optimizations"""
        conn = await aiosqlite.connect(
            self.database_path,
            check_same_thread=False,
            timeout=30.0
        )
        # Enable WAL mode for better concurrency
        await conn.execute('PRAGMA journal_mode=WAL')
        # Optimize for speed
        await conn.execute('PRAGMA synchronous=NORMAL')
        await conn.execute('PRAGMA cache_size=-64000')  # 64MB cache
        await conn.execute('PRAGMA temp_store=MEMORY')
        await conn.execute('PRAGMA mmap_size=268435456')  # 256MB mmap
        return conn
    
    async def acquire(self):
        """Get connection from pool"""
        self._ensure_initialized()
        
        try:
            # Try to get existing connection without waiting
            return await asyncio.wait_for(self._pool.get(), timeout=0.1)
        except asyncio.TimeoutError:
            # Pool is empty, create new if under limit
            async with self._lock:
                if self._created < self.pool_size:
                    self._created += 1
                    return await self._create_connection()
            # Wait for available connection
            return await self._pool.get()
    
    async def release(self, conn):
        """Return connection to pool"""
        self._ensure_initialized()
        
        try:
            self._pool.put_nowait(conn)
        except asyncio.QueueFull:
            # Pool is full, close the connection
            await conn.close()
            async with self._lock:
                self._created -= 1
    
    async def close_all(self):
        """Close all connections in pool"""
        if self._pool is None:
            return
            
        while not self._pool.empty():
            try:
                conn = await asyncio.wait_for(self._pool.get(), timeout=1.0)
                await conn.close()
            except asyncio.TimeoutError:
                break
        self._created = 0
        self._pool = None
        self._lock = None
        self._event_loop = None


class AsyncDatabase:
    base_dir = Path(__file__).resolve()
    _pools = {}  # Dictionary to store pools per database path

    def __init__(self, inline_db_name, path_inline_db=None):
        PATH = path_inline_db or self.base_dir.parent
        self.database = PATH / inline_db_name
        self.db_path = str(self.database)
        
        # Initialize pool for this database (lazy, per event loop)
        if self.db_path not in AsyncDatabase._pools:
            AsyncDatabase._pools[self.db_path] = ConnectionPool(self.db_path, pool_size=15)
        
        self._pool = AsyncDatabase._pools[self.db_path]
    
    @asynccontextmanager
    async def get_connection(self):
        """Context manager for getting connection from pool"""
        conn = await self._pool.acquire()
        try:
            yield conn
        finally:
            await self._pool.release(conn)
    
    async def execute(self, code, items: tuple = ()):
        """Execute query with connection from pool"""
        async with self.get_connection() as conn:
            async with conn.execute(code, items) as cursor:
                await conn.commit()
                return cursor
    
    async def fetchall(self, code, items: tuple = ()):
        """Fetch all results"""
        async with self.get_connection() as conn:
            async with conn.execute(code, items) as cursor:
                return await cursor.fetchall()
    
    async def fetchone(self, code, items: tuple = ()):
        """Fetch one result"""
        async with self.get_connection() as conn:
            async with conn.execute(code, items) as cursor:
                return await cursor.fetchone()
    
    async def fetchmany(self, code, items: tuple = (), size=None):
        """Fetch many results"""
        async with self.get_connection() as conn:
            async with conn.execute(code, items) as cursor:
                return await cursor.fetchmany(size)

    # ==========================================
    #       INITIALIZATION
    # ==========================================

    async def start(self):
        """Initialize all tables"""
        async with self.get_connection() as conn:
            # Original tables
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS Integrated (
                    id INTEGER PRIMARY KEY, 
                    adminid INTEGER
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS admin (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    adminid INTEGER,
                    save_info TEXT,
                    admin_status TEXT,
                    majburiy_obuna_on_off INTEGER DEFAULT 0
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS password (
                    id INTEGER PRIMARY KEY,
                    one_step TEXT
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS obunachilar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tg_user INTEGER UNIQUE,
                    joined_at TIMESTAMP,
                    referal_id INTEGER
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS channels_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id TEXT,
                    admin INTEGER
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS majburiy_obuna (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id TEXT
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS for_ads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    messageID INTEGER,
                    from_forwardID INTEGER,
                    posted TEXT
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS for_post (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    file_id TEXT,
                    caption TEXT,
                    entities TEXT,
                    posted TEXT,
                    type_ads TEXT,
                    is_multiple TEXT
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS hamkorlik (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admin INTEGER,
                    admin_partner INTEGER
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS admin_code (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    code TEXT
                )
            """)
            
            # New tables from second code
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER,
                    client_code TEXT UNIQUE NOT NULL,
                    fullname TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    passport_number TEXT NOT NULL,
                    birth_date TEXT NOT NULL,
                    pinfl TEXT NOT NULL,
                    address TEXT NOT NULL,
                    china_address_confirmed BOOLEAN DEFAULT 0,
                    passport_front_file_id TEXT,
                    passport_back_file_id TEXT,
                    passport_front_file_unique_id TEXT,
                    passport_back_file_unique_id TEXT,
                    verification_status TEXT DEFAULT 'pending',
                    rejection_reason TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    language TEXT DEFAULT 'uz',
                    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    verified_at TIMESTAMP,
                    last_login TIMESTAMP
                )
            ''')
            
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS shipments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tracking_code TEXT NOT NULL,
                    shipping_name TEXT,
                    package_number TEXT,
                    weight REAL,
                    quantity INTEGER,
                    flight TEXT,
                    customer_code TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS feedbacks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    telegram_id INTEGER NOT NULL,
                    message TEXT NOT NULL,
                    admin_reply TEXT,
                    replied_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS verification_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    telegram_message_id INTEGER,
                    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            # Create indexes for better performance
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_admin_adminid ON admin(adminid)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_obunachilar_tg ON obunachilar(tg_user)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_channels_admin ON channels_data(admin)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_telegram_id ON users(telegram_id)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_client_code ON users(client_code)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_phone ON users(phone)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_tracking_code ON shipments(tracking_code)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_customer_code ON shipments(customer_code)')

            # Birinchi admin 5374094754 ni avtomatik qo'shish (agar table bo'sh bo'lsa)
            admin_check = await conn.execute('SELECT COUNT(*) FROM admin')
            admin_count = await admin_check.fetchone()
            if admin_count[0] == 0:
                await conn.execute(
                    "INSERT INTO admin (adminid, admin_status, majburiy_obuna_on_off) VALUES (?, ?, ?)",
                    (5374094754, 'del', 0)
                )
                logger.info("Default admin 5374094754 added")

            await conn.commit()
            logger.info("Database initialized successfully with all tables and indexes")

    # ==========================================
    #       ADMIN SECTION (Original Code)
    # ==========================================

    async def register_user_with_code(self, client_code: str, telegram_id: Optional[int], user_data: Dict) -> Tuple[bool, str, str]:
        """
        Mavjud client_code bilan foydalanuvchini ro'yxatdan o'tkazish
        (Excel import uchun)

        Args:
            client_code: Mavjud client code (code_str)
            telegram_id: Telegram ID (ixtiyoriy, None bo'lishi mumkin)
            user_data: Foydalanuvchi ma'lumotlari

        Returns:
            (success, message, client_code)
        """
        try:
            await self.execute('''
                INSERT INTO users
                (telegram_id, client_code, fullname, phone, passport_number,
                 birth_date, pinfl, address,
                 passport_front_file_id, passport_back_file_id,
                 passport_front_file_unique_id, passport_back_file_unique_id,
                 language, verification_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                telegram_id,  # None bo'lishi mumkin
                client_code.upper(),  # Katta harfda saqlash
                user_data['fullname'],
                user_data['phone'],
                user_data['passport_number'],
                user_data['birth_date'],
                user_data['pinfl'],
                user_data['address'],
                user_data.get('passport_front_file_id'),
                user_data.get('passport_back_file_id'),
                user_data.get('passport_front_file_unique_id'),
                user_data.get('passport_back_file_unique_id'),
                user_data.get('language', 'uz'),
                VerificationStatus.APPROVED  # Excel dan kelganlar auto-approved
            ))
            
            logger.info(f"User registered with code: {client_code} (telegram_id: {telegram_id or 'None'})")
            return True, "Success", client_code
        
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return False, str(e), ""

    async def admin_view(self):
        result = await self.fetchall("SELECT adminid FROM admin")
        return list(*zip(*result)) if result else []

    async def is_admin(self, chat_id) -> bool:
        result = await self.fetchall("SELECT adminid FROM admin WHERE adminid = ?", (chat_id,))
        return bool(len(result))

    async def del_admin(self, id):
        await self.execute("DELETE FROM admin WHERE id = ?", (id,))

    async def admin_plus(self, chat_id):
        await self.execute("INSERT INTO admin(adminid) VALUES(?)", (chat_id,))

    async def replace_admin(self, new_owner):
        await self.execute("UPDATE admin SET adminid = ? WHERE id = 1", (new_owner,))
        return "Botning yangi egasi tayinlandi."

    async def new_pass(self, password):
        await self.execute("UPDATE password SET one_step = ? WHERE id = 1", (password,))
        return "Botga yangi parol qo'yildi."

    async def one_step_password_view(self):
        result = await self.fetchone("SELECT one_step FROM password WHERE id = 1")
        return result[0] if result else None

    async def vkm_stili_admin(self):
        return await self.fetchall("SELECT id, adminid FROM admin LIMIT 8")

    async def view_list_admin(self, kichik_id, katta_id):
        return await self.fetchall("""
            SELECT id, adminid FROM admin
            WHERE id BETWEEN ? AND ?
            ORDER BY id
        """, (kichik_id, katta_id))

    async def is_max(self):
        result = await self.fetchone("SELECT MAX(id) FROM admin")
        return result[0] if result else None

    async def is_min(self):
        result = await self.fetchone("SELECT MIN(id) FROM admin")
        return result[0] if result else None

    async def get_malumot_admin(self, id):
        result = await self.fetchone("SELECT adminid FROM admin WHERE id = ?", (id,))
        return result[0] if result else None

    async def save_info(self, id, admin_id):
        await self.execute("UPDATE admin SET save_info = ? WHERE adminid = ?", (id, admin_id))

    async def save_info_view(self, adminid):
        result = await self.fetchone("SELECT save_info FROM admin WHERE adminid = ?", (adminid,))
        return result[0] if result else None

    async def is_owner(self, user_id):
        result = await self.fetchone("SELECT adminid FROM admin WHERE id = 1")
        return bool(result and result[0] == user_id)

    async def owner_view(self):
        result = await self.fetchone("SELECT adminid FROM admin WHERE id = 1")
        return result[0] if result else None

    # ==========================================
    #       USER SECTION (Original Code)
    # ==========================================

    async def user_plus(self, chat_id, referrer_id=None):
        if referrer_id is None:
            await self.execute("""
                INSERT INTO obunachilar (tg_user, joined_at) VALUES(?, ?)
            """, (chat_id, datetime.now(tashkent_tz)))
        else:
            await self.execute("""
                INSERT INTO obunachilar (tg_user, joined_at, referal_id) VALUES(?, ?, ?)
            """, (chat_id, datetime.now(tashkent_tz), referrer_id))

    async def is_user(self, chat_id) -> bool:
        result = await self.fetchall("SELECT tg_user FROM obunachilar WHERE tg_user = ?", (chat_id,))
        return bool(len(result))

    async def user_view(self):
        result = await self.fetchall("SELECT tg_user FROM obunachilar")
        return list(*zip(*result)) if result else []

    async def user_count(self):
        try:
            result = await self.fetchone("SELECT COUNT(id) FROM users")
            return result[0] if result else 0
        except Exception as e:
            logger.error(f"Error in user_count: {e}")
            return 0

    async def last24_user_view(self):
        try:
            twenty_four_hours_ago = datetime.now(tashkent_tz) - timedelta(hours=24)
            one_month_ago = datetime.now(tashkent_tz) - timedelta(days=30)

            result_last30 = await self.fetchone(
                "SELECT COUNT(*) FROM obunachilar WHERE joined_at >= ?",
                (one_month_ago,)
            )
            result_last24 = await self.fetchone(
                "SELECT COUNT(*) FROM obunachilar WHERE joined_at >= ?",
                (twenty_four_hours_ago,)
            )

            return (result_last24[0] if result_last24 else 0,
                    result_last30[0] if result_last30 else 0)
        except Exception as e:
            logger.error(f"Error in last24_user_view: {e}")
            return 0, 0

    async def del_user(self, user_id):
        await self.execute("DELETE FROM obunachilar WHERE tg_user = ?", (user_id,))

    # ==========================================
    #       CHANNEL MANAGEMENT (Original Code)
    # ==========================================

    async def channel_plus(self, channel_id, admin_id):
        await self.execute("""
            INSERT INTO channels_data(channel_id, admin) VALUES(?, ?)
        """, (channel_id, admin_id))

    async def is_channel(self, channel_id, id_num=None) -> bool:
        if id_num is None and channel_id != "1280":
            result = await self.fetchall(
                "SELECT channel_id FROM channels_data WHERE channel_id = ?",
                (channel_id,)
            )
        else:
            result = await self.fetchall(
                "SELECT channel_id FROM channels_data WHERE id = ?",
                (id_num,)
            )
        return bool(len(result))

    async def chanel_count(self):
        result = await self.fetchone("SELECT COUNT(channel_id) FROM channels_data")
        return result[0] if result else 0

    async def channel_view(self):
        result = await self.fetchall("SELECT channel_id FROM channels_data")
        return list(*zip(*result)) if result else []

    async def channel_view_byID(self, admin_id):
        result = await self.fetchall(
            "SELECT channel_id FROM channels_data WHERE admin = ?",
            (admin_id,)
        )
        return list(*zip(*result)) if result else []

    async def exist_user_for_post(self, chat_id) -> bool:
        try:
            result = await self.fetchall("SELECT user_id FROM for_post WHERE user_id=?", (chat_id,))
            return bool(len(result))
        except Exception as e:
            logger.error(e)
            return False

    async def choosen_channel(self, user_id, channel_id):
        if await self.exist_user_for_post(user_id):
            await self.execute("UPDATE for_post SET posted = ? WHERE user_id = ?", (channel_id, user_id))
        else:
            await self.execute("INSERT INTO for_post(user_id, posted) VALUES(?, ?)", (user_id, channel_id))

    async def choosen_channel_view(self, user_id):
        try:
            result = await self.fetchone("SELECT posted FROM for_post WHERE user_id = ?", (user_id,))
            return "" if result is None or result[0] is None else result[0]
        except Exception as e:
            logger.error(e)
            return ""

    async def vkm_stili(self, admin_id, force_minus=None):
        if force_minus is None:
            if not (await self.is_owner(admin_id)):
                return await self.fetchall(
                    "SELECT id, channel_id FROM channels_data WHERE admin = ? LIMIT 8",
                    (admin_id,)
                )
            return await self.fetchall("SELECT id, channel_id FROM channels_data LIMIT 8")
        return await self.fetchall("SELECT id, channel_id FROM majburiy_obuna LIMIT 8")

    async def get_malumot(self, id):
        result = await self.fetchone("SELECT channel_id FROM channels_data WHERE id = ?", (id,))
        return result[0] if result else None

    async def is_max_channel(self, user_id=None):
        if user_id is None:
            result = await self.channel_view()
            result1 = await self.majburiy_subs_view()
            c = [i for i in result if i not in result1]
            if not c:
                return None
            result2 = max(c)
            row = await self.fetchone("SELECT id FROM channels_data WHERE channel_id = ?", (result2,))
            return row[0] if row else None

        if await self.is_owner(user_id):
            result = await self.fetchone("SELECT MAX(id) FROM channels_data")
            return result[0] if result else None

        result = await self.fetchone(
            "SELECT MAX(id) FROM channels_data WHERE admin = ?",
            (user_id,)
        )
        return result[0] if result else None

    async def is_min_channel(self, user_id=None):
        if user_id is None:
            result = await self.channel_view()
            result1 = await self.majburiy_subs_view()
            c = [i for i in result if i not in result1]
            if not c:
                return None
            result2 = min(c)
            row = await self.fetchone("SELECT id FROM channels_data WHERE channel_id = ?", (result2,))
            return row[0] if row else None

        if await self.is_owner(user_id):
            result = await self.fetchone("SELECT MIN(id) FROM channels_data")
            return result[0] if result else None

        result = await self.fetchone(
            "SELECT MIN(id) FROM channels_data WHERE admin = ?",
            (user_id,)
        )
        return result[0] if result else None

    async def is_min_majburiy(self):
        result = await self.fetchone("SELECT MIN(id) FROM majburiy_obuna")
        return result[0] if result else None

    async def is_max_majburiy(self):
        result = await self.fetchone("SELECT MAX(id) FROM majburiy_obuna")
        return result[0] if result else None

    async def get_chat_members_for_promoting_admin(self):
        result = await self.fetchone("SELECT channel_id FROM channels_data WHERE id = 1")
        return result[0] if result else None

    async def view_list_channel(self, admin_id, kichik_id, katta_id):
        return await self.fetchall("""
            SELECT id, channel_id FROM channels_data
            WHERE admin = ? AND id BETWEEN ? AND ?
            ORDER BY id LIMIT 8
        """, (admin_id, kichik_id, katta_id))

    async def view_list_majburiy(self, kichik_id, katta_id):
        return await self.fetchall("""
            SELECT id, channel_id FROM majburiy_obuna
            WHERE id BETWEEN ? AND ?
            ORDER BY id LIMIT 8
        """, (kichik_id, katta_id))

    async def remove_channel(self, channel_rowid):
        await self.execute("DELETE FROM channels_data WHERE id = ?", (channel_rowid,))

    async def admin_status(self, user_id, clear=None):
        chan = "del" if clear is None else ' '
        await self.execute("UPDATE admin SET admin_status = ? WHERE adminid = ?", (chan, user_id))

    async def admin_status_view(self, user_id) -> bool:
        result = await self.fetchone("SELECT admin_status FROM admin WHERE adminid = ?", (user_id,))
        return str(result[0]) == "del" if result else False

    async def is_add_channel(self, user_id) -> bool:
        results = await self.fetchall(
            "SELECT admin FROM channels_data WHERE admin = ?",
            (user_id,)
        )
        return bool(len(results))

    async def majburiy_subs_view(self):
        result = await self.fetchall("SELECT channel_id FROM majburiy_obuna")
        return list(*zip(*result)) if result else []

    async def is_majburiy_channel(self, id_num):
        result = await self.fetchone("SELECT channel_id FROM channels_data WHERE id = ?", (id_num,))
        if not result:
            return False
        result1 = result[0]
        majburiy_list = await self.majburiy_subs_view()
        return result1 in majburiy_list

    async def count_majburiy(self):
        result = await self.fetchone("SELECT COUNT(id) FROM majburiy_obuna")
        return result[0] if result else 0

    async def status_force(self, kod=None):
        if kod is None:
            result = await self.fetchone(
                "SELECT majburiy_obuna_on_off FROM admin WHERE id = 1"
            )
            if not result:
                return False
            return int(result[0]) == 1
        else:
            value = 1 if int(kod) == 1 else 0
            await self.execute("UPDATE admin SET majburiy_obuna_on_off = ? WHERE id = 1", (value,))

    async def add_majburiy_channel(self, id_num):
        result = await self.fetchone("SELECT channel_id FROM channels_data WHERE id = ?", (id_num,))
        if result:
            await self.execute("INSERT INTO majburiy_obuna(channel_id) VALUES(?)", (result[0],))

    async def remove_majburiy_channel(self, id_num):
        await self.execute("DELETE FROM majburiy_obuna WHERE id = ?", (id_num,))

    async def is_between_majburiy(self, id_num):
        results = await self.fetchall("SELECT channel_id FROM majburiy_obuna WHERE id = ?", (id_num,))
        return bool(len(results))

    # ==========================================
    #       ADS PREPARATION (Original Code)
    # ==========================================

    async def exist_user_ads(self, chat_id) -> bool:
        try:
            result = await self.fetchall("SELECT user_id FROM for_ads WHERE user_id=?", (chat_id,))
            return bool(len(result))
        except Exception as e:
            logger.error(e)
            return False

    async def for_ads(self, user_id, message_id, forward_chatID, posted):
        if await self.exist_user_ads(user_id):
            await self.execute(
                "UPDATE for_ads SET messageID = ?, from_forwardID = ?, posted = ? WHERE user_id = ?",
                (message_id, forward_chatID, posted, user_id)
            )
        else:
            await self.execute(
                "INSERT INTO for_ads(user_id, messageID, from_forwardID, posted) VALUES(?, ?, ?, ?)",
                (user_id, message_id, forward_chatID, posted)
            )

    async def for_ads_view(self, user_id):
        result = await self.fetchall(
            "SELECT messageID, from_forwardID, posted FROM for_ads WHERE user_id = ?",
            (user_id,)
        )
        return list(*zip(*result)) if result else []

    async def for_ads_bot(self, user_id, message_id, forward_chatID):
        if await self.exist_user_ads(user_id):
            await self.execute(
                "UPDATE for_ads SET messageID = ?, from_forwardID = ? WHERE user_id = ?",
                (message_id, forward_chatID, user_id)
            )
        else:
            await self.execute(
                "INSERT INTO for_ads(user_id, messageID, from_forwardID) VALUES(?, ?, ?)",
                (user_id, message_id, forward_chatID)
            )

    async def for_post(self, user_id, file_id, caption, entities, posted, type_ads):
        if await self.exist_user_for_post(user_id):
            await self.execute(
                "UPDATE for_post SET file_id = ?, caption = ?, entities = ?, posted = ?, type_ads = ? WHERE user_id = ?",
                (file_id, caption, entities, posted, type_ads, user_id)
            )
        else:
            await self.execute(
                "INSERT INTO for_post(user_id, file_id, caption, entities, posted, type_ads) VALUES(?, ?, ?, ?, ?, ?)",
                (user_id, file_id, caption, entities, posted, type_ads)
            )

    async def for_post_with_caption(self, user_id, file_id, caption, entities, type_ads):
        if await self.exist_user_for_post(user_id):
            await self.execute(
                "UPDATE for_post SET file_id = ?, caption = ?, entities = ?, type_ads = ? WHERE user_id = ?",
                (file_id, caption, entities, type_ads, user_id)
            )
        else:
            await self.execute(
                "INSERT INTO for_post(user_id, file_id, caption, entities, type_ads) VALUES(?, ?, ?, ?, ?)",
                (user_id, file_id, caption, entities, type_ads)
            )

    async def for_post_multiple(self, user_id):
        multiple = "multi"
        if await self.exist_user_for_post(user_id):
            await self.execute("UPDATE for_post SET is_multiple = ? WHERE user_id = ?", (multiple, user_id))
        else:
            await self.execute("INSERT INTO for_post(user_id, is_multiple) VALUES(?, ?)", (user_id, multiple))

    async def for_post_is_multiple(self, user_id):
        result = await self.fetchone("SELECT is_multiple FROM for_post WHERE user_id = ?", (user_id,))
        if not result or result[0] is None or result[0] == "":
            return 'bot'
        return result[0]

    async def for_post_single(self, user_id):
        single = "single"
        if await self.exist_user_for_post(user_id):
            await self.execute("UPDATE for_post SET is_multiple = ? WHERE user_id = ?", (single, user_id))
        else:
            await self.execute("INSERT INTO for_post(user_id, is_multiple) VALUES(?, ?)", (user_id, single))

    async def for_post_bot(self, user_id):
        bot_type = "bot"
        if await self.exist_user_for_post(user_id):
            await self.execute("UPDATE for_post SET is_multiple = ? WHERE user_id = ?", (bot_type, user_id))
        else:
            await self.execute("INSERT INTO for_post(user_id, is_multiple) VALUES(?, ?)", (user_id, bot_type))

    async def is_type_post(self, chat_id):
        result = await self.fetchone("SELECT type_ads FROM for_post WHERE user_id = ?", (chat_id,))
        return result[0] if result else None

    async def for_post_view(self, chat_id):
        results = await self.fetchall(
            "SELECT file_id, caption, entities, posted FROM for_post WHERE user_id = ?",
            (chat_id,)
        )
        if results:
            return list(results[0])
        return []

    async def for_elon(self, user_id, elon, entity, type_ads):
        if await self.exist_user_for_post(user_id):
            await self.execute(
                "UPDATE for_post SET caption = ?, entities = ?, type_ads = ? WHERE user_id = ?",
                (elon, entity, type_ads, user_id)
            )
        else:
            await self.execute(
                "INSERT INTO for_post(user_id, caption, entities, type_ads) VALUES(?, ?, ?, ?)",
                (user_id, elon, entity, type_ads)
            )

    async def for_elon_view(self, user_id):
        results = await self.fetchall(
            "SELECT caption, entities, type_ads FROM for_post WHERE user_id = ?",
            (user_id,)
        )
        return list(*zip(*results)) if results else []

    # ==========================================
    #       PARTNERSHIP (Original Code)
    # ==========================================

    async def exist_user_hamkorlik(self, chat_id, admin_id=None) -> bool:
        try:
            if admin_id is None:
                if not (await self.is_owner(chat_id)):
                    result = await self.fetchall(
                        "SELECT admin_partner FROM hamkorlik WHERE admin_partner = ?",
                        (chat_id,)
                    )
                    return bool(len(result))
                return False

            if not (await self.is_owner(chat_id)):
                result = await self.fetchall(
                    "SELECT admin_partner FROM hamkorlik WHERE admin_partner = ?",
                    (chat_id,)
                )
                result1 = await self.fetchall(
                    "SELECT admin FROM hamkorlik WHERE admin = ?",
                    (admin_id,)
                )
                return bool(len(result)), bool(len(result1))
            return False
        except Exception as e:
            logger.error(e)
            return False

    async def plus_partner(self, admin_id, partner_id):
        await self.execute(
            "INSERT INTO hamkorlik(admin, admin_partner) VALUES(?, ?)",
            (admin_id, partner_id)
        )

    async def remove_partner(self, partner_id):
        await self.execute("DELETE FROM hamkorlik WHERE id = ?", (partner_id,))

    async def admin_partner(self, user_id):
        result = await self.fetchone(
            "SELECT admin FROM hamkorlik WHERE admin_partner = ?",
            (user_id,)
        )
        if not result:
            return []
        admin = result[0]
        return await self.fetchall(
            "SELECT id, channel_id FROM channels_data WHERE admin = ? LIMIT 8",
            (admin,)
        )

    async def admin_partner_view(self, user_id):
        return await self.fetchall(
            "SELECT id, admin_partner FROM hamkorlik WHERE admin = ? LIMIT 8",
            (user_id,)
        )

    async def vkm_list_admin_partner(self, admin_id, kichik_id, katta_id):
        return await self.fetchall("""
            SELECT id, admin_partner FROM hamkorlik
            WHERE admin = ? AND id BETWEEN ? AND ?
            ORDER BY id LIMIT 8
        """, (admin_id, kichik_id, katta_id))

    async def exist_two_of_us(self, admin_id, partner_id):
        try:
            result = await self.fetchone(
                "SELECT admin_partner FROM hamkorlik WHERE admin = ?",
                (admin_id,)
            )
            result1 = await self.fetchone(
                "SELECT admin FROM hamkorlik WHERE admin_partner = ?",
                (partner_id,)
            )
            if result and result1:
                return int(result[0]) == int(partner_id) or int(result1[0]) == int(admin_id)
            return False
        except:
            return False

    async def is_min_max_hamkorlik(self, admin_id):
        result = await self.fetchall(
            "SELECT admin_partner FROM hamkorlik WHERE admin = ?",
            (admin_id,)
        )
        if not result:
            return None, None
        
        my_list = []
        for i in list(*zip(*result)):
            row = await self.fetchone(
                "SELECT id FROM hamkorlik WHERE admin_partner = ?",
                (i,)
            )
            if row:
                my_list.append(row[0])
        
        return (min(my_list), max(my_list)) if my_list else (None, None)

    async def view_list_admin_partner(self, user_id, kichik_id, katta_id):
        result = await self.fetchone(
            "SELECT admin FROM hamkorlik WHERE admin_partner = ?",
            (user_id,)
        )
        if not result:
            return []
        
        admin = result[0]
        return await self.fetchall("""
            SELECT id, channel_id FROM channels_data
            WHERE admin = ? AND id BETWEEN ? AND ?
            ORDER BY id LIMIT 8
        """, (admin, kichik_id, katta_id))

    async def is_exist_id(self, id):
        results = await self.fetchall("SELECT id FROM hamkorlik WHERE id = ?", (id,))
        return bool(len(results))

    async def get_malumot_hamkorlik(self, id):
        result = await self.fetchone(
            "SELECT admin_partner FROM hamkorlik WHERE id = ?",
            (id,)
        )
        return result[0] if result else None

    # ==========================================
    #       ADMIN CODES (Original Code)
    # ==========================================

    async def is_adminID_code(self, user_id) -> bool:
        results = await self.fetchall("SELECT user_id FROM admin_code WHERE user_id = ?", (user_id,))
        return bool(len(results))

    async def add_adminCode(self, admin_id, code):
        if await self.is_adminID_code(admin_id):
            await self.execute("DELETE FROM admin_code WHERE user_id = ?", (admin_id,))
        await self.execute("INSERT INTO admin_code(user_id, code) VALUES(?, ?)", (admin_id, code))

    async def check_code(self, code):
        results = await self.fetchall("SELECT code FROM admin_code WHERE code = ?", (code,))
        return bool(len(results))

    async def delete_code(self, code):
        await self.execute("DELETE FROM admin_code WHERE code = ?", (code,))

    # ==========================================
    #       USER MANAGEMENT (New from Code 2)
    # ==========================================

    async def is_user_registered(self, telegram_id: int) -> bool:
        """Foydalanuvchi ro'yxatdan o'tganmi?"""
        result = await self.fetchone(
            'SELECT id FROM users WHERE telegram_id = ? AND is_active = 1',
            (telegram_id,)
        )
        return result is not None

    async def is_client_active(self, telegram_id: int) -> bool:
        """Foydalanuvchi faolmi?"""
        result = await self.fetchone(
            'SELECT is_active FROM users WHERE telegram_id = ?',
            (telegram_id,)
        )
        return bool(result and result[0] == 1)
    
    async def deactivate_user(self, telegram_id: int) -> None:
        """Foydalanuvchini deaktivatsiya qilish"""
        await self.execute(
            'UPDATE users SET is_active = 0 WHERE telegram_id = ?',
            (telegram_id,)
        )
    
    async def activate_user(self, telegram_id: int) -> None:
        """Foydalanuvchini aktivatsiya qilish"""
        await self.execute(
            'UPDATE users SET is_active = 1 WHERE telegram_id = ?',
            (telegram_id,)
        )

    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict]:
        """Telegram ID bo'yicha foydalanuvchini olish"""
        async with self.get_connection() as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(
                'SELECT * FROM users WHERE telegram_id = ? AND is_active = 1',
                (telegram_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """ID bo'yicha foydalanuvchini olish"""
        async with self.get_connection() as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(
                'SELECT * FROM users WHERE id = ? AND is_active = 1',
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def get_user_by_client_code(self, client_code: str) -> Optional[Dict]:
        """Mijoz kodi bo'yicha foydalanuvchini olish"""
        async with self.get_connection() as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(
                'SELECT * FROM users WHERE UPPER(client_code) = UPPER(?) AND is_active = 1',
                (client_code,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def search_users(self, query: str) -> List[Dict]:
        """Foydalanuvchilarni qidirish"""
        clean_query = query.replace('+', '').replace(' ', '').replace('-', '')
        
        async with self.get_connection() as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute('''
                SELECT * FROM users 
                WHERE (UPPER(client_code) = UPPER(?) OR phone LIKE ?)
                AND is_active = 1
                ORDER BY registered_at DESC
            ''', (query, f'%{clean_query}%')) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def generate_client_code(self) -> str:
        """Yangi client code generatsiya qilish"""
        rows = await self.fetchall('''
            SELECT client_code FROM users
            WHERE UPPER(client_code) LIKE UPPER(?)
        ''', (f'{CLIENT_CODE_PREFIX}%',))

        if rows:
            max_number = CLIENT_CODE_START - 1
            for row in rows:
                try:
                    code = row[0].upper()
                    number = int(code.replace(CLIENT_CODE_PREFIX, ''))
                    if number > max_number:
                        max_number = number
                except:
                    continue
            next_number = max_number + 1
        else:
            next_number = CLIENT_CODE_START

        return f"{CLIENT_CODE_PREFIX}{next_number:03d}"

    async def register_user(self, telegram_id: int, user_data: Dict) -> Tuple[bool, str, str]:
        """Yangi foydalanuvchini ro'yxatdan o'tkazish"""
        try:
            client_code = await self.generate_client_code()

            await self.execute('''
                INSERT INTO users
                (telegram_id, client_code, fullname, phone, passport_number,
                 birth_date, pinfl, address,
                 passport_front_file_id, passport_back_file_id,
                 passport_front_file_unique_id, passport_back_file_unique_id,
                 language, verification_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                telegram_id,
                client_code,
                user_data['fullname'],
                user_data['phone'],
                user_data['passport_number'],
                user_data['birth_date'],
                user_data['pinfl'],
                user_data['address'],
                user_data.get('passport_front_file_id'),
                user_data.get('passport_back_file_id'),
                user_data.get('passport_front_file_unique_id'),
                user_data.get('passport_back_file_unique_id'),
                user_data.get('language', 'uz'),
                VerificationStatus.PENDING
            ))
            
            logger.info(f"User registered: {telegram_id} -> {client_code}")
            return True, "Success", client_code
        
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return False, str(e), ""

    async def verify_login(self, client_code: str, phone: str) -> Optional[Dict]:
        """Login ma'lumotlarini tekshirish"""
        clean_phone = phone.replace('+', '').replace(' ', '').replace('-', '')
        
        async with self.get_connection() as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute('''
                SELECT * FROM users 
                WHERE UPPER(client_code) = UPPER(?) 
                AND phone LIKE ? 
                AND is_active = 1
            ''', (client_code, f'%{clean_phone}%')) as cursor:
                row = await cursor.fetchone()
                
                if row:
                    await conn.execute(
                        'UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?',
                        (row['id'],)
                    )
                    await conn.commit()
                
                return dict(row) if row else None

    # ==========================================
    #       VERIFICATION (New from Code 2)
    # ==========================================

    async def add_to_verification_queue(self, user_id: int, message_id: int) -> bool:
        """Verification queuega qo'shish"""
        try:
            await self.execute('''
                INSERT INTO verification_queue (user_id, telegram_message_id)
                VALUES (?, ?)
            ''', (user_id, message_id))
            return True
        except Exception as e:
            logger.error(f"Add to queue error: {e}")
            return False

    async def approve_user(self, user_id: int) -> bool:
        """Foydalanuvchini tasdiqlash"""
        try:
            await self.execute('''
                UPDATE users 
                SET verification_status = ?, 
                    verified_at = CURRENT_TIMESTAMP,
                    rejection_reason = NULL
                WHERE id = ?
            ''', (VerificationStatus.APPROVED, user_id))
            
            logger.info(f"User {user_id} approved")
            return True
        except Exception as e:
            logger.error(f"Approve error: {e}")
            return False

    async def reject_user(self, user_id: int, reason: str) -> bool:
        """Foydalanuvchini rad etish"""
        try:
            await self.execute('''
                UPDATE users 
                SET verification_status = ?, 
                    rejection_reason = ?
                WHERE id = ?
            ''', (VerificationStatus.REJECTED, reason, user_id))
            
            await self.delete_user_by_telegram_id(user_id)
            
            logger.info(f"User {user_id} rejected: {reason}")
            return True
        except Exception as e:
            logger.error(f"Reject error: {e}")
            return False

    async def confirm_china_address(self, user_id: int) -> bool:
        """Xitoy manzilini tasdiqlash"""
        try:
            await self.execute(
                'UPDATE users SET china_address_confirmed = 1 WHERE id = ?',
                (user_id,)
            )
            return True
        except Exception as e:
            logger.error(f"China address confirm error: {e}")
            return False

    # ==========================================
    #       SHIPMENTS (New from Code 2)
    # ==========================================

    async def search_by_tracking_code(self, code: str) -> List[Dict]:
        """Trek kodi bo'yicha qidirish"""
        async with self.get_connection() as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute('''
                SELECT * FROM shipments 
                WHERE LOWER(tracking_code) = LOWER(?)
            ''', (code.strip(),)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def search_by_customer_code(self, code: str) -> List[Dict]:
        """Mijoz kodi bo'yicha qidirish"""
        async with self.get_connection() as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute('''
                SELECT * FROM shipments 
                WHERE LOWER(customer_code) = LOWER(?)
                ORDER BY id DESC
            ''', (code.strip(),)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def import_shipments_from_file(self, file_path: str) -> Tuple[bool, str]:
        """Excel yoki CSV fayldan yuklar import qilish"""
        try:
            import pandas as pd
            
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path, encoding='utf-8')
            elif file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                return False, "Noto'g'ri fayl formati"
            
            required_columns = ['Shipment Tracking Code', 'Customer code']
            if not all(col in df.columns for col in required_columns):
                return False, f"Kerakli ustunlar topilmadi: {required_columns}"
            
            df = df.fillna('')
            
            async with self.get_connection() as conn:
                await conn.execute('DELETE FROM shipments')
                
                for _, row in df.iterrows():
                    await conn.execute('''
                        INSERT INTO shipments 
                        (tracking_code, shipping_name, package_number, 
                         weight, quantity, flight, customer_code)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        str(row.get('Shipment Tracking Code', '')).strip(),
                        str(row.get('Shipping Name', '')).strip(),
                        str(row.get('Package Number', '')).strip(),
                        float(row.get('Weight/KG', 0) or 0),
                        int(row.get('Quantity', 0) or 0),
                        str(row.get('Flight', '')).strip(),
                        str(row.get('Customer code', '')).strip()
                    ))
                
                await conn.commit()
                count = len(df)
                logger.info(f"Imported {count} shipments")
                return True, f"{count} ta yuk yuklandi"
        
        except Exception as e:
            logger.error(f"Import error: {e}")
            return False, str(e)

    # ==========================================
    #       FEEDBACK (New from Code 2)
    # ==========================================

    async def save_feedback(self, user_id: int, telegram_id: int, message: str) -> Optional[int]:
        """Feedbackni saqlash"""
        try:
            cursor = await self.execute('''
                INSERT INTO feedbacks (user_id, telegram_id, message)
                VALUES (?, ?, ?)
            ''', (user_id, telegram_id, message))
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Save feedback error: {e}")
            return None

    async def save_feedback_reply(self, feedback_id: int, reply: str) -> bool:
        """Feedbackga admin javobini saqlash"""
        try:
            await self.execute('''
                UPDATE feedbacks 
                SET admin_reply = ?, replied_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (reply, feedback_id))
            return True
        except Exception as e:
            logger.error(f"Save reply error: {e}")
            return False

    async def sdel(self) -> bool:
        """Barcha userlarni o'chirish (test uchun)"""
        try:
            await self.execute('DELETE FROM users')
            return True
        except Exception as e:
            logger.error(f"delete users error: {e}")
            return False

    async def get_feedback_by_id(self, feedback_id: int) -> Optional[Dict]:
        """Feedback ni ID bo'yicha olish"""
        async with self.get_connection() as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(
                'SELECT * FROM feedbacks WHERE id = ?',
                (feedback_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    # ==========================================
    #       STATISTICS (New from Code 2)
    # ==========================================

    async def get_all_active_users(self) -> List[Dict]:
        """Barcha faol foydalanuvchilar"""
        async with self.get_connection() as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute('''
                SELECT * FROM users 
                WHERE is_active = 1 AND verification_status = ?
                ORDER BY registered_at DESC
            ''', (VerificationStatus.APPROVED,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_user_count_new(self) -> int:
        """Yangi users jadvalidagi foydalanuvchilar soni"""
        result = await self.fetchone('SELECT COUNT(*) FROM users WHERE is_active = 1')
        return result[0] if result else 0

    async def import_users_excel_background(
        self,
        file_path: str,
        bot,
        admin_id: int
    ) -> None:
        """
        Background taskda foydalanuvchilarni import qilish
        
        Bu metodni AsyncDatabase klassiga qo'shing!
        """
        import os
        from aiogram.types import FSInputFile
        
        try:
            await bot.send_message(
                admin_id,
                "📥 Excel fayl import qilish boshlandi...\n"
                "Bu biroz vaqt olishi mumkin."
            )
            
            importer = ExcelUserImporter(self)
            success_count, failed_count, failed_file = await importer.import_users_from_excel(file_path)
            
            # Natijani adminga yuborish
            result_message = (
                f"✅ Import yakunlandi!\n\n"
                f"✅ Muvaffaqiyatli: {success_count} ta foydalanuvchi\n"
                f"❌ Xatolik: {failed_count} ta foydalanuvchi"
            )
            
            if failed_count > 0:
                result_message += "\n\n⚠️ Ba'zi foydalanuvchilar validatsiyadan o'tmadi."
            
            await bot.send_message(admin_id, result_message)
            
            # Agar muvaffaqiyatsiz qatorlar bo'lsa, Excel faylni yuborish
            if failed_file and os.path.exists(failed_file):
                document = FSInputFile(failed_file)
                await bot.send_document(
                    admin_id,
                    document,
                    caption=(
                        f"❌ Bu faylda {failed_count} ta foydalanuvchi ro'yxati\n\n"
                        "Sabablari error_reason ustunida ko'rsatilgan:\n"
                        "• Passport noto'g'ri formatda\n"
                        "• Telefon raqam noto'g'ri\n"
                        "• PINFL 14 ta raqamdan iborat emas\n"
                        "• PINFL 3,4,5,6 dan boshlanmaydi\n"
                        "• Ism, manzil yoki tug'ilgan sana bo'sh\n"
                        "• Client code yoki Telegram ID takrorlangan"
                    )
                )

                # Faylni o'chirish
                try:
                    os.remove(failed_file)
                except:
                    pass

            # Baza faylini zaxira nusxasi sifatida yuborish
            try:
                database_file = FSInputFile(self.db_path)
                await bot.send_document(
                    admin_id,
                    database_file,
                    caption=f"💾 Yangilangan bazaning zaxira nusxasi\n\n"
                        f"Jami foydalanuvchilar: {success_count}"
                )
                logger.info("Database backup sent successfully")
            except Exception as e:
                logger.error(f"Database send error: {str(e)}")
                try:
                    await bot.send_message(
                        admin_id,
                        f"⚠️ Bazani yuborishda xatolik: {str(e)}"
                    )
                except:
                    pass

        except Exception as e:
            logger.error(f"Background import error: {str(e)}")
            await bot.send_message(
                admin_id,
                f"❌ Import jarayonida xatolik yuz berdi:\n{str(e)}"
            )


    async def edit_user_data(self, row_id: int, type: str, value: str) -> str:
        """ Foydalanuvchi ma'lumotlarini tahrirlash """

        if type == "name":
            valid, message, formatted_name = Validators.validate_fullname(value)
            if not valid:
                return f"Invalid name: {message}"
            value = formatted_name
            await self.execute("UPDATE users SET fullname = ? WHERE id = ?", (value, row_id))

        elif type == "phone":
            valid, message, normalized_phone = Validators.validate_phone(value)
            if not valid:
                return f"Invalid phone: {message}"
            value = normalized_phone
            await self.execute("UPDATE users SET phone = ? WHERE id = ?", (value, row_id))
        elif type == "passport_number":
            valid, message, clean_passport = Validators.validate_passport_number(value)
            if not valid:
                return f"Invalid passport number: {message}"
            value = clean_passport
            await self.execute("UPDATE users SET passport_number = ? WHERE id = ?", (value, row_id))
        elif type == "birthdate":
            valid, message, birth_date, warning, expiry_date = Validators.validate_birth_date(value)
            if not valid:
                return f"Invalid birthdate: {message}"
            value = birth_date
            await self.execute("UPDATE users SET birth_date = ? WHERE id = ?", (value, row_id))
        elif type == "pinfl":
            valid, message, clean_pinfl = Validators.validate_pinfl(value)
            if not valid:
                return f"Invalid PINFL: {message}"
            value = clean_pinfl
            await self.execute("UPDATE users SET pinfl = ? WHERE id = ?", (value, row_id))
        elif type == "address":
            valid, message, clean_address = Validators.validate_address(value)
            if not valid:
                return f"Invalid address: {message}"
            value = clean_address
            await self.execute("UPDATE users SET address = ? WHERE id = ?", (value, row_id))

        return "✅ Foydalanuvchi ma'lumotlari muvaffaqiyatli yangilandi."

    async def delete_user_by_row_id(self, row_id: int) -> None:
        """ Foydalanuvchini o'chirish """
        await self.execute("DELETE FROM users WHERE id = ?", (row_id,))

    async def delete_user_by_telegram_id(self, telegram_id: int) -> None:
        """ Telegram ID bo'yicha foydalanuvchini o'chirish """
        await self.execute("DELETE FROM users WHERE telegram_id = ?", (telegram_id,))


    async def update_user_id(self, telegram_id: int, client_code: str) -> None:
        """ Foydalanuvchi ID sini yangilash """
        await self.execute("UPDATE users SET telegram_id = ? WHERE client_code = ?", (telegram_id, client_code))

    async def close(self):
        """Close all connections"""
        if self._pool:
            await self._pool.close_all()


# Global instance
data_db = AsyncDatabase(DATABASE_NAME, Path(__file__).resolve().parent)


if __name__ == "__main__":
    async def test():
        print("🔄 Initializing database...")
        await data_db.start()
        print("✅ Database initialized successfully")
        print("=" * 50)
        
        await data_db.close()
    
    asyncio.run(test())
