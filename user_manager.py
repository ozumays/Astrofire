# user_manager.py (GÜNCEL TAM HALİ - Klasör Yönetimi Destekli)
import json
import os
import traceback 
import datetime 
from yardimcilar import is_valid_email, is_valid_phone, SESSION_FILE

# --- Numpy Kontrolü ---
try:
    import numpy as np
except ImportError:
    print("--- USER_MANAGER UYARI: 'numpy' BULUNAMADI! Arşiv kaydı başarısız olabilir. ---")
    np = None 

# --- Arşiv Dosyaları ---
USER_REGISTRY_FILE = "users.json"
USER_ARCHIVE_FILE = "user_archive.json"

# Global Veri Depoları
REGISTERED_USERS = {}
USER_DATA_STORE = {}

# --- Numpy Encoder ---
class NumpyJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if np and isinstance(obj, (np.integer, np.int_)):
            return int(obj)
        if np and isinstance(obj, (np.floating, np.float_)):
            return float(obj)
        if np and isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyJSONEncoder, self).default(obj)

# --- YENİ: Disk İşlemleri (Yükleme/Kaydetme) ---

def save_archive_to_disk():
    """Kullanıcı ve arşiv verilerini diske kaydeder."""
    try:
        with open(USER_REGISTRY_FILE, 'w', encoding='utf-8') as f:
            json.dump(REGISTERED_USERS, f, ensure_ascii=False, indent=4)
            
        with open(USER_ARCHIVE_FILE, 'w', encoding='utf-8') as f:
            json.dump(USER_DATA_STORE, f, ensure_ascii=False, indent=4, cls=NumpyJSONEncoder)
        
    except Exception as e:
        print(f"KRİTİK HATA: Arşiv kaydedilirken hata oluştu: {e}")
        traceback.print_exc()

def load_archive_from_disk():
    """Uygulama başlarken verileri yükler."""
    global REGISTERED_USERS, USER_DATA_STORE
    try:
        if os.path.exists(USER_REGISTRY_FILE):
            with open(USER_REGISTRY_FILE, 'r', encoding='utf-8') as f:
                REGISTERED_USERS = json.load(f)
        
        if os.path.exists(USER_ARCHIVE_FILE):
            with open(USER_ARCHIVE_FILE, 'r', encoding='utf-8') as f:
                USER_DATA_STORE = json.load(f)
        
        print(f"DEBUG: Arşiv yüklendi ({len(REGISTERED_USERS)} kullanıcı).")
        
    except Exception as e:
        print(f"KRİTİK HATA: Arşiv okunurken hata: {e}")
        traceback.print_exc()
        REGISTERED_USERS = {}
        USER_DATA_STORE = {}

# --- KLASÖR YÖNETİMİ (YENİ EKLENEN KISIM) ---

def create_new_folder(email, folder_name):
    """Kullanıcı için yeni bir klasör oluşturur."""
    if email in USER_DATA_STORE:
        if 'saved' not in USER_DATA_STORE[email]:
            USER_DATA_STORE[email]['saved'] = {}
        
        # Klasör zaten yoksa oluştur
        if folder_name not in USER_DATA_STORE[email]['saved']:
            USER_DATA_STORE[email]['saved'][folder_name] = []
            save_archive_to_disk()
            return True
    return False

def move_chart_to_folder(email, chart_id, current_folder, target_folder):
    """Haritayı bir klasörden diğerine taşır."""
    if email in USER_DATA_STORE and 'saved' in USER_DATA_STORE[email]:
        saved = USER_DATA_STORE[email]['saved']
        
        if current_folder in saved and target_folder in saved:
            chart_to_move = None
            chart_index = -1
            
            # Haritayı bul
            for i, chart in enumerate(saved[current_folder]):
                if str(chart.get('id')) == str(chart_id):
                    chart_to_move = chart
                    chart_index = i
                    break
            
            if chart_to_move:
                # Eskisinden sil
                saved[current_folder].pop(chart_index)
                # Yenisine ekle
                saved[target_folder].insert(0, chart_to_move)
                save_archive_to_disk()
                return True
    return False

def get_user_folder_list(email):
    """Kullanıcının klasör isimlerini liste olarak döner."""
    if email in USER_DATA_STORE and 'saved' in USER_DATA_STORE[email]:
        return list(USER_DATA_STORE[email]['saved'].keys())
    return ["Genel"]

# --- KULLANICI & OTURUM İŞLEMLERİ ---

def save_session_data(email, remember_me):
    data = {'logged_in_email': email if remember_me else None}
    try:
        with open(SESSION_FILE, 'w') as f: json.dump(data, f)
    except: pass

def load_session_data():
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, 'r') as f: return json.load(f).get('logged_in_email')
        except: return None
    return None

def get_user_data_by_email(email):
    return REGISTERED_USERS.get(email)

def get_all_users():
    user_list = []
    for email, info in REGISTERED_USERS.items():
        user_list.append({
            'email': email,
            'name': info.get('name', 'İsimsiz'),
            'phone': info.get('phone', '-'),
            'register_date': info.get('register_date', datetime.datetime.now().strftime("%d.%m.%Y"))
        })
    return user_list

def try_login(email, password, remember_me):
    user_data = get_user_data_by_email(email)
    if not (email and password): return False, "Lütfen tüm alanları doldurun."
    if user_data and user_data['password'] == password:
        save_session_data(email, remember_me)
        return True, user_data
    return False, "Hatalı e-posta veya şifre."

def try_register(name, email, phone, password):
    if not (name and email and phone and password): return False, "Eksik bilgi."
    if email in REGISTERED_USERS: return False, "Bu e-posta zaten kayıtlı."
    if not is_valid_email(email): return False, "Geçersiz e-posta."
    
    register_date = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
    REGISTERED_USERS[email] = {'name': name, 'password': password, 'phone': phone, 'email': email, 'register_date': register_date}
    
    # Kullanıcı veri deposunu başlat (Varsayılan Genel klasörü)
    USER_DATA_STORE[email] = {'active': [], 'saved': {'Genel': []}}
    
    save_archive_to_disk()
    return True, f"'{name}' başarıyla kaydedildi."

def logout_user():
    save_session_data(None, False)

def save_chart_to_user_data(email, chart_data, category_name="Genel"):
    if email not in USER_DATA_STORE:
        USER_DATA_STORE[email] = {'active': [], 'saved': {'Genel': []}}

    user_archive = USER_DATA_STORE[email]['saved']

    if category_name not in user_archive:
        user_archive[category_name] = []
    
    if 'id' not in chart_data or chart_data['id'] is None:
        import random
        chart_data['id'] = random.randint(100000, 999999) # Basit ID üretimi
    
    user_archive[category_name].append(chart_data)
    save_archive_to_disk()
    return True

def get_user_saved_charts(email):
    if email in USER_DATA_STORE:
        return USER_DATA_STORE[email].get('saved', {})
    return {}

def delete_chart_from_archive(email, category_name, chart_id):
    if email in USER_DATA_STORE:
        saved = USER_DATA_STORE[email].get('saved', {})
        if category_name in saved:
            for chart in saved[category_name]:
                if str(chart.get('id')) == str(chart_id):
                    saved[category_name].remove(chart)
                    save_archive_to_disk()
                    return True, "Silindi"
    return False, "Bulunamadı"

def delete_registered_user(email):
    if email in REGISTERED_USERS:
        del REGISTERED_USERS[email]
        if email in USER_DATA_STORE: del USER_DATA_STORE[email]
        save_archive_to_disk()
        return True
    return False

# --- Yükle ve Demo Kullanıcı Oluştur ---
load_archive_from_disk()
if "demo@astro.com" not in REGISTERED_USERS:
    try_register("Emre Karahan", "demo@astro.com", "5551234567", "demo")