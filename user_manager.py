# user_manager.py (DÜZELTİLMİŞ VERSİYON)
import json
import os
import traceback 
import datetime 
import re # Email kontrolü için
import random

# --- Numpy Kontrolü ---
try:
    import numpy as np
except ImportError:
    np = None 

# --- Sabitler ---
USER_REGISTRY_FILE = "users.json"
USER_ARCHIVE_FILE = "user_archive.json"
SESSION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flask_session', 'session_data.json')

# Global Veri Depoları
REGISTERED_USERS = {}
USER_DATA_STORE = {}

# --- YARDIMCI FONKSİYONLAR (Bağımsız çalışması için buraya alındı) ---
def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

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

# --- Disk İşlemleri ---

def save_archive_to_disk():
    try:
        with open(USER_REGISTRY_FILE, 'w', encoding='utf-8') as f:
            json.dump(REGISTERED_USERS, f, ensure_ascii=False, indent=4)
            
        with open(USER_ARCHIVE_FILE, 'w', encoding='utf-8') as f:
            json.dump(USER_DATA_STORE, f, ensure_ascii=False, indent=4, cls=NumpyJSONEncoder)
    except Exception as e:
        print(f"KRİTİK HATA: Arşiv kaydedilirken hata: {e}")

def load_archive_from_disk():
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
        REGISTERED_USERS = {}
        USER_DATA_STORE = {}

# --- KLASÖR YÖNETİMİ ---

def create_new_folder(email, folder_name):
    if email in USER_DATA_STORE:
        if 'saved' not in USER_DATA_STORE[email]:
            USER_DATA_STORE[email]['saved'] = {}
        
        if folder_name not in USER_DATA_STORE[email]['saved']:
            USER_DATA_STORE[email]['saved'][folder_name] = []
            save_archive_to_disk()
            return True
    return False

def move_chart_to_folder(email, chart_id, current_folder, target_folder):
    if email in USER_DATA_STORE and 'saved' in USER_DATA_STORE[email]:
        saved = USER_DATA_STORE[email]['saved']
        
        if current_folder in saved and target_folder in saved:
            chart_to_move = None
            chart_index = -1
            
            for i, chart in enumerate(saved[current_folder]):
                if str(chart.get('id')) == str(chart_id):
                    chart_to_move = chart
                    chart_index = i
                    break
            
            if chart_to_move:
                saved[current_folder].pop(chart_index)
                saved[target_folder].insert(0, chart_to_move)
                save_archive_to_disk()
                return True
    return False

def get_user_folder_list(email):
    if email in USER_DATA_STORE and 'saved' in USER_DATA_STORE[email]:
        return list(USER_DATA_STORE[email]['saved'].keys())
    return ["Genel"]

# --- KULLANICI & OTURUM İŞLEMLERİ ---

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

# DÜZELTME 1: try_login artık 'remember_me' zorunlu değil (Varsayılan False)
def try_login(email, password, remember_me=False):
    user_data = get_user_data_by_email(email)
    if not (email and password): return False, "Lütfen tüm alanları doldurun."
    
    if user_data and user_data.get('password') == password:
        return True, user_data
    return False, "Hatalı e-posta veya şifre."

# DÜZELTME 2: Fonksiyon adı 'register_user' yapıldı ve 'phone' opsiyonel oldu
def register_user(name, email, password, phone=""):
    if not (name and email and password): return False, "Eksik bilgi."
    if email in REGISTERED_USERS: return False, "Bu e-posta zaten kayıtlı."
    if not is_valid_email(email): return False, "Geçersiz e-posta."
    
    register_date = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
    
    # Kullanıcıyı kaydet
    REGISTERED_USERS[email] = {
        'name': name, 
        'password': password, 
        'phone': phone, 
        'email': email, 
        'register_date': register_date
    }
    
    # Veri deposunu başlat
    USER_DATA_STORE[email] = {'active': [], 'saved': {'Genel': []}}
    
    save_archive_to_disk()
    return True, f"'{name}' başarıyla kaydedildi."

def save_chart_to_user_data(email, chart_data, category_name="Genel"):
    if email not in USER_DATA_STORE:
        USER_DATA_STORE[email] = {'active': [], 'saved': {'Genel': []}}

    user_archive = USER_DATA_STORE[email]['saved']

    if category_name not in user_archive:
        user_archive[category_name] = []
    
    if 'id' not in chart_data or chart_data['id'] is None:
        chart_data['id'] = random.randint(100000, 999999)
    
    user_archive[category_name].append(chart_data)
    save_archive_to_disk()
    return True

def get_user_saved_charts(email):
    if email in USER_DATA_STORE:
        return USER_DATA_STORE[email].get('saved', {})
    return {}

# DÜZELTME 3: Fonksiyon adı web_app.py ile uyumlu hale getirildi
def delete_user_chart(email, category_name, chart_id):
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

# --- Yükleme İşlemi ---
load_archive_from_disk()

# Demo Kullanıcı (İstersen kaldırabilirsin)
if "demo@astro.com" not in REGISTERED_USERS:
    register_user("Demo Kullanıcı", "demo@astro.com", "demo", "5550000000")
