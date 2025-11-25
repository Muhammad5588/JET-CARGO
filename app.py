import middlewares, filters, handlers
import asyncio
import logging
import sys
from loader import dp, bot
from middlewares.throttling import ThrottlingMiddleware
from middlewares.check_user import UserCheckMiddleware
from utils.notify_admins import on_startup_notify
from data.Async_sqlDataBase import data_db as db

logger = logging.getLogger(__name__)

async def main():
    """Asosiy funksiya - bot va barcha background vazifalarini boshqaradi"""
    logger.info("Bot ishga tushmoqda...")

    # Database ni initialize qilish
    logger.info("Database initialize qilinyoqda...")
    try:
        await db.start()
        logger.info("✅ Database muvaffaqiyatli initialize qilindi")
    except Exception as e:
        logger.error(f"Database initialize qilishda xato: {e}")
        raise

    # Middleware larni ro'yxatdan o'tkazish
    dp.message.middleware.register(ThrottlingMiddleware())
    dp.update.middleware.register(UserCheckMiddleware())


    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook o'chirildi")


        # Admin notifikasiyalarini yuborish
        await on_startup_notify()
        logger.info("Bot polling rejimda ishlamoqda...")

        # Asosiy polling loopini ishga tushirish
        await dp.start_polling(bot, skip_updates=True)

    except KeyboardInterrupt:
        logger.info("Bot foydalanuvchi tomonidan to'xtatildi")
    except Exception as e:
        logger.error(f"Asosiy bot xatosi: {e}", exc_info=True)
    finally:
        # Database connectionlarini yopish
        await db.close()
        logger.info("Database connectionlari yopildi")

        # Bot sessionini yopish
        await bot.session.close()
        logger.info("Bot to'xtatildi")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot foydalanuvchi tomonidan to'xtatildi")
    except SystemExit:
        logger.info("Bot tizim tomonidan to'xtatildi")
    except Exception as e:
        logger.critical(f"Jiddiy xato: {e}", exc_info=True)