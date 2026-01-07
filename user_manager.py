import os
import re
import datetime
import random
import traceback
from pymongo import MongoClient
import certifi

# ============================================================================
# 🔌 MONGODB ATLAS BAĞLANTISI
# ============================================================================
# web_app.py içindeki URI ile aynısını kullanıyoruz
MONGO_URI = "mongodb+srv://ozumays:26674424140@cluster0.8ptsdi0.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

try:
    # SSL Sertifika hatasını önlemek için certifi kullanıyoruz
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = client['AstrofireDB']
    users_col = db['users']  # Tüm kullanıcı verileri burada tutulacak
    print("✅ user_manager: MongoDB Atlas bağlantısı başarılı.")
except Exception as e:
    print(f"❌ user_manager: MongoDB Bağlantı Hatası: {e}")

# ============================================================================
# 🛠️ YARDIMCI FONKSİYONLAR
# ============================================================================

def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

# --- ESKİ DİSK FONKSİYONLARI (Uyumluluk için boş bıraktık) ---
def save_archive_to_disk():
    pass  # Artık MongoDB otomatik kaydediyor, gerek yok.

def load_archive_from_disk():
    print("ℹ️ Veriler MongoDB Bulut üzerinden canlı okunuyor.")

# ============================================================================
# 📂 KLASÖR VE HARİTA YÖNETİMİ (MONGODB)
# ============================================================================

def create_new_folder(email, folder_name):
    """Kullanıcının 'saved' alanına yeni bir klasör anahtarı ekler"""
    try:
        # MongoDB'de iç içe objeye dinamik key eklemek için $set kullanıyoruz
        users_col.update_one(
            {"email": email},
            {"$set": {f"saved.{folder_name}": []}}
        )
        return True
    except Exception as e:
        print(f"Klasör oluşturma hatası: {e}")
        return False

def save_chart_to_user_data(email, chart_data, category_name="Genel"):
    """Haritayı ilgili klasöre array olarak ekler ($push)"""
    try:
        # ID kontrolü
        if 'id' not in chart_data or chart_data['id'] is None:
            chart_data['id'] = random.randint(100000, 999999)
        
        # Eğer klasör yoksa oluştur, varsa içine ekle
        users_col.update_one(
            {"email": email},
            {"$push": {f"saved.{category_name}": chart_data}}
        )
        return True
    except Exception as e:
        print(f"Harita kayıt hatası: {e}")
        return False

def delete_user_chart(email, category_name, chart_id):
    """Haritayı array içinden siler ($pull)"""
    try:
        # ID'nin integer olduğundan emin olalım
        chart_id_int = int(chart_id)
        
        result = users_col.update_one(
            {"email": email},
            {"$pull": {f"saved.{category_name}": {"id": chart_id_int}}}
        )
        
        if result.modified_count > 0:
            return True, "Silindi"
        return False, "Bulunamadı"
    except Exception as e:
        print(f"Silme hatası: {e}")
        return False, str(e)

def move_chart_to_folder(email, chart_id, current_folder, target_folder):
    """Bir klasörden alıp diğerine taşır"""
    try:
        user = users_col.find_one({"email": email})
        if not user or 'saved' not in user: return False
        
        saved = user.get('saved', {})
        source_list = saved.get(current_folder, [])
        
        # Haritayı bul
        chart_to_move = next((c for c in source_list if str(c.get('id')) == str(chart_id)), None)
        
        if chart_to_move:
            # 1. Eski yerden sil ($pull)
            users_col.update_one(
                {"email": email},
                {"$pull": {f"saved.{current_folder}": {"id": chart_to_move['id']}}}
            )
            
            # 2. Yeni yere ekle ($push)
            users_col.update_one(
                {"email": email},
                {"$push": {f"saved.{target_folder}": chart_to_move}}
            )
            return True
            
    except Exception as e:
        print(f"Taşıma hatası: {e}")
    return False

def get_user_folder_list(email):
    user = users_col.find_one({"email": email}, {"saved": 1})
    if user and 'saved' in user:
        return list(user['saved'].keys())
    return ["Genel"]

def get_user_saved_charts(email):
    user = users_col.find_one({"email": email}, {"saved": 1})
    if user and 'saved' in user:
        return user['saved']
    return {}

# ============================================================================
# 👤 KULLANICI İŞLEMLERİ (MONGODB)
# ============================================================================

def get_user_data_by_email(email):
    """Kullanıcı verisini çeker (active_charts ve saved dahil)"""
    return users_col.find_one({"email": email})

def register_user(name, email, password, phone=""):
    if not (name and email and password): return False, "Eksik bilgi."
    if not is_valid_email(email): return False, "Geçersiz e-posta."
    
    # E-posta kontrolü (MongoDB)
    if users_col.find_one({"email": email}):
        return False, "Bu e-posta zaten kayıtlı."
    
    register_date = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
    
    new_user = {
        'name': name,
        'email': email,
        'password': password,
        'phone': phone,
        'register_date': register_date,
        'active_charts': [],     # Session'daki aktif haritalar için
        'saved': {'Genel': []}   # Klasör sistemi
    }
    
    try:
        users_col.insert_one(new_user)
        return True, f"'{name}' başarıyla kaydedildi."
    except Exception as e:
        return False, f"Veritabanı hatası: {e}"

def try_login(email, password, remember_me=False):
    if not (email and password): return False, "Lütfen tüm alanları doldurun."
    
    user = users_col.find_one({"email": email})
    
    if user and user.get('password') == password:
        return True, user
    return False, "Hatalı e-posta veya şifre."

def save_user_data(email, user_data):
    """
    Kullanıcının profil, şifre veya aktif harita verilerini günceller.
    user_data içindeki alanları $set ile güncelleriz.
    """
    try:
        # _id alanını güncellemeye çalışmamak için temizle
        if '_id' in user_data:
            del user_data['_id']
            
        users_col.update_one(
            {"email": email},
            {"$set": user_data}
        )
        return True
    except Exception as e:
        print(f"Kullanıcı güncelleme hatası: {e}")
        return False

def get_all_users():
    """Admin paneli için tüm kullanıcıları listeler"""
    try:
        cursor = users_col.find({}, {"_id": 0, "saved": 0, "active_charts": 0}) # Büyük verileri çekme
        return list(cursor)
    except:
        return []

def delete_registered_user(email):
    try:
        users_col.delete_one({"email": email})
        return True
    except:
        return False
