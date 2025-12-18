# yardimcilar.py (GÜNCEL TAM HALİ)

import math
import re # E-posta ve telefon doğrulaması için eklendi
import json # SESSION_FILE için eklendi

# --- user_manager.py'nin İHTİYAÇ DUYDUKLARI ---
SESSION_FILE = "session_data.json" 

def is_valid_email(email):
    """Basit bir e-posta formatı doğrulaması yapar."""
    if not email:
        return False
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None

def is_valid_phone(phone):
    """Basit bir telefon numarası doğrulaması (en az 10 rakam)."""
    if not phone:
        return True # Telefon opsiyonel olabilir, boş geçilebilir
    digits = re.sub(r'\D', '', phone)
    return len(digits) >= 10
# --- BLOK SONU ---


# --- astro_core.py'nin İHTİYAÇ DUYDUKLARI ---
def decimal_to_dms_string(dec_degree):
    """
    Ondalık dereceyi (örn: 84.68) Derece° Dakika' (örn: 24° 41') 
    formatına çevirir.
    """
    try:
        degrees = int(dec_degree)
        minutes_float = (dec_degree - degrees) * 60
        minutes = int(minutes_float)
        
        return f"{degrees}° {minutes:02d}'"
    
    except Exception as e:
        print(f"HATA: decimal_to_dms_string: {e}")
        return "0° 00'"

def convert_bc_to_swe_year(year):
    """M.Ö. (BC) yılları Swiss Ephemeris'in anladığı formata çevirir."""
    if year < 1:
        return year - 1
    return year
# --- BLOK SONU ---