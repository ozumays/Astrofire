# yardimcilar.py (GÜNCEL TAM HALİ)

import math
import json # SESSION_FILE için eklendi

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
