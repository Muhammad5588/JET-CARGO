import time
from aiogram import BaseMiddleware, types
from aiogram.dispatcher.event.handler import HandlerObject


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, default_rate: float = 0.5) -> None:
        self.default_rate = default_rate
        self.last_throttled = 0
        self.count_throttled = 0

    async def __call__(self, handler, event: types.Update, data):
        real_handler: HandlerObject = data["handler"]
        skip_pass = real_handler.flags.get("skip_pass", True)

        if skip_pass:
            current_time = time.time()
            time_diff = current_time - self.last_throttled

            if time_diff >= self.default_rate:
                self.last_throttled = current_time
                self.count_throttled = 0
                self.default_rate = 0.5
                return await handler(event, data)
            else:
                self.count_throttled += 1
                if self.count_throttled >= 2:
                    self.default_rate = 3
                if hasattr(event, 'message') and event.message:
                    await event.message.reply(
                        "<b>So'rov ko'payib ketdi!</b>\nYana davom ettirsangiz blocklanasiz!!!"
                    )

                self.last_throttled = current_time
        else:
            return await handler(event, data)
