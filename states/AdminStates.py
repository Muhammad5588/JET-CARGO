# ==================== STATES ====================

from aiogram.filters.state import State, StatesGroup

class AdminStates(StatesGroup):
    in_admin_panel = State()
    entering_rejection_reason = State()
    searching_user = State()
    entering_broadcast_message = State()
    uploading_database = State()
    admin_searching_trek = State()
    replying_to_feedback = State()
    bulk_importing_users = State()
    user_exel_importing_process = State()
    
    

class RegistrationStates(StatesGroup):
    entering_fullname = State()
    entering_phone = State()
    selecting_passport_type = State()
    uploading_passport_front = State()
    uploading_passport_back = State()
    uploading_passport_booklet = State()
    entering_passport_number = State()
    entering_birth_date = State()
    entering_pinfl = State()
    entering_address = State()
    confirming_registration = State()


class LoginStates(StatesGroup):
    entering_client_code = State()
    entering_phone_verify = State()


class EditUserDataStates(StatesGroup):
    editing_user_data = State()

class UserStates(StatesGroup):
    viewing_profile = State()
    entering_feedback = State()
    confirming_china_address = State()
    
    
    
class SearchStates(StatesGroup):
    selecting_search_type = State()
    searching_by_trek = State()
    viewing_my_shipments = State()
