"""
Validatorlar - Ma'lumotlarni tekshirish

Bu faylni utils/validators.py ga joylashtiring!
"""
from datetime import datetime
import re
from typing import Optional, Tuple

from data.config import PASSPORT_EXPIRY_WARNING_MONTHS

# Constants
VALID_PASSPORT_PREFIXES = ['AA', 'AB', 'AC', 'AD', 'AE']  # O'zbekiston
VALID_KARAKALPAK_PREFIX = 'K'  # Qoraqalpog'iston
VALID_PINFL_FIRST_DIGITS = ['3', '4', '5', '6']  # O'zbekiston fuqarolari


class Validators:
    """Ma'lumotlarni tekshirish klassi"""
    
    @staticmethod
    def validate_birth_date(date_str: str) -> Tuple[bool, str, str, Optional[str], Optional[str]]:
        """
        Tug'ilgan sanani tekshirish va pasport muddatini hisoblash
        
        Returns:
            (valid, message, formatted_date, warning, expiry_date)
        """
        # Har xil formatlarni qo'llab-quvvatlash
        patterns = [
            r'(\d{1,2})[./-](\d{1,2})[./-](\d{4})',  # dd.mm.yyyy, dd/mm/yyyy, dd-mm-yyyy
            r'(\d{4})[./-](\d{1,2})[./-](\d{1,2})',  # yyyy.mm.dd
        ]
        
        for pattern in patterns:
            match = re.search(pattern, date_str)
            if match:
                parts = match.groups()
                
                try:
                    if len(parts[0]) == 4:  # yyyy-mm-dd format
                        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
                    else:  # dd-mm-yyyy format
                        day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
                    
                    # Sana validatsiyasi
                    birth_date = datetime(year, month, day)
                    
                    # Yoshni tekshirish (18+ bo'lishi kerak)
                    today = datetime.now()
                    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                    
                    if age < 18:
                        return False, "Siz 18 yoshdan kichik bo'la olmaysiz", "", None, None
                    
                    if age > 100:
                        return False, "Tug'ilgan sana noto'g'ri", "", None, None
                    
                    formatted_date = birth_date.strftime('%d.%m.%Y')
                    
                    # Pasport muddatini hisoblash
                    expiry_date, warning = Validators._calculate_passport_expiry(birth_date, age)
                    
                    return True, "OK", formatted_date, warning, expiry_date
                
                except ValueError:
                    continue
        
        return False, (
            "Sana formati noto'g'ri!\n"
            "To'g'ri format: dd.mm.yyyy (masalan: 15.03.1990)"
        ), "", None, None
    
    @staticmethod
    def validate_phone(phone: str) -> Tuple[bool, str, str]:
        """
        Telefon raqamini tekshirish va normalize qilish
        
        Args:
            phone: Telefon raqam (998901234567, +998901234567, 901234567)
        
        Returns:
            (valid, message, normalized_phone)
            
        Examples:
            >>> Validators.validate_phone("998901234567")
            (True, "OK", "998901234567")
            
            >>> Validators.validate_phone("+998901234567")
            (True, "OK", "998901234567")
            
            >>> Validators.validate_phone("901234567")
            (True, "OK", "998901234567")
            
            >>> Validators.validate_phone("12345")
            (False, "Telefon raqam noto'g'ri formatda", "")
        """
        # Faqat raqamlarni olish
        digits = re.sub(r'\D', '', phone)
        
        if not digits:
            return False, "Telefon raqam kiritilmadi", ""
        
        # Agar 998 bilan boshlanmasa, qo'shish
        if not digits.startswith('998'):
            if len(digits) == 9:
                digits = '998' + digits
            else:
                return False, "Telefon raqam noto'g'ri formatda", ""
        
        if len(digits) != 12:
            return False, "Telefon raqam 12 ta raqamdan iborat bo'lishi kerak", ""
        
        return True, "OK", digits
    
    @staticmethod
    def _calculate_passport_expiry(birth_date: datetime, age: int) -> Tuple[Optional[str], Optional[str]]:
        """
        Pasport muddatini hisoblash
        
        O'zbekistonda pasport muddati:
        - 16 yoshgacha: Farzandlik guvohnomasi
        - 16 yoshda: Birinchi pasport (9 yil)
        - 25 yoshda: Ikkinchi pasport (20 yil)
        - 45 yoshda: Uchinchi pasport (umrbod)
        
        Returns:
            (expiry_date_str, warning)
        """
        today = datetime.now()
        
        if age < 25:
            # 16 yoshda olingan pasport 25 yoshda tugaydi
            expiry_age = 25
            expiry_date = datetime(birth_date.year + expiry_age, birth_date.month, birth_date.day)
        elif age < 45:
            # 25 yoshda olingan pasport 45 yoshda tugaydi
            expiry_age = 45
            expiry_date = datetime(birth_date.year + expiry_age, birth_date.month, birth_date.day)
        else:
            # 45 yoshdan keyin umrbod pasport
            return None, None
        
        expiry_str = expiry_date.strftime('%d.%m.%Y')
        
        # Muddati tugashiga necha oy qolganini hisoblash
        months_until_expiry = (expiry_date.year - today.year) * 12 + (expiry_date.month - today.month)
        
        warning = None
        
        if months_until_expiry < 0:
            warning = (
                "🚨 MUHIM OGOHLANTIRISH!\n\n"
                f"Pasportingiz muddati {expiry_str} da tugagan!\n"
                "Yangi pasport olishingiz SHART!\n\n"
                "Muddati tugagan pasport bilan xizmatlardan foydalana olmaysiz."
            )
        elif months_until_expiry <= PASSPORT_EXPIRY_WARNING_MONTHS:
            warning = (
                "⚠️ ESLATMA!\n\n"
                f"Pasportingiz muddati tez orada tugaydi: {expiry_str}\n"
                f"Yangi pasport olishga tayyorgarlik ko'ring.\n\n"
                f"Qolgan vaqt: {months_until_expiry} oy"
            )
        
        return expiry_str, warning

    @staticmethod
    def validate_passport_number(passport: str) -> Tuple[bool, str, str]:
        """
        Pasport raqamini tekshirish
        
        Args:
            passport: Pasport seriya raqami (AA1234567, AB1234567, KA1234567)
        
        Returns:
            (valid, message, clean_passport)
            
        Examples:
            >>> Validators.validate_passport_number("AA1234567")
            (True, "OK", "AA1234567")
            
            >>> Validators.validate_passport_number("KA1234567")
            (True, "OK", "KA1234567")
            
            >>> Validators.validate_passport_number("AB123")
            (False, "Pasport raqami 9 ta belgidan iborat bo'lishi kerak! To'g'ri format: AA1234567", "")
            
            >>> Validators.validate_passport_number("XX1234567")
            (False, "Pasport raqami noto'g'ri! ...", "")
        """
        # Bo'sh joylarni olib tashlash
        clean = passport.replace(' ', '').replace('-', '').upper()
        
        # Format: 2 harf + 7 raqam
        if len(clean) != 9:
            return False, (
                "Pasport raqami 9 ta belgidan iborat bo'lishi kerak! "
                "To'g'ri format: AA1234567"
            ), ""
        
        # Harflarni tekshirish
        letters = clean[:2]
        
        # O'zbekiston pasportlari
        if letters in VALID_PASSPORT_PREFIXES:
            pass  # Valid
        # Qoraqalpog'iston pasportlari (K bilan boshlanuvchi)
        elif letters[0] == VALID_KARAKALPAK_PREFIX and letters[1].isalpha():
            pass  # Valid
        else:
            return False, (
                f"Pasport raqami noto'g'ri! "
                f"Qabul qilinadigan: {', '.join(VALID_PASSPORT_PREFIXES)}, K* (Qoraqalpog'iston). "
                f"Siz kiritdingiz: {letters}"
            ), ""
        
        # Raqamlarni tekshirish
        numbers = clean[2:]
        if not numbers.isdigit():
            return False, "Pasport raqami oxirgi 7 belgisi raqam bo'lishi kerak", ""
        
        return True, "OK", clean
    
    @staticmethod
    def validate_pinfl(pinfl: str) -> Tuple[bool, str, str]:
        """
        PINFL ni tekshirish va nazorat raqamini tekshirish

        Args:
            pinfl: PINFL raqami (14 ta raqam)

        Returns:
            (valid, message, clean_pinfl)

        Examples:
            >>> Validators.validate_pinfl("31234567890123")
            (True, "OK", "31234567890123")

            >>> Validators.validate_pinfl("312345678901")
            (False, "PINFL 14 ta raqamdan iborat bo'lishi kerak", "")

            >>> Validators.validate_pinfl("11234567890123")
            (False, "PINFL birinchi raqami 3, 4, 5, 6 dan biri bo'lishi kerak. Siz kiritdingiz: 1", "")
        """
        # Float ko'rinishidagi PINFL-larni tekshirish (31234567890123.0 -> 31234567890123)
        pinfl_str = str(pinfl).strip()

        # Agar .0 bilan tugsa (float), olib tashlash
        if '.' in pinfl_str:
            try:
                pinfl_float = float(pinfl_str)
                pinfl_str = str(int(pinfl_float))
            except (ValueError, TypeError):
                pass

        # Faqat raqamlarni olish
        digits = re.sub(r'\D', '', pinfl_str)

        if len(digits) != 14:
            return False, "PINFL 14 ta raqamdan iborat bo'lishi kerak", ""

        # Birinchi raqam 3, 4, 5, 6 dan boshlanishi kerak
        if digits[0] not in VALID_PINFL_FIRST_DIGITS:
            return False, (
                f"PINFL birinchi raqami {', '.join(VALID_PINFL_FIRST_DIGITS)} dan biri bo'lishi kerak. "
                f"Siz kiritdingiz: {digits[0]}"
            ), ""

        # PINFL nazorat raqamini tekshirish (checksum)
        if not Validators._validate_pinfl_checksum(digits):
            return False, "PINFL nazorat raqami noto'g'ri (checksum failed)", ""

        return True, "OK", digits

    @staticmethod
    def _validate_pinfl_checksum(pinfl: str) -> bool:
        """
        PINFL nazorat raqamini tekshirish

        Args:
            pinfl: PINFL raqami (14 ta raqam)

        Returns:
            bool: Nazorat raqami to'g'ri bo'lsa True
        """
        try:
            digits = list(map(int, pinfl))
            control_digit = digits[-1]

            # Vazn koeffitsiyentlari
            weights = [7, 3, 1, 7, 3, 1, 7, 3, 1, 7, 3, 1, 7]

            # Nazorat summasi
            s = sum(d * w for d, w in zip(digits[:13], weights))

            # Nazorat raqami hisoblash
            calculated_cd = s % 10

            return calculated_cd == control_digit
        except (ValueError, IndexError, TypeError):
            return False
    
    @staticmethod
    def validate_fullname(fullname: str) -> Tuple[bool, str, str]:
        """
        Ism-familiyani tekshirish va formatlash
        
        Args:
            fullname: Ism va familiya
        
        Returns:
            (valid, message, formatted_name)
            
        Examples:
            >>> Validators.validate_fullname("sardor aliyev")
            (True, "OK", "Sardor Aliyev")
            
            >>> Validators.validate_fullname("ABC")
            (False, "Ism va familiyani to'liq kiriting (kamida 5 ta belgi)", "")
        """
        # Bo'sh joylarni tozalash
        name = ' '.join(fullname.strip().split())
        
        if len(name) < 5:
            return False, "Ism va familiyani to'liq kiriting (kamida 5 ta belgi)", ""
        
        # Har bir so'zning birinchi harfini katta qilish
        formatted = ' '.join(word.capitalize() for word in name.split())
        
        return True, "OK", formatted
    
    @staticmethod
    def validate_address(address: str) -> Tuple[bool, str, str]:
        """
        Manzilni tekshirish
        
        Args:
            address: Yashash manzili
        
        Returns:
            (valid, message, clean_address)
            
        Examples:
            >>> Validators.validate_address("Toshkent shahar")
            (True, "OK", "Toshkent shahar")
            
            >>> Validators.validate_address("ABC")
            (False, "Manzilni to'liqroq kiriting (kamida 10 ta belgi)", "")
        """
        clean = address.strip()
        
        if len(clean) < 10:
            return False, "Manzilni to'liqroq kiriting (kamida 10 ta belgi)", ""
        
        return True, "OK", clean

