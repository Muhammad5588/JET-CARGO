import random
import string

def generate_unique_code(length=12, prefix='UMTS-'):
    characters = string.ascii_letters + string.digits
    code = ''.join(random.choices(characters, k=length))
    return f"{prefix}{code}"

