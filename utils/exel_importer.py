
import pandas as pd
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class ExcelUserImporter:
    """Excel fayldan foydalanuvchilarni import qilish"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        # Validators ni import qilish
        try:
            from utils.validators import Validators
            self.validator = Validators
        except ImportError:
            logger.error("Validators import qilinmadi!")
            self.validator = None
    
    async def import_users_from_excel(self, file_path: str) -> Tuple[int, int, Optional[str]]:
        """
        Excel fayldan foydalanuvchilarni import qilish
        
        Returns:
            (success_count, failed_count, failed_file_path)
        """
        success_count = 0
        failed_count = 0
        failed_rows = []
        
        try:
            # Excel faylni o'qish
            print(f"\n{'='*60}")
            print(f"📁 Excel faylni o'qish: {file_path}")
            print(f"{'='*60}\n")
            
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path, encoding='utf-8')
            elif file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                logger.error(f"Unsupported file format: {file_path}")
                return 0, 0, None
            
            print(f"✅ Fayl o'qildi: {len(df)} ta qator topildi\n")
            
            # Kerakli ustunlarni tekshirish
            required_columns = ['code_str', 'fullname_passport', 'phone_number', 'passport_series', 
                              'birth_date', 'passport_pinfl', 'address_region']
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                error_msg = f"❌ Kerakli ustunlar topilmadi: {missing_columns}"
                print(error_msg)
                logger.error(f"Missing columns: {missing_columns}")
                return 0, len(df), None
            
            print(f"✅ Barcha kerakli ustunlar mavjud\n")
            
            # Har bir qatorni import qilish
            for index, row in df.iterrows():
                validation_errors = []
                
                # Progress ko'rsatish
                print(f"\n{'='*60}")
                print(f"📋 Qator {index + 2} ni tekshirish boshlandi...")
                print(f"{'='*60}")
                
                try:
                    # Client code ni olish (majburiy)
                    client_code = str(row.get('code_str', '')).strip().upper()
                    print(f"🔑 Client Code: {client_code}")
                    
                    if not client_code:
                        error_msg = "Client code (code_str) bo'sh bo'lmasligi kerak"
                        print(f"   ❌ XATO: {error_msg}")
                        raise ValueError(error_msg)
                    else:
                        print(f"   ✅ Client code to'g'ri")
                    
                    # Telegram ID ni olish (ixtiyoriy)
                    telegram_id = None
                    if pd.notna(row.get('telegram_id')):
                        try:
                            telegram_id = int(row.get('telegram_id'))
                            print(f"📱 Telegram ID: {telegram_id}")
                        except (ValueError, TypeError):
                            telegram_id = None
                            print(f"📱 Telegram ID: N/A (noto'g'ri format)")
                    else:
                        print(f"📱 Telegram ID: N/A (bo'sh)")
                    
                    # ==============================================
                    # VALIDATSIYA BOSHLANDI
                    # ==============================================
                    
                    print(f"\n🔍 Validatsiya boshlandi...")
                    
                    # 1. Passport seriya raqamini tekshirish
                    passport_series = str(row.get('passport_series', '')).strip()
                    print(f"\n1️⃣ Passport tekshiruvi:")
                    print(f"   Qiymat: '{passport_series}'")
                    
                    if self.validator:
                        is_valid_passport, passport_msg, clean_passport = self.validator.validate_passport_number(passport_series)
                        if not is_valid_passport:
                            error_msg = f"Passport: {passport_msg}"
                            validation_errors.append(error_msg)
                            print(f"   ❌ XATO: {passport_msg}")
                        else:
                            passport_series = clean_passport
                            print(f"   ✅ To'g'ri: {clean_passport}")
                    
                    # 2. Telefon raqamini tekshirish
                    phone_number = str(row.get('phone_number', '')).strip()
                    print(f"\n2️⃣ Telefon tekshiruvi:")
                    print(f"   Qiymat: '{phone_number}'")
                    
                    if self.validator:
                        is_valid_phone, phone_msg, clean_phone = self.validator.validate_phone(phone_number)
                        if not is_valid_phone:
                            error_msg = f"Telefon: {phone_msg}"
                            validation_errors.append(error_msg)
                            print(f"   ❌ XATO: {phone_msg}")
                        else:
                            phone_number = clean_phone
                            print(f"   ✅ To'g'ri: {clean_phone}")
                    
                    # 3. PINFL ni tekshirish
                    pinfl = str(row.get('passport_pinfl', '')).strip()
                    print(f"\n3️⃣ PINFL tekshiruvi:")
                    print(f"   Qiymat: '{pinfl}'")
                    
                    if self.validator:
                        is_valid_pinfl, pinfl_msg, clean_pinfl = self.validator.validate_pinfl(pinfl)
                        if not is_valid_pinfl:
                            error_msg = f"PINFL: {pinfl_msg}"
                            validation_errors.append(error_msg)
                            print(f"   ❌ XATO: {pinfl_msg}")
                        else:
                            pinfl = clean_pinfl
                            print(f"   ✅ To'g'ri: {clean_pinfl}")
                    
                    # 4. Ism-familiyani tekshirish (faqat bo'sh emasligini)
                    fullname = str(row.get('fullname_passport', '')).strip()
                    print(f"\n4️⃣ Ism-familiya tekshiruvi:")
                    print(f"   Qiymat: '{fullname}'")
                    
                    if not fullname:
                        error_msg = "Ism-familiya bo'sh"
                        validation_errors.append(error_msg)
                        print(f"   ❌ XATO: {error_msg}")
                    else:
                        print(f"   ✅ To'g'ri")
                    
                    # 5. Manzilni tekshirish (faqat bo'sh emasligini)
                    address = str(row.get('address_region', '')).strip()
                    print(f"\n5️⃣ Manzil tekshiruvi:")
                    print(f"   Qiymat: '{address}'")
                    
                    if not address:
                        error_msg = "Manzil bo'sh"
                        validation_errors.append(error_msg)
                        print(f"   ❌ XATO: {error_msg}")
                    else:
                        print(f"   ✅ To'g'ri")
                    
                    # 6. Tug'ilgan sanani tekshirish (faqat bo'sh emasligini)
                    birth_date = str(row.get('birth_date', '')).strip()
                    print(f"\n6️⃣ Tug'ilgan sana tekshiruvi:")
                    print(f"   Qiymat: '{birth_date}'")
                    
                    if not birth_date:
                        error_msg = "Tug'ilgan sana bo'sh"
                        validation_errors.append(error_msg)
                        print(f"   ❌ XATO: {error_msg}")
                    else:
                        print(f"   ✅ To'g'ri")
                    
                    # Agar validatsiya xatolari bo'lsa, qatorni tashlab ketish
                    if validation_errors:
                        failed_count += 1
                        print(f"\n{'='*60}")
                        print(f"❌ Qator {index + 2} validatsiyadan O'TMADI!")
                        print(f"📝 Xatoliklar soni: {len(validation_errors)}")
                        for i, err in enumerate(validation_errors, 1):
                            print(f"   {i}. {err}")
                        print(f"{'='*60}")
                        
                        failed_rows.append({
                            'row': index + 2,
                            'error_reason': ' | '.join(validation_errors),
                            'code_str': client_code,
                            'telegram_id': telegram_id if telegram_id else 'N/A',
                            'fullname_passport': fullname,
                            'phone_number': phone_number,
                            'passport_series': passport_series,
                            'birth_date': birth_date,
                            'passport_pinfl': pinfl,
                            'address_region': address,
                        })
                        logger.warning(f"Row {index + 2} validatsiyadan o'tmadi: {', '.join(validation_errors)}")
                        continue
                    
                    # ==============================================
                    # VALIDATSIYA TUGADI - Ma'lumotlarni tayyorlash
                    # ==============================================
                    
                    print(f"\n✅ Barcha validatsiyalar o'tdi!")
                    print(f"💾 Ma'lumotlarni bazaga yozishga tayyorlanmoqda...")
                    
                    user_data = {
                        'fullname': fullname,
                        'phone': phone_number,
                        'passport_number': passport_series,
                        'birth_date': birth_date,
                        'pinfl': pinfl,
                        'address': address,
                        'passport_front_file_id': str(row.get('passport_front_file_id', '')).strip() if pd.notna(row.get('passport_front_file_id')) else None,
                        'passport_back_file_id': str(row.get('passport_back_file_id', '')).strip() if pd.notna(row.get('passport_back_file_id')) else None,
                        'passport_front_file_unique_id': str(row.get('passport_front_file_unique_id', '')).strip() if pd.notna(row.get('passport_front_file_unique_id')) else None,
                        'passport_back_file_unique_id': str(row.get('passport_back_file_unique_id', '')).strip() if pd.notna(row.get('passport_back_file_unique_id')) else None,
                        'language': str(row.get('language', 'uz')).strip() if pd.notna(row.get('language')) else 'uz',
                    }
                    
                    # Client code bo'yicha allaqachon mavjudmi tekshirish
                    existing_user = await self.db.get_user_by_client_code(client_code)
                    if existing_user:
                        error_msg = 'Client code allaqachon mavjud'
                        print(f"   ❌ XATO: {error_msg}")
                        logger.warning(f"User with client code {client_code} already registered, skipping...")
                        failed_rows.append({
                            'row': index + 2,
                            'error_reason': error_msg,
                            'code_str': client_code,
                            'telegram_id': telegram_id if telegram_id else 'N/A',
                            **user_data
                        })
                        failed_count += 1
                        continue
                    
                    # Agar telegram_id mavjud bo'lsa, uni ham tekshirish
                    if telegram_id:
                        existing_telegram_user = await self.db.get_user_by_telegram_id(telegram_id)
                        if existing_telegram_user:
                            error_msg = 'Telegram ID allaqachon ro\'yxatdan o\'tgan'
                            print(f"   ❌ XATO: {error_msg}")
                            logger.warning(f"User with telegram_id {telegram_id} already registered, skipping...")
                            failed_rows.append({
                                'row': index + 2,
                                'error_reason': error_msg,
                                'code_str': client_code,
                                'telegram_id': telegram_id,
                                **user_data
                            })
                            failed_count += 1
                            continue
                    
                    # Ro'yxatdan o'tkazish
                    success, message, generated_code = await self.db.register_user_with_code(
                        client_code=client_code,
                        telegram_id=telegram_id,
                        user_data=user_data
                    )
                    
                    if success:
                        success_count += 1
                        print(f"✅ MUVAFFAQIYATLI! Qator {index + 2} bazaga qo'shildi")
                        print(f"   Client code: {client_code}")
                        print(f"   Telegram ID: {telegram_id or 'N/A'}")
                        logger.info(f"User imported: {client_code} (telegram_id: {telegram_id or 'None'})")
                    else:
                        failed_count += 1
                        print(f"❌ Bazaga yozishda xatolik: {message}")
                        failed_rows.append({
                            'row': index + 2,
                            'error_reason': message,
                            'code_str': client_code,
                            'telegram_id': telegram_id if telegram_id else 'N/A',
                            **user_data
                        })
                        logger.error(f"Failed to import user {client_code}: {message}")
                
                except Exception as e:
                    failed_count += 1
                    error_msg = f"Xatolik: {str(e)}"
                    print(f"\n{'='*60}")
                    print(f"❌ UMUMIY XATOLIK qator {index + 2} da!")
                    print(f"📝 Xatolik: {str(e)}")
                    print(f"{'='*60}")
                    
                    failed_rows.append({
                        'row': index + 2,
                        'error_reason': error_msg,
                        'code_str': row.get('code_str', 'N/A'),
                        'telegram_id': row.get('telegram_id', 'N/A'),
                        'fullname_passport': row.get('fullname_passport', ''),
                        'phone_number': row.get('phone_number', ''),
                        'passport_series': row.get('passport_series', ''),
                        'birth_date': row.get('birth_date', ''),
                        'passport_pinfl': row.get('passport_pinfl', ''),
                        'address_region': row.get('address_region', ''),
                    })
                    logger.error(f"Error importing row {index + 2}: {e}")
            
            # Import tugadi - natijalarni chiqarish
            print(f"\n{'='*60}")
            print(f"📊 IMPORT YAKUNLANDI!")
            print(f"{'='*60}")
            print(f"✅ Muvaffaqiyatli: {success_count} ta")
            print(f"❌ Xatolik: {failed_count} ta")
            print(f"📋 Jami: {len(df)} ta qator")
            print(f"{'='*60}\n")
            
            # Xatoliklar bo'lsa, Excel faylga saqlash
            failed_file_path = None
            if failed_rows:
                print(f"💾 Xatolik bo'lgan qatorlarni Excel faylga saqlash...")

                failed_df = pd.DataFrame(failed_rows)

                # Ustunlarni kerakli tartibda joylashtirish
                preferred_order = [
                    'row',
                    'error_reason',
                    'code_str',
                    'fullname_passport',
                    'passport_pinfl',
                    'phone_number',
                    'passport_series',
                    'birth_date',
                    'address_region',
                    'telegram_id'
                ]

                # Faqat mavjud ustunlarni olish
                cols = [col for col in preferred_order if col in failed_df.columns]
                # Qolgan ustunlarni qo'shish
                for col in failed_df.columns:
                    if col not in cols:
                        cols.append(col)

                failed_df = failed_df[cols]

                # Fayl nomini to'g'ri o'zgartirivchi qism
                if file_path.endswith('.csv'):
                    failed_file_path = file_path.replace('.csv', '_failed.csv')
                elif file_path.endswith('.xlsx'):
                    failed_file_path = file_path.replace('.xlsx', '_failed.xlsx')
                elif file_path.endswith('.xls'):
                    failed_file_path = file_path.replace('.xls', '_failed.xlsx')
                else:
                    failed_file_path = file_path + '_failed.xlsx'

                if failed_file_path.endswith('.csv'):
                    failed_df.to_csv(failed_file_path, index=False, encoding='utf-8')
                else:
                    failed_df.to_excel(failed_file_path, index=False)

                print(f"✅ Failed fayl saqlandi: {failed_file_path}")
                print(f"   📊 Xatolik bo'lgan qatorlar: {len(failed_rows)}")
                logger.info(f"Failed rows saved to: {failed_file_path}")
            else:
                print(f"✅ Barcha qatorlar muvaffaqiyatli import qilindi!")
            
            return success_count, failed_count, failed_file_path
        
        except Exception as e:
            logger.error(f"Excel import error: {e}")
            print(f"\n❌ UMUMIY XATOLIK: {str(e)}")
            return success_count, failed_count, None