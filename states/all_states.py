from aiogram.fsm.state import State, StatesGroup



class for_admin(StatesGroup):
    forward_msg = State()
    reklama_start = State()
    for_caption = State()
    for_btn = State()
    for_post = State()
    for_admin_plus = State()
    for_admin_message = State()
    for_channel_add = State()
    for_force_subs = State()
    get_url = State()




