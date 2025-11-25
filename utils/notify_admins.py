import asyncio
import logging
from typing import List

from loader import bot

logger = logging.getLogger(__name__)


async def on_startup_notify() -> None:
    """
    Bot startup vaqtida barcha adminlarga parallel notification yuborish

    Adminlarga "Bot ishga tushdi" xabarini yuboradi
    """
    from data.config import get_admins

    admins: List[int] = await get_admins()

    if not admins:
        logger.warning("No admins found in database")
        return

    async def send_startup_notification(admin_id: int) -> bool:
        """Yagona adminga startup notification yuborish"""
        try:
            await bot.send_message(
                chat_id=admin_id,
                text="✅ Bot ishga tushdi! /start"
            )
            logger.info(f"Startup notification sent to admin {admin_id}")
            return True
        except Exception as e:
            logger.warning(f"Could not send startup notification to admin {admin_id}: {e}")
            return False

    # Send to all admins in parallel
    tasks = [send_startup_notification(admin) for admin in admins]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    successful = sum(1 for r in results if r is True)
    logger.info(f"Startup notifications sent to {successful}/{len(admins)} admins")
