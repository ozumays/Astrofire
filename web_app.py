from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
from flask_session import Session 
import os 
import json
from datetime import datetime, timedelta, date # En sağlam yöntem budur.
import traceback 
import random 
import math
import re        
import csv       
import io        
from werkzeug.utils import secure_filename
from dateutil import tz
from dateutil.relativedelta import relativedelta
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz
import swisseph as swe 

# Kendi modüllerin
from astro_core import ASTRO_MOTOR_NESNESİ, get_relative_degree

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')
app.jinja_env.add_extension('jinja2.ext.do')

# ============================================================================
# 🌍 SWISS EPHEMERIS YOL AYARI (GLOBAL VE GARANTİ)
# ============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EPHE_FOLDER = os.path.join(BASE_DIR, 'ephe')
EPHE_PATH = EPHE_FOLDER
combined_path = f"{EPHE_FOLDER}:{BASE_DIR}" # Hem klasöre hem ana dizine bak
swe.set_ephe_path(combined_path)

# ============================================================================
# ❓ ANALİZ SORULARI (SABİT LİSTE)
# ============================================================================
ANALIZ_SORULARI = [
    "1. Ev: Kişinin mizacı nasıl? | Hayata nasıl bakıyor? | Kaderi zor mu, kolay mı? | Hayatla nasıl mücadele ediyor? | Kendini nasıl gösteriyor? | İlk izlenim enerjisi ne?",
    "2. Ev: Kişinin çocukluk yılları mı, gençlik yılları mı daha kolay? | Yaş aldıkça gündemleri, zorlukları ve kolaylıkları neler? | Hayatında dönüm noktası var mı? | Hayatta kalmak için nasıl para kazanıyor? | Paraya nasıl bakıyor? | Ne ile para kazanıyor? | Yetenekleri neler? | Maddi anlamda neleri tekrar ediyor, nerede tıkanıyor?",
    "3. Ev: Kişinin yaşlılığa doğru hayatı nasıl ilerliyor? | Hayatında ne değişti? | Zihinsel anlamda yetenekleri neler? | Nasıl düşünüyor ve bu düşünceler hayatını nasıl değiştirdi? | Düşünceleri ile eylemleri çelişiyor mu? | Kendini nasıl anlatıyor? | Yakın çevre ilişkileri önemli mi? | İlk okul hayatı nasıldı? | Yaşadığı önemli bir olay var mı?",
    "4. Ev: Ailenin bu dünyadaki yeri ne? | Ailesine ait hissediyor mu? | Taşınma, göç, yer değiştirme gibi durumlar var mı? | Evlatlık olma veya aileden kopma hikâyesi var mı? | Aileden ayrılma ne zaman ve nasıl oldu? | Annesi ile eylemsel ilişkisi nasıl? | Aile karması var mı? | Ailede tekrar eden bir kader döngüsü var mı?",
    "5. Ev: Anne zamanla nasıl birine dönüştü? | Anne ile ilişkisi nasıl devam etti? | Annesi ne zaman vefat etti? | Kişi isteklerini gerçekleştirebiliyor mu? | Cinsel hayatında tek eşli mi? | Cinselliğe dair engelleri var mı? | Çocuğu var mı? | Çocuklarda gecikme, kayıp veya zorluk var mı? | Çocuğuyla ilişkisi nasıl?",
    "6. Ev: Kişi düzen kurabiliyor mu? | Günlük rutini nasıl? | Sağlıksal bir problemi var mı? | Stresli bir yapıya sahip mi? | Çalışma hayatı nasıl ilerliyor? | İş arkadaşlarıyla arası nasıl? | Problem yaşadığı biri veya birileri var mı? | Evcil hayvanı var mı? | Evcil hayvanıyla yaşadığı önemli bir olay var mı?",
    "7. Ev: Birebir ilişkilerde en çok nerede takılıyor? | İkili ilişkilerde tekrara düştüğü bir konu var mı? | Partnerleri nasıl biri? | Ortaklığı veya iş birliği var mı? | Kaç evlilik yapmış? | İlk evliliği nasıldı? | Boşanma var mı? | Mahkemeleri var mı? | Varsa konusu ne? | Bu süreçleri kazanmış mı?",
    "8. Ev: Çocuklukta veya yetişkinlikte yaşadığı küçük/büyük travma var mı? | Kaza, doğal afet, savaş gibi kadersel olaylar yaşadı mı? | Bu olaylar onu nasıl etkiledi? | Fetişizmi var mı? | Skandal, iftira, dedikodu gibi dışlanma durumları yaşadı mı? | Suça karışmış mı? | Bağımlılıkları var mı? | Karanlık yönü ne?",
    "9. Ev: İnançlı biri mi? | Ahlak ve adalet anlayışı nasıl? | Üniversite/yüksek eğitim almış mı? | Büyük kamu davaları veya hukuk süreçleri var mı? | Seyahat eden biri mi? | Kendini geliştirmeye açık mı? | Uzak kültürler, yabancı ülkeler kişiyi nasıl etkiledi?",
    "10. Ev: Babasıyla eylemsel ilişkisi nasıl? | Saygın biri mi? Kendini saygın hissediyor mu? | Toplum önünde nasıl tanınıyor? | Bir kariyeri var mı? | Kariyer süreci nasıl işliyor? | Mesleği ne? | Mesleğini kendi mi seçti? | Başarıyı nasıl tanımlıyor?",
    "11. Ev: Baba ile ilişkisi zaman içinde nasıl devam etti? | Babası ne zaman vefat etti? | Hedeflerini gerçekleştirdi mi? | Gerçekleştiremediği hedefleri var mı? | Geleceğe nasıl baktı? | Arkadaş grupları var mıydı? | Gruplarla ilişkisi nasıldı? | Bulunduğu zamanın hızına yetişebildi mi? (Teknoloji, devrimler, yenilikler, fikir akımları…)",
    "12. Ev: Kişinin açığa çıkarmadığı gizli yetenekleri ne? | Kendinde kontrol edemediği bir negatif özellik veya yetenek var mı? | Rüya görüyor mu? | Uyku bozuklukları var mı? | Kadersel bir engeli olduğunu hiç düşünmüş mü? | Gizli düşmanları var mı? | Bilinçaltında çözülmemiş hangi konular var?"
]

# ============================================================================
# 🔢 SABİTLER
# ============================================================================
SECONDS_IN_YEAR = 365.242199 * 24 * 3600  # Bir tropik yıldaki saniye sayısı

# ============================================================================
# 🚀 EPHEMERIS KONTROLÜ
# ============================================================================
has_sepl = os.path.exists(os.path.join(EPHE_FOLDER, 'sepl_18.se1'))
has_semo = os.path.exists(os.path.join(EPHE_FOLDER, 'semo_18.se1'))

if has_sepl and has_semo:
    print(f"✅ Ephemeris Dosyaları Bulundu: {EPHE_FOLDER}")
    CALC_MODE = swe.FLG_SWIEPH | swe.FLG_SPEED 
else:
    print(f"⚠️ Ephemeris Dosyaları Eksik. Moshier moduna geçiliyor.")
    CALC_MODE = swe.FLG_MOSEPH 

# ============================================================================
# 🚀 SESSION VE DOSYA AYARLARI
# ============================================================================
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flask_session')
Session(app)

UPLOAD_FOLDER_COURSES = os.path.join(BASE_DIR, 'static', 'uploads', 'courses')
UPLOAD_FOLDER_CONTACT = os.path.join(BASE_DIR, 'static', 'uploads', 'contact')
UPLOAD_FOLDER_CHARTS = os.path.join(BASE_DIR, 'static', 'uploads', 'charts')

app.config['UPLOAD_FOLDER_COURSES'] = UPLOAD_FOLDER_COURSES
app.config['UPLOAD_FOLDER_CONTACT'] = UPLOAD_FOLDER_CONTACT
app.config['UPLOAD_FOLDER_CHARTS'] = UPLOAD_FOLDER_CHARTS

os.makedirs(UPLOAD_FOLDER_COURSES, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_CONTACT, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_CHARTS, exist_ok=True)

# ============================================================================
# 🔐 YÖNETİCİ AYARLARI
# ============================================================================
ADMIN_EMAILS = ["astrozumaay@hotmail.com"] 
ADMIN_PASSWORD = "123" 

DATA_FILE = 'data_public_charts.json'        
COURSES_FILE = 'data_courses.json'
CONSULTATIONS_FILE = 'data_consultations.json'
CONTACT_FILE = 'data_contact.json'
SUPPORT_LINKS_FILE = 'support_links.json'

# --- YARDIMCI FONKSİYONLAR (GÜVENLİ VERSİYON) ---
def load_json_data(filename):
    if not os.path.exists(filename): return {} if filename == CONTACT_FILE else []
    try: 
        with open(filename, 'r', encoding='utf-8') as f: return json.load(f)
    except: return {} if filename == CONTACT_FILE else []

def save_json_data(filename, data):
    try:
        with open(filename, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=4)
    except: pass


# ============================================================================
# 🛡️ GÜVENLİ CONTEXT YÜKLEYİCİ (KULLANICI GİRİŞİ KALDIRILDI)
# ============================================================================
def get_common_context():
    # --- CHART_TYPE MANTIĞI ---
    current_chart = session.get('current_chart_data')
    if current_chart and isinstance(current_chart, dict):
        chart_type = current_chart.get('type', 'natal')
    else:
        chart_type = 'natal'
    
    # Destek linklerini yükle
    support_links = load_json_data(SUPPORT_LINKS_FILE)

    return {
        'user_email': None, 
        'is_logged_in': False,
        'display_name': 'Kullanıcı',
        'user_profile_image': None,
        'user_phone': '',
        'chart_type': chart_type,
        'motor': ASTRO_MOTOR_NESNESİ,
        'active_charts': session.get('active_charts', []),
        'current_chart_data': session.get('current_chart_data'),
        'user_folders': [],
        'support_links': support_links,
        'is_admin': lambda: False,
        'analiz_sorulari': ANALIZ_SORULARI
    }


# ============================================================================
# 🔮 TRANSİT TAHMİN MOTORU (DÜZELTİLMİŞ)
# ============================================================================
def get_transit_predictions(chart_date, current_planets, motor_instance):
    """
    Hızlı gezegenlerin gelecekte ne zaman tam kavuşum yapacağını hesaplar.
    Düzeltme: Ay için tolerans artırıldı.
    """
    if not current_planets or not chart_date: return []

    fast_movers = ['Ay', 'Merkür', 'Venüs', 'Güneş', 'Mars']
    predictions = []
    
    # 1. HIZLI GEZEGENLERİ DÖNGÜYE AL
    for mover_name in fast_movers:
        if mover_name not in current_planets: continue
        
        # 2. HEDEF GEZEGENLERİ DÖNGÜYE AL
        for target_name, target_data in current_planets.items():
            if mover_name == target_name: continue
            
            target_abs_deg = float(target_data[0])
            target_sign_str, target_deg_val, _ = get_relative_degree(target_abs_deg, 'Astronomik')

            # 3. SİMÜLASYON AYARLARI
            max_days = 180  
            step_days = 1   
            
            # Ay için özel ayar
            tolerance = 1.5
            if mover_name == 'Ay': 
                max_days = 30 
                tolerance = 10.0 # Ay günde 13 derece gider, 1.5 az kalır.
            
            found_date = None
            is_retro_trap = False 
            
            # Simülasyon Döngüsü (Geleceği Tara)
            temp_date = chart_date
            
            for i in range(1, max_days):
                temp_date += timedelta(days=step_days)
                
                try:
                    # Sadece 12:00 UTC için hesapla
                    _, daily_data = motor_instance.calculate_chart_data(
                        temp_date.year, temp_date.month, temp_date.day, 
                        12, 0, 0.0, 0.0, 0.0, None, 'P', 'Astronomik'
                    )
                except: continue
                
                if not daily_data or mover_name not in daily_data['planets']: continue

                mover_future_pos = float(daily_data['planets'][mover_name][0])
                mover_speed = float(daily_data['planets'][mover_name][2]) 
                
                diff = abs(mover_future_pos - target_abs_deg)
                if diff > 180: diff = 360 - diff
                
                if diff < tolerance: 
                    found_date = i 
                    if mover_speed < 0: is_retro_trap = True
                    break
            
            if found_date:
                predictions.append({
                    'mover': mover_name,
                    'target': target_name,
                    'target_sign': target_sign_str, 
                    'target_deg': target_deg_val,   
                    'days_later': found_date,
                    'is_retro': is_retro_trap
                })

    return predictions

@app.context_processor
def inject_utility_functions():
    return dict(get_relative_degree=get_relative_degree, is_admin=lambda: session.get('logged_in_email') in ADMIN_EMAILS)

# ============================================================================
# 🌙 GÖKYÜZÜ OLAYLARI
# ============================================================================
def find_annual_celestial_events(year):
    eclipses = []
    phases = []
    jd_start = swe.julday(year, 1, 1)
    jd_end = swe.julday(year + 1, 1, 1)
    current_jd = jd_start
     
    def get_phase_angle(t):
        try:
            res_s = swe.calc_ut(t, swe.SUN, CALC_MODE)
            res_m = swe.calc_ut(t, swe.MOON, CALC_MODE)
            if not isinstance(res_s, tuple) or not isinstance(res_m, tuple): return 0.0
            diff = (res_m[0][0] - res_s[0][0]) % 360.0
            return diff
        except: return 0.0

    while current_jd < jd_end:
        angle1 = get_phase_angle(current_jd)
        next_day_jd = current_jd + 1.0
        angle2 = get_phase_angle(next_day_jd)
         
        found_type = None
        if angle1 > 300 and angle2 < 60: found_type = "new"
        elif angle1 < 180 and angle2 >= 180: found_type = "full"
            
        if found_type:
            t_low = current_jd; t_high = next_day_jd
            for _ in range(15):
                t_mid = (t_low + t_high) / 2.0
                a_mid = get_phase_angle(t_mid)
                if found_type == "new":
                    if a_mid > 180: t_low = t_mid
                    else: t_high = t_mid
                else:
                    if a_mid < 180: t_low = t_mid
                    else: t_high = t_mid
            
            exact_jd = t_high
            y, m, d, h_dec = swe.revjul(exact_jd)
            h = int(h_dec); mn = int((h_dec - h) * 60)
            
            target = swe.SUN if found_type == "new" else swe.MOON
            try:
                res_pos = swe.calc_ut(exact_jd, target, CALC_MODE)
                if isinstance(res_pos, tuple):
                      pos = res_pos[0]
                      sign, deg, _ = get_relative_degree(pos[0], 'Astronomik')
                else:
                      sign, deg = "Bilinmeyen", 0
            except: sign, deg = "Bilinmeyen", 0
            
            is_eclipse = False; eclipse_name = ""
            try:
                search_start_jd = exact_jd - 1.0 
                if found_type == "new":
                    ecl_flag = swe.FLG_MOSEPH_ECL_ALL if CALC_MODE == swe.FLG_MOSEPH else 0
                    ecl = swe.sol_eclipse_when_glob(search_start_jd, ecl_flag) 
                    if isinstance(ecl, tuple) and (ecl[0] & swe.ECL_ALLTYPES_SOLAR):
                        if abs(ecl[1][0] - exact_jd) < 2.0:
                            is_eclipse = True
                            if ecl[0] & swe.ECL_TOTAL: eclipse_name = "Tam Güneş Tutulması"
                            elif ecl[0] & swe.ECL_ANNULAR: eclipse_name = "Halkalı G. Tutulması"
                            elif ecl[0] & swe.ECL_HYBRID: eclipse_name = "Hibrit G. Tutulması"
                            else: eclipse_name = "Parçalı G. Tutulması"
                else:
                    ecl_flag = swe.FLG_MOSEPH_ECL_ALL if CALC_MODE == swe.FLG_MOSEPH else 0
                    ecl = swe.lun_eclipse_when(search_start_jd, ecl_flag)
                    if isinstance(ecl, tuple) and (ecl[0] & swe.ECL_ALLTYPES_LUNAR):
                        if abs(ecl[1][0] - exact_jd) < 2.0:
                            is_eclipse = True
                            if ecl[0] & swe.ECL_TOTAL: eclipse_name = "Tam Ay Tutulması"
                            elif ecl[0] & swe.ECL_PENUMBRAL: eclipse_name = "Gölgeli Ay Tutulması"
                            else: eclipse_name = "Parçalı Ay Tutulması"
            except: pass
            
            event_data = {
                'title': eclipse_name if is_eclipse else ("Yeni Ay" if found_type=="new" else "Dolunay"),
                'sign_info': f"{sign} {int(deg)}°",
                'date_str': f"{d:02d}.{m:02d}.{y} {h:02d}:{mn:02d}",
                'year': y, 'month': m, 'day': d, 'hour': h, 'minute': mn
            }
            if is_eclipse: eclipses.append(event_data)
            else: phases.append(event_data)
            current_jd += 14; continue

        current_jd += 1.0
    return {'eclipses': eclipses, 'phases': phases}

# ============================================================================
# 🔐 YÖNETİCİ PANELİ ROTALARI
# ============================================================================

@app.route('/yonetim', methods=['GET', 'POST'])
def admin_login_page():
    """Admin giriş sayfası ve Giriş Kontrolü"""
    # Zaten giriş yapmışsa direkt panele at
    if session.get('admin_access'):
        return redirect(url_for('admin_dashboard'))
        
    # Kullanıcı form doldurup 'Giriş' butonuna bastıysa:
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if email in ADMIN_EMAILS and password == ADMIN_PASSWORD:
            session['admin_access'] = True
            session['logged_in_email'] = email
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error='Yanlış e-posta veya şifre!')
            
    # Sadece sayfayı açmak istediyse (GET):
    return render_template('admin_login.html')

@app.route('/yonetim/panel')
def admin_dashboard():
    """Admin dashboard"""
    if not session.get('admin_access'):
        return redirect(url_for('admin_login_page'))
    
    context = {
        'public_charts': load_json_data(DATA_FILE),
        'courses': load_json_data(COURSES_FILE),
        'contact': load_json_data(CONTACT_FILE),
        'users': []  # Kullanıcı sistemi kaldırıldı
    }
    return render_template('admin_dashboard.html', **context)

@app.route('/admin_logout')
def admin_logout():
    """Admin çıkışı"""
    session.pop('admin_access', None)
    session.pop('logged_in_email', None)
    return redirect(url_for('home'))

# ============================================================================
# 🗑️ SİLME ROTALARı
# ============================================================================

@app.route('/admin/delete_chart/<int:chart_id>')
def admin_delete_chart(chart_id):
    """Harita silme"""
    if not session.get('admin_access'):
        return redirect(url_for('admin_login_page'))
    
    try:
        charts = load_json_data(DATA_FILE)
        charts = [c for c in charts if c.get('id') != chart_id]
        save_json_data(DATA_FILE, charts)
    except Exception as e:
        print(f"Harita silme hatası: {e}")
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_course/<int:course_id>')
def admin_delete_course(course_id):
    """Eğitim silme"""
    if not session.get('admin_access'):
        return redirect(url_for('admin_login_page'))
    
    try:
        courses = load_json_data(COURSES_FILE)
        courses = [c for c in courses if c.get('id') != course_id]
        save_json_data(COURSES_FILE, courses)
    except Exception as e:
        print(f"Eğitim silme hatası: {e}")
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_user/<email>')
def admin_delete_user(email):
    """Kullanıcı silme (Artık kullanılmıyor)"""
    if not session.get('admin_access'):
        return redirect(url_for('admin_login_page'))
    
    # Kullanıcı sistemi kaldırıldığı için sadece yönlendirme yapıyoruz
    return redirect(url_for('admin_dashboard'))

# ============================================================================
# 📝 EKLEME/DÜZENLEME ROTALARI
# ============================================================================

@app.route('/admin/add_chart', methods=['POST'])
def admin_add_chart():
    """Yeni harita ekleme"""
    if not session.get('admin_access'):
        return redirect(url_for('admin_login_page'))
    
    try:
        charts = load_json_data(DATA_FILE)
        
        # Form verilerini al
        name = request.form.get('name')
        category = request.form.get('category', 'Genel')
        day = int(request.form.get('day'))
        month = int(request.form.get('month'))
        year = int(request.form.get('year'))
        hour = int(request.form.get('hour'))
        minute = int(request.form.get('minute'))
        lat = float(request.form.get('lat'))
        lon = float(request.form.get('lon'))
        tz = float(request.form.get('tz'))
        location_name = request.form.get('location_name', '')
        bio = request.form.get('bio', '')
        
        # Harita hesapla
        _, chart_data = ASTRO_MOTOR_NESNESİ.calculate_chart_data(
            year, month, day, hour, minute, tz, lat, lon, None, 'P', 'Astronomik'
        )
        
        asc_sign = "Bilinmeyen"
        sun_sign = "Bilinmeyen"
        if chart_data:
            asc_sign, _, _ = get_relative_degree(chart_data['cusps']['ASC'], 'Astronomik')
            sun_sign, _, _ = get_relative_degree(chart_data['planets']['Güneş'][0], 'Astronomik')
        
        # Resim yükleme
        image_filename = ""
        if 'chart_image' in request.files:
            file = request.files['chart_image']
            if file and file.filename:
                filename = secure_filename(file.filename)
                image_filename = f"{random.randint(1000,9999)}_{filename}"
                file.save(os.path.join(UPLOAD_FOLDER_CHARTS, image_filename))
        
        # Yeni harita objesi
        new_chart = {
            'id': max([c.get('id', 0) for c in charts] + [0]) + 1,
            'name': name,
            'category': category,
            'asc_sign': asc_sign,
            'sun_sign': sun_sign,
            'bio': bio,
            'image': image_filename,
            'year': year,
            'month': month,
            'day': day,
            'hour': hour,
            'minute': minute,
            'lat': lat,
            'lon': lon,
            'tz': tz,
            'location_name': location_name
        }
        
        charts.append(new_chart)
        save_json_data(DATA_FILE, charts)
        
    except Exception as e:
        print(f"Harita ekleme hatası: {e}")
        import traceback
        traceback.print_exc()
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit_chart/<int:chart_id>', methods=['POST'])
def admin_edit_chart(chart_id):
    """Harita düzenleme"""
    if not session.get('admin_access'):
        return redirect(url_for('admin_login_page'))
    
    try:
        charts = load_json_data(DATA_FILE)
        chart = next((c for c in charts if c.get('id') == chart_id), None)
        
        if chart:
            # Form verilerini al
            chart['name'] = request.form.get('name', chart['name'])
            chart['category'] = request.form.get('category', chart.get('category', 'Genel'))
            chart['day'] = int(request.form.get('day', chart['day']))
            chart['month'] = int(request.form.get('month', chart['month']))
            chart['year'] = int(request.form.get('year', chart['year']))
            chart['hour'] = int(request.form.get('hour', chart['hour']))
            chart['minute'] = int(request.form.get('minute', chart['minute']))
            chart['lat'] = float(request.form.get('lat', chart['lat']))
            chart['lon'] = float(request.form.get('lon', chart['lon']))
            chart['tz'] = float(request.form.get('tz', chart['tz']))
            chart['location_name'] = request.form.get('location_name', chart.get('location_name', ''))
            chart['bio'] = request.form.get('bio', chart.get('bio', ''))
            
            # Haritayı yeniden hesapla
            _, chart_data = ASTRO_MOTOR_NESNESİ.calculate_chart_data(
                chart['year'], chart['month'], chart['day'], chart['hour'], chart['minute'],
                chart['tz'], chart['lat'], chart['lon'], None, 'P', 'Astronomik'
            )
            
            if chart_data:
                asc_sign, _, _ = get_relative_degree(chart_data['cusps']['ASC'], 'Astronomik')
                sun_sign, _, _ = get_relative_degree(chart_data['planets']['Güneş'][0], 'Astronomik')
                chart['asc_sign'] = asc_sign
                chart['sun_sign'] = sun_sign
            
            # Resim güncelleme
            if 'chart_image' in request.files:
                file = request.files['chart_image']
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    image_filename = f"{random.randint(1000,9999)}_{filename}"
                    file.save(os.path.join(UPLOAD_FOLDER_CHARTS, image_filename))
                    chart['image'] = image_filename
            
            save_json_data(DATA_FILE, charts)
        
    except Exception as e:
        print(f"Harita düzenleme hatası: {e}")
        import traceback
        traceback.print_exc()
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add_course', methods=['POST'])
def admin_add_course():
    """Yeni eğitim ekleme"""
    if not session.get('admin_access'):
        return redirect(url_for('admin_login_page'))
    
    try:
        courses = load_json_data(COURSES_FILE)
        
        title = request.form.get('title')
        date = request.form.get('date')
        link = request.form.get('link', '')
        description = request.form.get('description', '')
        
        # Resim yükleme
        image_filename = ""
        if 'course_image' in request.files:
            file = request.files['course_image']
            if file and file.filename:
                filename = secure_filename(file.filename)
                image_filename = f"{random.randint(1000,9999)}_{filename}"
                file.save(os.path.join(UPLOAD_FOLDER_COURSES, image_filename))
        
        new_course = {
            'id': max([c.get('id', 0) for c in courses] + [0]) + 1,
            'title': title,
            'date': date,
            'link': link,
            'description': description,
            'image': image_filename
        }
        
        courses.append(new_course)
        save_json_data(COURSES_FILE, courses)
        
    except Exception as e:
        print(f"Eğitim ekleme hatası: {e}")
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/update_contact', methods=['POST'])
def admin_update_contact():
    """İletişim bilgilerini güncelleme"""
    if not session.get('admin_access'):
        return redirect(url_for('admin_login_page'))
    
    try:
        contact = {
            'email': request.form.get('email', ''),
            'phone': request.form.get('phone', ''),
            'bio': request.form.get('bio', '')
        }
        save_json_data(CONTACT_FILE, contact)
    except Exception as e:
        print(f"İletişim güncelleme hatası: {e}")
    
    return redirect(url_for('admin_dashboard'))

    
# ============================================================================
# 🛰️ API ROTALARI (RETURN & GET DATA & ADMIN UPLOAD)
# ============================================================================

@app.route('/api/admin/smart_parse', methods=['POST'])
def admin_smart_parse():
    if not session.get('admin_access'): return jsonify({'success': False, 'error': 'Yetkisiz'})
    try:
        raw_text = request.json.get('text', '')
        data = {}
        date_match = re.search(r'(\d{1,2})[./-](\d{1,2})[./-](\d{4})', raw_text)
        if date_match:
            data['day'] = int(date_match.group(1)); data['month'] = int(date_match.group(2)); data['year'] = int(date_match.group(3)); raw_text = raw_text.replace(date_match.group(0), '')
        time_match = re.search(r'(\d{1,2})[:.](\d{2})', raw_text)
        if time_match:
            data['hour'] = int(time_match.group(1)); data['minute'] = int(time_match.group(2)); raw_text = raw_text.replace(time_match.group(0), '')
        else: data['hour'] = 12; data['minute'] = 0
        parts = [p.strip() for p in raw_text.split(',') if p.strip()]
        manual_utc_found = False; remaining_parts = []
        for p in parts:
            if re.match(r'^[+\-]?\d+(\.\d+)?$', p): data['tz'] = float(p); manual_utc_found = True
            else: remaining_parts.append(p)
        if len(remaining_parts) > 0: data['name'] = remaining_parts[0]
        location_name = ""
        if len(remaining_parts) > 1: location_name = remaining_parts[1]
        if len(remaining_parts) > 2: data['category'] = remaining_parts[2]
        else: data['category'] = "Genel"
        data['location_name'] = location_name
        if location_name:
            try:
                geolocator = Nominatim(user_agent="astro_smart_parser_v3")
                loc = geolocator.geocode(location_name, language='tr')
                if loc:
                    data['lat'] = loc.latitude; data['lon'] = loc.longitude
                    if not manual_utc_found:
                        tf = TimezoneFinder(); tz_str = tf.timezone_at(lng=loc.longitude, lat=loc.latitude)
                        if tz_str:
                            tz_obj = pytz.timezone(tz_str); y = data.get('year', 2000); m = data.get('month', 1); d = data.get('day', 1)
                            dt = datetime.datetime(y, m, d, 12, 0); offset = tz_obj.utcoffset(dt).total_seconds() / 3600.0; data['tz'] = offset
                else: data['lat'] = 0.0; data['lon'] = 0.0
            except: pass
        return jsonify({'success': True, 'data': data})
    except Exception as e: return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/upload_sfch', methods=['POST'])
def admin_upload_sfch():
    if not session.get('admin_access'): return jsonify({'success': False, 'error': 'Yetkisiz'})
    try:
        if 'file' not in request.files: return jsonify({'success': False, 'error': 'Dosya yok.'})
        file = request.files['file']
        content = ""
        try: content = file.read().decode('utf-8')
        except: file.seek(0); content = file.read().decode('latin-1', errors='ignore')

        f = io.StringIO(content)
        reader = csv.reader(f, delimiter=',', quotechar='"')
        success_count = 0; failed_count = 0; duplicate_count = 0
        current_charts = load_json_data(DATA_FILE)
        geolocator = Nominatim(user_agent="astro_csv_filter_final")
        
        existing_signatures = set()
        for c in current_charts:
            sig = f"{str(c.get('name', '')).strip().lower()}_{c.get('year')}_{c.get('month')}_{c.get('day')}"
            existing_signatures.add(sig)

        for row in reader:
            if not row or len(row) < 5: continue
            if not row[1].strip().lstrip('-').replace('.', '', 1).isdigit(): continue
            try:
                name = row[0].strip()
                d, m, y = int(row[1]), int(row[2]), int(row[3])
                h, mn = int(row[4]), int(row[5])
                
                current_sig = f"{name.lower()}_{y}_{m}_{d}"
                if current_sig in existing_signatures: duplicate_count += 1; continue
                
                tz = float(row[6].replace(',', '.'))
                location = row[-1].strip()
                if not location or location.isdigit(): location = "Bilinmiyor"
                lat, lon = 0.0, 0.0
                if location != "Bilinmiyor":
                    try:
                        loc = geolocator.geocode(location, language='tr', timeout=1)
                        if loc: lat, lon = loc.latitude, loc.longitude
                    except: pass
                
                _, calc_res = ASTRO_MOTOR_NESNESİ.calculate_chart_data(y, m, d, h, mn, tz, lat, lon, None, 'P', 'Astronomik')
                asc_sign = "Bilinmeyen"; sun_sign = "Bilinmeyen"
                if calc_res:
                    asc_sign, _, _ = get_relative_degree(calc_res['cusps']['ASC'], 'Astronomik')
                    sun_sign, _, _ = get_relative_degree(calc_res['planets']['Güneş'][0], 'Astronomik')

                new_chart = {
                    "id": random.randint(100000, 999999),
                    "name": name, "category": "Bütün Haritalar",
                    "asc_sign": asc_sign, "sun_sign": sun_sign, "bio": "Dosyadan yüklendi.", "image": "",
                    "year": y, "month": m, "day": d, "hour": h, "minute": mn,
                    "lat": lat, "lon": lon, "tz": tz,
                    "location_name": location
                }
                current_charts.append(new_chart)
                existing_signatures.add(current_sig)
                success_count += 1
            except: failed_count += 1
        save_json_data(DATA_FILE, current_charts)
        return jsonify({'success': True, 'message': f"İşlem Tamamlandı!\n✅ Eklenen: {success_count}\n⚠️ Mükerrer: {duplicate_count}"})
    except Exception as e: return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/auto_classify', methods=['POST'])
def admin_auto_classify():
    if not session.get('admin_access'): return jsonify({'success': False, 'error': 'Yetkisiz'})
    try:
        charts = load_json_data(DATA_FILE)
        count = 0
        for c in charts:
            asc = c.get('asc_sign', 'Bilinmeyen')
            if asc and asc != "Bilinmeyen": c['category'] = f"Yükselen {asc}"; count += 1
        save_json_data(DATA_FILE, charts)
        return jsonify({'success': True, 'message': f"{count} harita sınıflandırıldı!"})
    except Exception as e: return jsonify({'success': False, 'error': str(e)})

# ============================================================================
# 🔄 API: RETURN HESAPLAMA (GÜNCELLENDİ: TROPIKAL / ASTRONOMİK / DRAKONİK)
# ============================================================================
@app.route('/api/calculate_returns', methods=['POST'])
def api_calculate_returns():
    try:
        print("\n--- RETURN HESAPLAMA BAŞLADI ---")
        data = request.get_json()
        
        # ID'yi al
        raw_id = data.get('natal_chart_id')
        natal_chart_id = int(raw_id) if raw_id is not None else -1
        
        start_year = int(data.get('start_year'))
        end_year = int(data.get('end_year'))
        planet_name = data.get('planet_name')
        target_zodiac = data.get('zodiac_type', 'Tropikal') # Varsayılan: Tropikal
        
        print(f"İstek: ID={natal_chart_id}, Gezegen={planet_name}, Yıl={start_year}-{end_year}, Tip={target_zodiac}")

        # 1. HARİTAYI BUL
        natal_chart = None
        active_charts = session.get('active_charts', [])
        
        # A) Aktif Haritalarda Ara
        if 0 <= natal_chart_id < len(active_charts):
            natal_chart = active_charts[natal_chart_id]
            print("-> Kaynak: Aktif Oturum Haritası")
            
        # B) Veri Bankasında Ara
        if not natal_chart:
            all_public = load_json_data(DATA_FILE)
            natal_chart = next((c for c in all_public if c['id'] == natal_chart_id), None)
            if natal_chart: print("-> Kaynak: Veri Bankası")

        if not natal_chart:
            return jsonify({'success': False, 'error': 'Harita bulunamadı.'})
        
        # 2. HESAPLAMA VERİLERİNİ HAZIRLA
        swe.set_ephe_path(EPHE_PATH) # Yolu garantile
        
        tz_val = float(natal_chart.get('tz', natal_chart.get('tz_offset', 0)))
        utc_hour = natal_chart['hour'] + (natal_chart['minute']/60.0) - tz_val
        tjd_natal = swe.julday(natal_chart['year'], natal_chart['month'], natal_chart['day'], utc_hour)
        
        p_map = {'Güneş': swe.SUN, 'Ay': swe.MOON, 'Merkür': swe.MERCURY, 'Venüs': swe.VENUS, 'Mars': swe.MARS, 'Jüpiter': swe.JUPITER, 'Satürn': swe.SATURN}
        pid = p_map.get(planet_name, swe.SUN)
        
        # 3. MODU AYARLA (HEDEF DERECEYİ BUL)
        calc_flags = swe.FLG_SWIEPH | swe.FLG_SPEED
        target_lon = 0
        
        if target_zodiac == 'Astronomik':
            # Astronomik (Sidereal - Fagan/Bradley)
            swe.set_sid_mode(swe.SIDM_FAGAN_BRADLEY, 0, 0)
            calc_flags |= swe.FLG_SIDEREAL
            res = swe.calc_ut(tjd_natal, pid, calc_flags)
            target_lon = res[0][0]
            
        elif target_zodiac == 'Drakonik':
            # Drakonik (Tropikal - Mean Node)
            swe.set_sid_mode(0, 0, 0) # Tropikal mod
            p_res = swe.calc_ut(tjd_natal, pid, swe.FLG_SWIEPH | swe.FLG_SPEED)[0][0]
            n_res = swe.calc_ut(tjd_natal, swe.MEAN_NODE, swe.FLG_SWIEPH | swe.FLG_SPEED)[0][0]
            target_lon = (p_res - n_res) % 360.0
            
        else:
            # Tropikal (Standart)
            swe.set_sid_mode(0, 0, 0)
            res = swe.calc_ut(tjd_natal, pid, calc_flags)
            target_lon = res[0][0]
        
        # 4. TARAMA FONKSİYONU
        def get_current_pos(t):
            if target_zodiac == 'Drakonik':
                # Drakonik ise o anki (Gezegen - Node) farkını hesapla
                pp = swe.calc_ut(t, pid, swe.FLG_SWIEPH | swe.FLG_SPEED)[0][0]
                nn = swe.calc_ut(t, swe.MEAN_NODE, swe.FLG_SWIEPH | swe.FLG_SPEED)[0][0]
                return (pp - nn) % 360.0
            else:
                # Tropikal veya Astronomik (Bayraklar yukarıda ayarlandı)
                return swe.calc_ut(t, pid, calc_flags)[0][0]

        # 5. DÖNÜŞLERİ ARA
        returns = []
        curr_jd = swe.julday(start_year, 1, 1)
        limit_jd = swe.julday(end_year + 1, 1, 1)
        step = 0.5 if pid == swe.MOON else 2.0
        
        safety = 0
        while curr_jd < limit_jd and safety < 20000:
            safety += 1
            
            p1 = get_current_pos(curr_jd)
            p2 = get_current_pos(curr_jd + step)
            
            # Açılar arasındaki fark (Geçiş kontrolü)
            d1 = (p1 - target_lon + 180) % 360 - 180
            d2 = (p2 - target_lon + 180) % 360 - 180
            
            if (d1 * d2 < 0) and (abs(d1 - d2) < 180):
                # Geçiş bulundu, hassaslaştır (Binary Search benzeri)
                low = curr_jd
                high = curr_jd + step
                found_time = high
                
                for _ in range(15):
                    mid = (low + high) / 2.0
                    pm = get_current_pos(mid)
                    dm = (pm - target_lon + 180) % 360 - 180
                    if d1 * dm < 0:
                        high = mid
                    else:
                        low = mid
                    found_time = low
                
                # Tarihi Çevir ve Kaydet
                y, m, d, h_dec = swe.revjul(found_time)
                if start_year <= y <= end_year:
                    h = int(h_dec)
                    mn = int((h_dec - h) * 60)
                    date_str = f"{d:02d}.{m:02d}.{y} {h:02d}:{mn:02d}"
                    print(f"   -> Bulundu: {date_str} ({target_zodiac})")
                    returns.append({
                        'year': y, 'month': m, 'day': d, 
                        'hour': h, 'minute': mn, 
                        'date_str': date_str
                    })
                
                # Bir sonraki döngü için ileri atla (Ay ise 25 gün, Güneş ise 300 gün)
                curr_jd = found_time + (25.0 if pid == swe.MOON else 300.0)
                continue
            
            curr_jd += step

        print(f"--- BİTTİ: {len(returns)} sonuç ---")
        return jsonify({'success': True, 'returns': returns})

    except Exception as e:
        print(f"API HATASI: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/load_return_chart', methods=['POST'])
def load_return_chart():
    try:
        y, mo, d = int(request.form.get('r_year')), int(request.form.get('r_month')), int(request.form.get('r_day'))
        h, mn = int(request.form.get('r_hour')), int(request.form.get('r_minute'))
        lat, lon, tz_off = float(request.form.get('r_lat')), float(request.form.get('r_lon')), float(request.form.get('r_tz'))
        title = f"{request.form.get('planet_name')} Dönüşü ({y})"
        z_type = request.form.get('r_zodiac_type', 'Astronomik')
        
        res_text, chart_data = ASTRO_MOTOR_NESNESİ.calculate_chart_data(y, mo, d, h, mn, tz_off, lat, lon, None, "P", z_type)
        if chart_data:
            new_chart = {'id': len(session.get('active_charts', []))+1, 'name': title, 'year': y, 'month': mo, 'day': d, 'hour': h, 'minute': mn, 'tz_offset': tz_off, 'lat': lat, 'lon': lon, 'location_name': request.form.get('r_loc_name'), 'zodiac_type': z_type, 'house_system': "Placidus", 'type': 'return'}
            current = session.get('active_charts', []); current.insert(0, new_chart); session['active_charts'] = current
            session['current_chart_index'] = 0; session['last_report'] = f"RETURN HARİTASI ({z_type})\n\n{res_text}"; session['last_chart'] = chart_data; session['current_chart_data'] = new_chart
            return redirect(url_for('home', tab='aktif'))
    except Exception as e: print(e)
    return redirect(url_for('home'))

@app.route('/api/get_asc', methods=['POST'])
def get_asc():
    try:
        d = request.get_json()
        _, c = ASTRO_MOTOR_NESNESİ.calculate_chart_data(int(d['year']), int(d['month']), int(d['day']), int(d['hour']), int(d['minute']), float(d['tz']), float(d['lat']), float(d['lon']), None, 'P', d.get('zodiac_type', 'Astronomik'))
        asc = c['cusps']['ASC']; const, _, fmt = get_relative_degree(asc, d.get('zodiac_type', 'Astronomik')); return jsonify({'success': True, 'asc': f"{const} {fmt}"})
    except: return jsonify({'success': False})

@app.route('/api/search_location', methods=['POST'])
def search_location():
    try:
        d = request.get_json()
        city = d.get('city')
        now = datetime.now()
        
        # Tarihi al
        try:
            req_year = int(d.get('year', now.year))
            req_month = int(d.get('month', now.month))
            req_day = int(d.get('day', now.day))
        except:
            req_year, req_month, req_day = now.year, now.month, now.day
        
        # Konumu ara
        geolocator = Nominatim(user_agent=f"astro_{random.randint(1000,9999)}")
        locs = geolocator.geocode(city, exactly_one=False, limit=5, language='tr', timeout=10)
        
        if not locs:
            return jsonify({'success': False, 'message': 'Bulunamadı'})
        
        res = []
        tf = None
        try:
            tf = TimezoneFinder(in_memory=True)
        except:
            pass
        
        for l in locs:
            offset = 0.0
            tz_name = "UTC"
            
            # Address'i Türkçe'ye çevir
            address_turkish = l.address
            
            # Yaygın ülke isimlerini Türkçe'ye çevir
            country_translations = {
                'Turkey': 'Türkiye',
                'United States': 'Amerika Birleşik Devletleri',
                'United Kingdom': 'Birleşik Krallık',
                'Germany': 'Almanya',
                'France': 'Fransa',
                'Italy': 'İtalya',
                'Spain': 'İspanya',
                'Greece': 'Yunanistan',
                'Netherlands': 'Hollanda',
                'Belgium': 'Belçika',
                'Austria': 'Avusturya',
                'Switzerland': 'İsviçre',
                'Sweden': 'İsveç',
                'Norway': 'Norveç',
                'Denmark': 'Danimarka',
                'Poland': 'Polonya',
                'Russia': 'Rusya',
                'China': 'Çin',
                'Japan': 'Japonya',
                'South Korea': 'Güney Kore',
                'India': 'Hindistan',
                'Pakistan': 'Pakistan',
                'Iran': 'İran',
                'Iraq': 'Irak',
                'Syria': 'Suriye',
                'Egypt': 'Mısır',
                'Saudi Arabia': 'Suudi Arabistan',
                'United Arab Emirates': 'Birleşik Arap Emirlikleri',
                'Israel': 'İsrail',
                'Lebanon': 'Lübnan',
                'Jordan': 'Ürdün',
                'Cyprus': 'Kıbrıs',
                'Bulgaria': 'Bulgaristan',
                'Romania': 'Romanya',
                'Serbia': 'Sırbistan',
                'Croatia': 'Hırvatistan',
                'Bosnia and Herzegovina': 'Bosna-Hersek',
                'Albania': 'Arnavutluk',
                'North Macedonia': 'Kuzey Makedonya',
                'Montenegro': 'Karadağ',
                'Kosovo': 'Kosova'
            }
            
            for eng, tr in country_translations.items():
                address_turkish = address_turkish.replace(eng, tr)
            
            # ÖNCELİK: TÜRKİYE İÇİN MANUEL KONTROL (pytz'ye güvenme!)
            if 'Turkey' in l.address or 'Türkiye' in address_turkish:
                # 2016'dan sonra yaz saati kaldırıldı, UTC+3 sabit
                if req_year >= 2016:
                    offset = 3.0
                else:
                    # 2016 öncesi: Mart-Ekim arası UTC+3 (yaz), Kasım-Şubat UTC+2 (kış)
                    if 3 <= req_month <= 10:
                        offset = 3.0  # Yaz saati
                    else:
                        offset = 2.0  # Kış saati
                tz_name = "Europe/Istanbul"
            
            # Türkiye değilse pytz ile hesapla
            elif tf:
                try:
                    # Timezone'u bul
                    found_tz = tf.timezone_at(lng=l.longitude, lat=l.latitude)
                    
                    if found_tz:
                        tz_name = found_tz
                        
                        # Hedef tarihi oluştur (saat 12:00'de hesapla)
                        target_dt = datetime.datetime(req_year, req_month, req_day, 12, 0)
                        
                        # Timezone objesini oluştur
                        tz_obj = pytz.timezone(tz_name)
                        
                        # UTC offset'i hesapla
                        try:
                            dt_aware = tz_obj.localize(target_dt, is_dst=False)
                        except:
                            try:
                                dt_aware = tz_obj.localize(target_dt, is_dst=True)
                            except:
                                dt_aware = tz_obj.normalize(tz_obj.localize(target_dt))
                        
                        # Offset'i saat cinsinden hesapla
                        offset = dt_aware.utcoffset().total_seconds() / 3600.0
                        
                except Exception as e:
                    print(f"Timezone hesaplama hatası ({l.address}): {e}")
                    offset = 0.0
            else:
                # TimezoneFinder yoksa varsayılan
                offset = 0.0
            
            res.append({
                'address': l.address,
                'lat': l.latitude,
                'lon': l.longitude,
                'tz_offset': offset,
                'tz_name': tz_name
            })
        
        return jsonify({'success': True, 'results': res})
        
    except Exception as e:
        print(f"search_location genel hatası: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/search_celestial_events', methods=['POST'])
def api_search_celestial_events():
    try:
        import os 
        # 1. Gelen Veriyi Al
        data = request.json
        year = int(data.get('year', 2025))
        zodiac_type = data.get('zodiac_type', 'Tropikal') 
        
        eclipses = []
        phases = []
        
        # 2. EPHEMERIS YOLUNU AYARLA
        base_dir = os.path.dirname(os.path.abspath(__file__))
        ephe_path = os.path.join(base_dir, 'ephe')
        swe.set_ephe_path(ephe_path)

        # 3. MOD SEÇİMİ (Kritik Düzeltme)
        # Önce dosyalar çalışıyor mu diye test et
        try:
            swe.calc_ut(2460000, swe.SUN, swe.FLG_SWIEPH)
            ACTIVE_FLAG = swe.FLG_SWIEPH | swe.FLG_SPEED
            ECL_FLAG = 0 # Swiss Eph modu için 0 yeterli
            print("✅ Swiss Ephemeris Modu Aktif (Dosyalar Okundu)")
        except:
            # Hata verirse Moshier moda geç
            ACTIVE_FLAG = swe.FLG_MOSEPH
            ECL_FLAG = swe.FLG_MOSEPH_ECL_ALL
            print("⚠️ Ephemeris Hatası: Moshier (Matematiksel) Moda Geçildi.")

        # --- YARDIMCI: Zodyak Konumu ---
        def get_zodiac_pos(julian_day, body_id):
            swe.set_sid_mode(0, 0, 0)
            res = swe.calc_ut(julian_day, body_id, ACTIVE_FLAG)[0]
            deg_trop = res[0]
            final_deg = deg_trop
            
            if zodiac_type == 'Astronomik':
                swe.set_sid_mode(swe.SIDM_FAGAN_BRADLEY, 0, 0)
                res_sid = swe.calc_ut(julian_day, body_id, ACTIVE_FLAG | swe.FLG_SIDEREAL)[0]
                final_deg = res_sid[0]
                
            elif zodiac_type == 'Drakonik':
                node_res = swe.calc_ut(julian_day, swe.MEAN_NODE, ACTIVE_FLAG)[0]
                node_deg = node_res[0]
                final_deg = (deg_trop - node_deg + 360) % 360
                
            return final_deg

        # --- YARDIMCI: Burç İsmi ---
        def get_sign_name(degree):
            signs = ["Koç", "Boğa", "İkizler", "Yengeç", "Aslan", "Başak", "Terazi", "Akrep", "Yay", "Oğlak", "Kova", "Balık"]
            idx = int(degree // 30)
            rem = degree % 30
            d = int(rem)
            m = int((rem - d) * 60)
            return f"{d}° {signs[idx]} {m}'"

        # --- TARAMA ---
        tjd_start = swe.julday(year, 1, 1)
        tjd_end = swe.julday(year, 12, 31)
        
        # A) GÜNEŞ TUTULMALARI
        tjd = tjd_start
        while tjd < tjd_end:
            try:
                res = swe.sol_eclipse_when_glob(tjd, ECL_FLAG)
            except: res = (0, [0])
                
            if res[0] & swe.ECL_ALLTYPES_SOLAR:
                t_eclipse = res[1][0]
                if t_eclipse > tjd_end: break
                
                y, m, d, h_dec = swe.revjul(t_eclipse)
                h = int(h_dec); mn = int((h_dec - h) * 60)
                
                deg = get_zodiac_pos(t_eclipse, swe.SUN)
                sign_str = get_sign_name(deg)
                
                eclipses.append({
                    "title": "Güneş Tutulması", 
                    "date_str": f"{d:02d}.{m:02d}.{y} {h:02d}:{mn:02d}", 
                    "sign_info": f"{sign_str} ({zodiac_type})", 
                    "year":y, "month":m, "day":d, "hour":h, "minute":mn
                })
                tjd = t_eclipse + 25 
            else: 
                tjd += 25

        # B) AY TUTULMALARI
        tjd = tjd_start
        while tjd < tjd_end:
            try:
                res = swe.lun_eclipse_when(tjd, ECL_FLAG)
            except: res = (0, [0])

            if res[0] & swe.ECL_ALLTYPES_LUNAR:
                t_eclipse = res[1][0]
                if t_eclipse > tjd_end: break
                
                y, m, d, h_dec = swe.revjul(t_eclipse)
                h = int(h_dec); mn = int((h_dec - h) * 60)
                
                deg = get_zodiac_pos(t_eclipse, swe.MOON)
                sign_str = get_sign_name(deg)
                
                eclipses.append({
                    "title": "Ay Tutulması", 
                    "date_str": f"{d:02d}.{m:02d}.{y} {h:02d}:{mn:02d}", 
                    "sign_info": f"{sign_str} ({zodiac_type})", 
                    "year":y, "month":m, "day":d, "hour":h, "minute":mn
                })
                tjd = t_eclipse + 25
            else: 
                tjd += 25

        # C) YENİ AY VE DOLUNAYLAR
        t_search = tjd_start
        while t_search < tjd_end:
            r_sun = swe.calc_ut(t_search, swe.SUN, ACTIVE_FLAG)[0][0]
            r_moon = swe.calc_ut(t_search, swe.MOON, ACTIVE_FLAG)[0][0]
            
            diff = (r_moon - r_sun + 360) % 360
            days_to_new = (360 - diff) / 12.2
            days_to_full = (180 - diff + 360) % 360 / 12.2
            
            if days_to_new < days_to_full: 
                target_tjd = t_search + days_to_new
                type_str = "Yeni Ay"
            else: 
                target_tjd = t_search + days_to_full
                type_str = "Dolunay"
            
            # Hassaslaştırma
            for _ in range(3):
                r_s = swe.calc_ut(target_tjd, swe.SUN, ACTIVE_FLAG)[0][0]
                r_m = swe.calc_ut(target_tjd, swe.MOON, ACTIVE_FLAG)[0][0]
                d_diff = (r_m - r_s + 360) % 360
                
                if type_str == "Dolunay": 
                    err = (d_diff - 180)
                    while err > 180: err -= 360
                    while err < -180: err += 360
                else: 
                    err = d_diff
                    if err > 180: err -= 360
                
                target_tjd -= (err / 12.19)
            
            # Kaydet
            if target_tjd >= tjd_start and target_tjd <= tjd_end:
                # Çakışma kontrolü
                is_duplicate = False
                t_y, t_m, t_d, _ = swe.revjul(target_tjd)
                for ec in eclipses:
                    if ec["year"] == t_y and ec["month"] == t_m and abs(ec["day"] - t_d) < 2:
                        is_duplicate = True; break
                
                if not is_duplicate:
                    y, m, d, h_dec = swe.revjul(target_tjd)
                    h = int(h_dec); mn = int((h_dec - h) * 60)
                    
                    deg = get_zodiac_pos(target_tjd, swe.MOON)
                    sign_str = get_sign_name(deg)
                    
                    phases.append({
                        "title": type_str, 
                        "date_str": f"{d:02d}.{m:02d}.{y} {h:02d}:{mn:02d}", 
                        "sign_info": f"{sign_str} ({zodiac_type})", 
                        "year":y, "month":m, "day":d, "hour":h, "minute":mn
                    })
            
            t_search = target_tjd + 14
            
        # Sıralama
        eclipses.sort(key=lambda x: (x['year'], x['month'], x['day']))
        phases.sort(key=lambda x: (x['year'], x['month'], x['day']))

        return jsonify({'success': True, 'eclipses': eclipses, 'phases': phases})

    except Exception as e:
        print(f"API Celestial Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})
        
@app.route('/load_celestial_event', methods=['POST'])
def load_celestial_event():
    try:
        title = request.form.get('title')
        year = int(request.form.get('year'))
        month = int(request.form.get('month'))
        day = int(request.form.get('day'))
        hour = int(request.form.get('hour'))
        minute = int(request.form.get('minute'))
        
        res_text, chart_data = ASTRO_MOTOR_NESNESİ.calculate_chart_data(year, month, day, hour, minute, 0.0, 0.0, 0.0, None, "P", "Astronomik")
        if chart_data:
            new_chart = {'id': len(session.get('active_charts', [])) + 1, 'name': title, 'year': year, 'month': month, 'day': day, 'hour': hour, 'minute': minute, 'tz_offset': 0.0, 'lat': 0.0, 'lon': 0.0, 'location_name': "Evrensel (UTC 0)", 'zodiac_type': "Astronomik", 'house_system': "Placidus", 'type': 'event'}
            current_charts = session.get('active_charts', [])
            current_charts.insert(0, new_chart)
            session['active_charts'] = current_charts
            session['current_chart_index'] = 0
            session['last_report'] = res_text
            session['last_chart'] = chart_data
            session['current_chart_data'] = new_chart
            return redirect(url_for('home', tab='aktif'))
    except Exception as e: print(e)
    return redirect(url_for('home'))

# ============================================================================
# ❤️ SİNASTRİ HESAPLAMA (DİNAMİK ZOD-TİPİ HESAPLAMA)
# ============================================================================

@app.route('/sinastri_hesapla', methods=['POST'])
def sinastri_hesapla():
    try:
        # --- 1. KİŞİNİN VERİLERİNİ AL ---
        n1 = request.form.get('name1')
        d1 = int(request.form.get('day1')); m1 = int(request.form.get('month1')); y1 = int(request.form.get('year1'))
        h1 = int(request.form.get('hour1')); mn1 = int(request.form.get('minute1'))
        tz1 = float(request.form.get('tz1')); lat1 = float(request.form.get('lat1')); lon1 = float(request.form.get('lon1'))
        z1 = request.form.get('zodiac_type1', 'Astronomik') 

        # --- 2. KİŞİNİN VERİLERİNİ AL ---
        n2 = request.form.get('name2')
        d2 = int(request.form.get('day2')); m2 = int(request.form.get('month2')); y2 = int(request.form.get('year2'))
        h2 = int(request.form.get('hour2')); mn2 = int(request.form.get('minute2'))
        tz2 = float(request.form.get('tz2')); lat2 = float(request.form.get('lat2')); lon2 = float(request.form.get('lon2'))
        z2 = request.form.get('zodiac_type2', 'Astronomik')

        # --- HESAPLAMA MOTORUNU ÇALIŞTIR ---
        _, chart1_data = ASTRO_MOTOR_NESNESİ.calculate_chart_data(
            y1, m1, d1, h1, mn1, tz1, lat1, lon1, None, 'P', z1
        )
        if chart1_data:
            chart1_data['name'] = n1
            chart1_data['zodiac_type'] = z1

        _, chart2_data = ASTRO_MOTOR_NESNESİ.calculate_chart_data(
            y2, m2, d2, h2, mn2, tz2, lat2, lon2, None, 'P', z2
        )
        if chart2_data:
            chart2_data['name'] = n2
            chart2_data['zodiac_type'] = z2

        # --- SİNASTRİ KIYASLAMASI ---
        synastry_results = []
        if chart1_data and chart2_data:
            synastry_results = ASTRO_MOTOR_NESNESİ.calculate_synastry_aspects(chart1_data, chart2_data)

        # --- SONUCU EKRANA BAS ---
        combined_chart_structure = {
            'natal': chart1_data,   
            'transit': chart2_data  
        }

        return render_template(
            'report_output.html', 
            sinastri_raporu=synastry_results,
            last_chart=combined_chart_structure,
            k1=chart1_data, 
            k2=chart2_data
        )

    except Exception as e:
        traceback.print_exc()
        return f"<h3>Sinastri Hesaplama Hatası Oluştu:</h3><p>{str(e)}</p>"

def astronomik_cakisma_onleyici(planets_data):
    if not planets_data: return planets_data
    
    # Mutlak dereceye göre (0-360) sırala (Koç -> Balık)
    sorted_planets = sorted(planets_data.items(), key=lambda x: float(x[1][0]))
    
    last_abs_degree = -10.0
    current_level = 0
    # Katmanlar: Sadece içeri doğru (negatif) basamaklama yaparak taşmayı önler
    # 0: Orijinal hat, -22: Bir alt katman, -44: İkinci alt katman
    levels = [0, -22, -44] 
    
    updated_planets = {}
    for name, data in sorted_planets:
        curr_abs_deg = float(data[0])
        
        diff = abs(curr_abs_deg - last_abs_degree)
        if diff > 180: diff = 360 - diff 
        
        # 5 dereceden yakınsa katman değiştir
        if diff < 5.0:
            current_level = (current_level + 1) % len(levels)
        else:
            current_level = 0
            
        new_data = list(data)
        new_data.append(levels[current_level]) # En sona offseti ekle
        updated_planets[name] = new_data
        
        last_abs_degree = curr_abs_deg
        
    return updated_planets

@app.route('/api/get_synastry_data', methods=['POST'])
def get_synastry_data():
    try:
        print("\n🔵 SİNASTRİ HESAPLAMA MODÜLÜ DEVREDE...")
        data = request.json
        id1 = int(data.get('id1'))
        id2 = int(data.get('id2'))
        calc_type = data.get('calc_type', 'Sinastri')

        active_charts = session.get('active_charts', [])

        if id1 < 0 or id1 >= len(active_charts) or id2 < 0 or id2 >= len(active_charts):
             return jsonify({'success': False, 'error': 'Harita indeksi hatalı.'})

        raw_c1 = active_charts[id1]
        raw_c2 = active_charts[id2]

        # YARDIMCI FONKSİYONLAR
        def safe_float(val, default=0.0):
            try:
                return float(val) if val is not None else default
            except:
                return default

        def safe_int(val, default=0):
            try:
                return int(val) if val is not None else default
            except:
                return default

        def get_or_calculate_full_data(chart_meta):
            name = chart_meta.get('name', 'Bilinmeyen')
            
            if chart_meta.get('planets') and isinstance(chart_meta['planets'], dict) and len(chart_meta['planets']) > 0:
                print(f"✅ HAZIR VERİ BULUNDU: {name}")
                return chart_meta

            print(f"⚠️ VERİ EKSİK, HESAPLANIYOR: {name}")
            
            year = safe_int(chart_meta.get('year'), 2000)
            month = safe_int(chart_meta.get('month'), 1)
            day = safe_int(chart_meta.get('day'), 1)
            hour = safe_int(chart_meta.get('hour'), 12)
            minute = safe_int(chart_meta.get('minute'), 0)
            
            lat = safe_float(chart_meta.get('lat') or chart_meta.get('latitude'), 0.0)
            lon = safe_float(chart_meta.get('lon') or chart_meta.get('longitude'), 0.0)
            tz = safe_float(chart_meta.get('tz') or chart_meta.get('tz_offset'), 3.0)

            if lat == 0.0 and lon == 0.0:
                lat, lon, tz = 41.0082, 28.9784, 3.0

            zodiac_type = chart_meta.get('zodiac_type') or chart_meta.get('zodiac') or 'Astronomik'
            h_sys_name = chart_meta.get('house_system') or chart_meta.get('house_system_name') or 'Placidus'
            house_code = ASTRO_MOTOR_NESNESİ.HOUSE_SYSTEMS.get(h_sys_name, 'P')

            try:
                _, calculated_data = ASTRO_MOTOR_NESNESİ.calculate_chart_data(
                    year, month, day, hour, minute, tz, lat, lon, None, house_code, zodiac_type
                )
                
                full_chart = chart_meta.copy()
                if calculated_data:
                    full_chart.update(calculated_data) 
                    full_chart['zodiac_type'] = zodiac_type
                
                return full_chart

            except Exception as inner_e:
                print(f"   ❌ MOTOR HATASI: {inner_e}")
                return chart_meta

        # 1. VERİLERİ ÇEK/HESAPLA
        c1_full = get_or_calculate_full_data(raw_c1)
        c2_full = get_or_calculate_full_data(raw_c2)

        # --- ÇAKIŞMA ÖNLEYİCİ DEVRE DIŞI (Frontend kendi algoritmasını kullanıyor) ---
        # if 'planets' in c1_full:
        #     c1_full['planets'] = astronomik_cakisma_onleyici(c1_full['planets'])
        # if 'planets' in c2_full:
        #     c2_full['planets'] = astronomik_cakisma_onleyici(c2_full['planets'])
        # -------------------------------------------------------

        # --- KOMPOZİT İSE HESAPLA ---
        if calc_type == 'Kompozit':
            # ... (mevcut kompozit kodun buraya gelecek) ...
            pass

        # SİNASTRİ PAKETİ
        synastry_package = {
            'type': 'synastry',
            'chart1': c2_full,  # DIŞ çark
            'chart2': c1_full,  # İÇ çark
            'houses': c1_full.get('houses', {}),
            'cusps': c1_full.get('houses', {}),
            'boundaries': c1_full.get('boundaries', []),
            'map_type': 'synastry' # MongoDB için tipini de ekledik
        }
        
        return jsonify({
            'success': True,
            'is_composite': False,
            'data': synastry_package,
            'id1': id1, 'id2': id2
        })

    except Exception as e:
        print(f"GENEL SİNASTRİ HATASI: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})
    
        # --- HESAPLAMA VE VERİ KURTARMA FONKSİYONU ---
        def get_or_calculate_full_data(chart_meta):
            name = chart_meta.get('name', 'Bilinmeyen')
            
            if chart_meta.get('planets') and isinstance(chart_meta['planets'], dict) and len(chart_meta['planets']) > 0:
                print(f"✅ HAZIR VERİ BULUNDU: {name}")
                return chart_meta

            print(f"⚠️ VERİ EKSİK, HESAPLANIYOR: {name}")
            
            year = safe_int(chart_meta.get('year'), 2000)
            month = safe_int(chart_meta.get('month'), 1)
            day = safe_int(chart_meta.get('day'), 1)
            hour = safe_int(chart_meta.get('hour'), 12)
            minute = safe_int(chart_meta.get('minute'), 0)
            
            lat = safe_float(chart_meta.get('lat') or chart_meta.get('latitude'), 0.0)
            lon = safe_float(chart_meta.get('lon') or chart_meta.get('longitude'), 0.0)
            tz = safe_float(chart_meta.get('tz') or chart_meta.get('tz_offset'), 3.0)

            if lat == 0.0 and lon == 0.0:
                lat, lon, tz = 41.0082, 28.9784, 3.0

            zodiac_type = chart_meta.get('zodiac_type') or chart_meta.get('zodiac') or 'Astronomik'
            h_sys_name = chart_meta.get('house_system') or chart_meta.get('house_system_name') or 'Placidus'
            house_code = ASTRO_MOTOR_NESNESİ.HOUSE_SYSTEMS.get(h_sys_name, 'P')

            try:
                _, calculated_data = ASTRO_MOTOR_NESNESİ.calculate_chart_data(
                    year, month, day, hour, minute, tz, lat, lon, None, house_code, zodiac_type
                )
                
                full_chart = chart_meta.copy()
                if calculated_data:
                    full_chart.update(calculated_data) 
                    full_chart['zodiac_type'] = zodiac_type
                
                return full_chart

            except Exception as inner_e:
                print(f"   ❌ MOTOR HATASI: {inner_e}")
                return chart_meta 

        # Verileri hazırla
        c1_full = get_or_calculate_full_data(raw_c1)
        c2_full = get_or_calculate_full_data(raw_c2)

        # --- KOMPOZİT İSE HESAPLA ---
        if calc_type == 'Kompozit':
            if hasattr(ASTRO_MOTOR_NESNESİ, 'calculate_synastry_chart'):
                wrapper1 = {'data': c1_full}
                wrapper2 = {'data': c2_full}
                _, result = ASTRO_MOTOR_NESNESİ.calculate_synastry_chart(wrapper1, wrapper2, c_type="Kompozit")
                
                if result:
                    composite_chart = {
                        'name': f"Kompozit: {c1_full['name']} & {c2_full['name']}",
                        'planets': result['planets'], 
                        'houses': c1_full.get('houses', {}),
                        'cusps': c1_full.get('cusps', {}),
                        'zodiac_type': c1_full.get('zodiac_type', 'Astronomik'),
                        'type': 'composite'
                    }
                    return jsonify({'success': True, 'is_composite': True, 'data': composite_chart})

        # SİNASTRİ İSE FRONTEND İÇİN PAKETLENECEK VERİ YAPISI
        # chart1 = DIŞ çark (2. seçilen, transit/değişken)
        # chart2 = İÇ çark (1. seçilen, natal/sabit)
        synastry_package = {
            'type': 'synastry',
            'chart1': c2_full,  # DIŞ çark (2. harita)
            'chart2': c1_full,  # İÇ çark (1. harita)
            'houses': c1_full.get('houses', {}),
            'cusps': c1_full.get('houses', {}),
            'boundaries': c1_full.get('boundaries', [])
        }
        
        return jsonify({
            'success': True,
            'is_composite': False,
            'data': synastry_package,
            'id1': id1, 'id2': id2
        })

    except Exception as e:
        print(f"GENEL SİNASTRİ HATASI: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/register_synastry_session', methods=['POST'])
def register_synastry_session():
    try:
        content = request.json
        print(f"\n🔍 DEBUG: Gelen JSON = {content}")
        
        full_data = content.get('data')
        calc_type = content.get('type')
        
        active_charts = session.get('active_charts', [])
        
        # KOMPOZİT HARİTA İSE (ID'siz gelebilir)
        if full_data and full_data.get('is_composite'):
            print("✅ KOMPOZİT HARİTA ALGILANDI - ID kontrolü atlanıyor")
            
            composite_data = full_data.get('data', {})
            composite_data['type'] = 'composite'
            
            new_chart_entry = {
                'id': len(active_charts) + 1,
                'type': 'composite',
                'saved_data': composite_data,
                'name': composite_data.get('name', 'Kompozit Harita'),
                'year': 2000,
                'month': 1,
                'day': 1,
                'hour': 12,
                'minute': 0,
                'tz_offset': 0.0,
                'lat': 0.0,
                'lon': 0.0,
                'location_name': 'Kompozit',
                'zodiac_type': composite_data.get('zodiac_type', 'Astronomik'),
                'house_system': 'P'
            }
            
            active_charts.insert(0, new_chart_entry)
            session['active_charts'] = active_charts
            session['current_chart_index'] = 0
            session['last_chart'] = composite_data
            session['last_report'] = "Kompozit Harita"
            session['current_chart_data'] = new_chart_entry
            
            print("✅ Kompozit harita kaydedildi!")
            return jsonify({'success': True, 'new_index': 0})
        
        # SİNASTRİ HARİTASI İSE (ID'ler gerekli)
        raw_id1 = content.get('id1')
        raw_id2 = content.get('id2')
        
        # Eğer üst seviyede yoksa, data içinde ara
        if raw_id1 is None and full_data:
            raw_id1 = full_data.get('id1')
        if raw_id2 is None and full_data:
            raw_id2 = full_data.get('id2')
        
        print(f"🔍 DEBUG: raw_id1={raw_id1}, raw_id2={raw_id2}")
        
        # ID kontrolü yap - None ise hata döndür
        if raw_id1 is None or raw_id2 is None:
            print(f"❌ HATA: ID'ler bulunamadı!")
            return jsonify({'success': False, 'error': 'Sinastri için harita ID\'leri eksik'})
        
        # İndeks sınırlarını kontrol et
        if raw_id1 < 0 or raw_id1 >= len(active_charts) or raw_id2 < 0 or raw_id2 >= len(active_charts):
            return jsonify({'success': False, 'error': 'Geçersiz harita indeksi'})
        
        # Session'daki haritaları ID'leri ile çekiyoruz
        c1_original = active_charts[raw_id1]
        c2_original = active_charts[raw_id2]
        
        # full_data içindeki 'data' objesini al (eğer varsa)
        actual_data = full_data.get('data', full_data)
        
        # Type bilgisini açıkça ekle
        if 'type' not in actual_data:
            actual_data['type'] = 'synastry' if calc_type == 'Sinastri' else 'composite'

        new_chart_entry = {
            'id': len(active_charts) + 1,
            'type': 'synastry' if calc_type == 'Sinastri' else 'composite',
            'saved_data': actual_data,
            'name': f"{calc_type}: {c1_original['name']} & {c2_original['name']}",
            
            # --- ZAMAN İLERLETMESİ İÇİN KRİTİK NATAL VERİLER ---
            'natal_meta_1': c1_original,
            'natal_meta_2': c2_original,
            
            # Layout.html'in tarih kutusu için ilerletilebilir değerler (2. kişinin zamanını alır)
            'year': c2_original.get('year', 2000), 
            'month': c2_original.get('month', 1), 
            'day': c2_original.get('day', 1),
            'hour': c2_original.get('hour', 12), 
            'minute': c2_original.get('minute', 0), 
            'tz_offset': c2_original.get('tz_offset', 0.0), 
            'lat': c2_original.get('lat', 0.0), 
            'lon': c2_original.get('lon', 0.0), 
            'location_name': c2_original.get('location_name', 'Sinastri Konumu'),
            'zodiac_type': 'Multi',
            'house_system': 'P'
        }
        
        # Listeye en başa ekle
        active_charts.insert(0, new_chart_entry)
        session['active_charts'] = active_charts
        session['current_chart_index'] = 0
        
        # last_chart'a type bilgisini de ekle
        session['last_chart'] = actual_data
        session['last_report'] = "Sinastri Analizi"
        session['current_chart_data'] = new_chart_entry
        
        return jsonify({'success': True, 'new_index': 0})
        
    except Exception as e:
        print(f"Session Kayıt Hatası: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/get_current_chart_data', methods=['GET'])
def api_get_current_chart_data():
    """
    Frontend'e güncel harita verisini döndürür (Swap sonrası kullanılır)
    """
    try:
        chart_data = session.get('last_chart', {})
        if chart_data:
            return jsonify({'success': True, 'chart_data': chart_data})
        else:
            return jsonify({'success': False, 'error': 'Harita verisi bulunamadı'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/swap_synastry', methods=['POST'])
def api_swap_synastry():
    """
    Sinastri haritalarında iç ve dış çarkı değiştir.
    SADECE chart1 ve chart2'nin YERİNİ DEĞİŞTİRİR.
    Dereceler, evler ve tüm veriler AYNEN KALIR.
    """
    try:
        active_charts = session.get('active_charts', [])
        current_index = session.get('current_chart_index', 0)
        
        if current_index < 0 or current_index >= len(active_charts):
            return jsonify({'success': False, 'error': 'Aktif harita bulunamadı.'})
        
        chart = active_charts[current_index]
        
        # Sadece sinastri haritaları için çalış
        if chart.get('type') not in ['synastry', 'composite', 'synastri']:
            return jsonify({'success': False, 'error': 'Bu işlem sadece sinastri haritaları için geçerlidir.'})
        
        # Saved data'yı al
        saved_data = chart.get('saved_data', {})
        if not saved_data:
            return jsonify({'success': False, 'error': 'Harita verileri eksik.'})
        
        print("\n🔄 SWAP İŞLEMİ BAŞLADI")
        print(f"Chart1 ÖNCE (DIŞ): {saved_data.get('chart1', {}).get('name')}")
        print(f"  → Güneş: {saved_data.get('chart1', {}).get('planets', {}).get('Güneş', ['?'])[0]}")
        print(f"Chart2 ÖNCE (İÇ): {saved_data.get('chart2', {}).get('name')}")
        print(f"  → Güneş: {saved_data.get('chart2', {}).get('planets', {}).get('Güneş', ['?'])[0]}")
        
        # MEVCUT DURUMU AL (Deep Copy ile)
        import copy
        chart1_backup = copy.deepcopy(saved_data.get('chart1'))
        chart2_backup = copy.deepcopy(saved_data.get('chart2'))
        
        if not chart1_backup or not chart2_backup:
            return jsonify({'success': False, 'error': 'Harita verileri eksik.'})
        
        # SADECE YER DEĞİŞTİR (Veriler aynen kalır)
        saved_data['chart1'] = chart2_backup  # DIŞ ÇARK ← eski iç çark
        saved_data['chart2'] = chart1_backup  # İÇ ÇARK ← eski dış çark
        
        print(f"\nChart1 SONRA (DIŞ): {saved_data.get('chart1', {}).get('name')}")
        print(f"  → Güneş: {saved_data.get('chart1', {}).get('planets', {}).get('Güneş', ['?'])[0]}")
        print(f"Chart2 SONRA (İÇ): {saved_data.get('chart2', {}).get('name')}")
        print(f"  → Güneş: {saved_data.get('chart2', {}).get('planets', {}).get('Güneş', ['?'])[0]}")
        
        # EVLERİ YENİ İÇ ÇARKTAN AL (chart2 artık iç çark)
        saved_data['houses'] = chart2_backup.get('houses', {})
        saved_data['cusps'] = chart2_backup.get('cusps', {})
        saved_data['boundaries'] = chart2_backup.get('boundaries', [])
        
        # META VERİLERİ DE DEĞİŞTİR
        meta1_backup = copy.deepcopy(chart.get('natal_meta_1'))
        meta2_backup = copy.deepcopy(chart.get('natal_meta_2'))
        
        if meta1_backup and meta2_backup:
            print(f"\nMeta1 ÖNCE: {chart.get('natal_meta_1', {}).get('name')}")
            print(f"Meta2 ÖNCE: {chart.get('natal_meta_2', {}).get('name')}")
            
            chart['natal_meta_1'] = meta2_backup
            chart['natal_meta_2'] = meta1_backup
            
            print(f"Meta1 SONRA: {chart.get('natal_meta_1', {}).get('name')}")
            print(f"Meta2 SONRA: {chart.get('natal_meta_2', {}).get('name')}")
        
        # LAYOUT TARİH BİLGİSİNİ GÜNCELLEME (KRİTİK DÜZELTME)
        # Layout.html'in tarih kutusundaki bilgiler swap sonrası doğru kalmalı
        # Ama YENİDEN HESAPLAMA TETİKLENMEMELİ!
        
        print(f"\nLayout Tarih ÖNCE: {chart.get('year')}/{chart.get('month')}/{chart.get('day')}")
        
        # UYARI: Tarih bilgisini değiştirmeyelim ki set_active_time tetiklenmesin!
        # Layout sadece gösterim için kullanıyor, hesaplama saved_data'dan yapılıyor.
        
        print(f"Layout Tarih SONRA: {chart.get('year')}/{chart.get('month')}/{chart.get('day')}")
        
        # GÜNCELLE
        chart['saved_data'] = saved_data
        active_charts[current_index] = chart
        session['active_charts'] = active_charts
        session['last_chart'] = saved_data
        session['current_chart_data'] = chart
        session.modified = True
        
        print("✅ SWAP TAMAMLANDI\n")
        
        return jsonify({'success': True, 'message': 'İç ve dış çarklar yer değiştirdi!'})
        
    except Exception as e:
        print(f"❌ Swap Hatası: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})
    
    # --- YARDIMCI FONKSİYON (api_calculate_progression DIŞINDA OLMALI) ---
def calculate_donum_noktasi_logic(natal_data, years_passed, direction="forward"):
    shift = years_passed if direction == "forward" else -years_passed
    advanced_data = natal_data.copy()
    
    # 1. Gezegenleri Kaydır
    new_planets = {}
    for p_id, p_info in natal_data['planets'].items():
        # p_info[0] ham boylamdır
        new_long = (p_info[0] + shift) % 360
        # Diğer verileri koru, sadece boylamı ve formatlanmış dereceyi güncelle
        p_list = list(p_info)
        p_list[0] = new_long
        # Buradaki get_relative_degree senin motorunda mevcut olan fonksiyondur
        from astro_core import get_relative_degree # Gerekirse import et
        _, _, fmt = get_relative_degree(new_long, "Astronomik")
        p_list[4] = fmt
        new_planets[p_id] = tuple(p_list)
    
    advanced_data['planets'] = new_planets

    # 2. Evleri Kaydır
    if 'houses' in natal_data:
        new_houses = {}
        for h_id, h_long in natal_data['houses'].items():
            new_houses[h_id] = (h_long + shift) % 360
        advanced_data['houses'] = new_houses
        advanced_data['cusps'] = new_houses

    return advanced_data

@app.route('/api/calculate_progression', methods=['POST'])
def api_calculate_progression():
    """
    İlerletilmiş Haritalar (Progression) - DRAKONİK DESTEKLİ HİBRİT MOD
    Örnek Senaryo:
    - Kaynak Harita (Sol): Astronomik Natal
    - Hedef Teknik (Sağ): Drakonik Güneş Yayı
    - Sonuç: İçeride Astronomik, Dışarıda Drakonik görünür.
    """
    try:
        data = request.get_json()
        chart_index = int(data.get('chart_index'))
        technique = data.get('technique', 'solar_arc')
        mode = data.get('mode', 'dual')
        
        # ✅ KRİTİK DÜZELTME: chart_type değişkenini tanımlıyoruz
        chart_type = technique

        # SAĞ MENÜDEN GELEN HEDEF ZODYAK (Örn: "Drakonik 29")
        target_zodiac = data.get('zodiac_type', 'Astronomik') 
        target_year = data.get('target_year')
        
        print(f"\n🔮 İLERLETİM: Teknik={technique}, Mod={mode}, Hedef Zodyak={target_zodiac}")
        
        # 1. HAM VERİYİ ÇEK
        active_charts = session.get('active_charts', [])
        if chart_index < 0 or chart_index >= len(active_charts):
            return jsonify({'success': False, 'error': 'Harita bulunamadı.'})
        
        source_chart = active_charts[chart_index]
        
        # Kaynak haritanın orijinal zodyak tipini sakla (Örn: Astronomik)
        source_zodiac_type = source_chart.get('zodiac_type', 'Astronomik')

        # Natal Ham Veriler
        natal_year = source_chart['year']
        natal_month = source_chart['month']
        natal_day = source_chart['day']
        natal_hour = source_chart['hour']
        natal_minute = source_chart['minute']
        natal_tz = float(source_chart.get('tz_offset', 0))
        natal_lat = float(source_chart.get('lat', 0))
        natal_lon = float(source_chart.get('lon', 0))
        house_code = ASTRO_MOTOR_NESNESİ.HOUSE_SYSTEMS.get(source_chart.get('house_system', 'Placidus'), 'P')

        # Hedef Zaman (Bugün veya seçilen tarih)
        now = datetime.now()
        if data.get('target_date'):
            try:
                dt_target = datetime.strptime(data.get('target_date'), '%Y-%m-%dT%H:%M')
                now = dt_target
            except: pass

        # --------------------------------------------------------------------
        # 2. ADIM: HESAPLAMA TABANI (TARGET ZODIAC İLE)
        # İlerletilmiş haritayı hesaplamak için, natalin HEDEF ZODYAKTAKİ (Drakonik) karşılığını bulmalıyız.
        # --------------------------------------------------------------------
        
        _, calculation_base_natal = ASTRO_MOTOR_NESNESİ.calculate_chart_data(
            natal_year, natal_month, natal_day, natal_hour, natal_minute,
            natal_tz, natal_lat, natal_lon, None, house_code, target_zodiac
        )
        
        if not calculation_base_natal:
            return jsonify({'success': False, 'error': 'Baz hesaplama hatası.'})

        # --------------------------------------------------------------------
        # 3. ADIM: İLERLETİLMİŞ HARİTAYI HESAPLA (Target Zodiac ile)
        # --------------------------------------------------------------------
        
        prog_data = None
        res_text = ""
        title = ""
        
        # Görüntüleme tarihleri
        prog_year, prog_month, prog_day = now.year, now.month, now.day
        prog_hour, prog_minute = now.hour, now.minute

        # A) TRANSİT (Anlık Drakonik Transit)
        if technique == 'transit':
            res_text, prog_data = ASTRO_MOTOR_NESNESİ.calculate_chart_data(
                now.year, now.month, now.day, now.hour, now.minute,
                natal_tz, natal_lat, natal_lon, None, house_code, target_zodiac
            )
            title = f"Transit ({now.day}.{now.month}.{now.year})"

        # B) DÖNÜM NOKTASI (KADER & KARMA - Sabit 1 Derece) 🌟
        elif technique in ['donum_noktasi_kader', 'donum_noktasi_karma']:
            # 1. Yaş Hesabı
            natal_dt = datetime(natal_year, natal_month, natal_day, natal_hour, natal_minute)
            total_seconds_lived = (now - natal_dt).total_seconds()
            age_in_years = total_seconds_lived / (365.242199 * 24 * 3600)
            
            # 2. Yön Belirle (Kader + / Karma -)
            direction = "forward" if technique == "donum_noktasi_kader" else "backward"
            shift = age_in_years if direction == "forward" else -age_in_years
            
            # 3. Hesaplama (Dışarıda tanımladığımız yardımcı fonksiyonu kullanır)
            # Not: calculation_base_natal yukarıda 2. adımda zaten hesaplanmıştı.
            prog_data = calculate_donum_noktasi_logic(calculation_base_natal, age_in_years, direction)
            
            title = "Dönüm Noktası (Kader)" if direction == "forward" else "Dönüm Noktası (Karma)"
            if prog_data:
                prog_data['display_date_str'] = now.strftime("%d.%m.%Y")

        elif technique == 'secondary':
            # 1. Hedef Zaman
            target_dt = now 
            title = f"İkincil İlerletim ({target_dt.year})"
            
            # 2. Doğum Zamanı
            natal_dt = datetime(natal_year, natal_month, natal_day, natal_hour, natal_minute)
            
            # 3. YAŞ HESABI (YIL OLARAK)
            total_seconds_lived = (target_dt - natal_dt).total_seconds()
            age_in_years = total_seconds_lived / (365.242199 * 24 * 3600)
            
            # 4. İLERLETİM TARİHİ HESABI (1 GÜN = 1 YIL)
            # timedelta kullanırken günün kesirli kısmını (saati) de ekleriz.
            # Bu, Ay ve hızlı gezegenlerin hassas konumu için gereklidir.
            prog_calc_dt = natal_dt + timedelta(days=age_in_years)
            
            print(f"DEBUG: Yaş={age_in_years:.4f}, Progres Tarih={prog_calc_dt}")

            # 5. HESAPLAMA (KRİTİK DÜZELTME BURADA) 🛠️
            # Gezegenler için: prog_calc_dt (İlerletilmiş tarih ve saat) kullanılır.
            # Evler (ASC) için: Standart "Mean" yöntemde DOĞUM SAATİ baz alınır.
            # Ancak çoğu motor tek bir saat aldığı için, burada 'natal_hour' ve 'natal_minute'
            # kullanarak ASC'nin çılgınca dönmesini (Quotidian etkisini) engelliyoruz.
            
            # NOT: Eğer motorun Julian Day (JD) kabul ediyorsa Ay için hassas ayar gerekebilir ama
            # aşağıdaki yöntem ASC kaymasını %100 çözer ve standart görüntüyü verir.
            
            res_text, prog_data = ASTRO_MOTOR_NESNESİ.calculate_chart_data(
                prog_calc_dt.year,    # Yıl değişti
                prog_calc_dt.month,   # Ay değişti
                prog_calc_dt.day,     # Gün değişti
                natal_hour,           # <--- SABİT KALMALI (Doğum Saati)
                natal_minute,         # <--- SABİT KALMALI (Doğum Dakikası)
                natal_tz,
                natal_lat, natal_lon, None, house_code, target_zodiac
            )
            
            # Ekranda hedef tarihi göster
            if prog_data:
                prog_data['display_date_str'] = target_dt.strftime("%d.%m.%Y")

        # B) SOLAR ARC (GÜNEŞ YAYI)
        else: 
            title = f"Güneş Yayı ({now.year})"
            
            # Solar Arc için özel fonksiyonunu çağır
            res_text, prog_data = ASTRO_MOTOR_NESNESİ.calculate_solar_arc_progression(
                natal_year, natal_month, natal_day, natal_hour, natal_minute, natal_tz,
                now.year, now.month, now.day,
                natal_lat, natal_lon, house_code, target_zodiac
            )
            
            # Zaman kapsülü için bugünün tarihini ekle
            if prog_data:
                prog_data['display_date_str'] = now.strftime("%d.%m.%Y")

        # Hata Kontrolü
        if not prog_data:
            return jsonify({'success': False, 'error': 'İlerletim hesaplanamadı: ' + str(res_text)})
        
        # İsimlendirme ve bitiş
        prog_data['name'] = f"{source_chart['name']} - {title}"
        prog_data['zodiac_type'] = target_zodiac

        # --- KOD BİTİŞİ --- 

        # --------------------------------------------------------------------
        # 4. ADIM: SONUCU PAKETLE (İÇ HARİTA ORİJİNAL KALSIN)
        # --------------------------------------------------------------------

        if mode == 'single':
            # TEKLİ MOD: Sadece Drakonik İlerletilmiş Harita
            new_chart = {
                'id': len(active_charts) + 1,
                'name': prog_data['name'],
                'year': prog_year, 'month': prog_month, 'day': prog_day,
                'hour': prog_hour, 'minute': prog_minute,
                'tz_offset': natal_tz, 'lat': natal_lat, 'lon': natal_lon,
                'location_name': source_chart.get('location_name', ''),
                'zodiac_type': target_zodiac,
                'house_system': source_chart.get('house_system', 'Placidus'),
                'type': f'progression_{technique}'
            }
            session['last_chart'] = prog_data
            
        else:
            # DUAL MOD (HİBRİT):
            # İç Çember: Kullanıcının soldan seçtiği harita (örn: Astronomik Natal)
            # Dış Çember: Sağdan seçtiği teknik (örn: Drakonik Solar Arc)
            
            # İç haritayı orijinal zodyak tipiyle hesapla/getir
            _, inner_chart_display = ASTRO_MOTOR_NESNESİ.calculate_chart_data(
                natal_year, natal_month, natal_day, natal_hour, natal_minute,
                natal_tz, natal_lat, natal_lon, None, house_code, source_zodiac_type
            )
            inner_chart_display['name'] = source_chart['name']
            inner_chart_display['zodiac_type'] = source_zodiac_type 
            
            synastry_package = {
                'type': 'synastry',
                'chart1': inner_chart_display,  # İÇ ÇARK (Orijinal Zodyak)
                'chart2': prog_data,            # DIŞ ÇARK (Hedef Zodyak - Drakonik)
                'houses': inner_chart_display.get('houses', {}),
                'cusps': inner_chart_display.get('cusps', {}),
                'boundaries': inner_chart_display.get('boundaries', [])
            }
            
            new_chart = {
                'id': len(active_charts) + 1,
                'type': 'synastry',
                'saved_data': synastry_package,
                'name': f"{title} (Dual)",
                
                # Natal Meta 1: İÇ HARİTA (Orijinal)
                'natal_meta_1': {
                    'name': inner_chart_display['name'], 
                    'year': natal_year, 'month': natal_month, 'day': natal_day,
                    'hour': natal_hour, 'minute': natal_minute, 'tz_offset': natal_tz,
                    'lat': natal_lat, 'lon': natal_lon, 
                    'zodiac_type': source_zodiac_type, 
                    'house_system': source_chart.get('house_system', 'Placidus')
                },
                
                # Natal Meta 2: DIŞ HARİTA (Drakonik İlerletim)
                'natal_meta_2': {
                    'name': title, 
                    'year': prog_year, 'month': prog_month, 'day': prog_day,
                    'hour': prog_hour, 'minute': prog_minute, 'tz_offset': natal_tz,
                    'lat': natal_lat, 'lon': natal_lon, 
                    'zodiac_type': target_zodiac, 
                    'house_system': source_chart.get('house_system', 'Placidus')
                },
                
                # Layout tarih kutusu verileri (Dış çarkın tarihi)
                'year': prog_year, 'month': prog_month, 'day': prog_day,
                'hour': prog_hour, 'minute': prog_minute,
                'tz_offset': natal_tz, 'lat': natal_lat, 'lon': natal_lon,
                'location_name': source_chart.get('location_name', ''),
                'zodiac_type': target_zodiac,
                'house_system': source_chart.get('house_system', 'Placidus')
            }
            session['last_chart'] = synastry_package

        # Ortak Kayıt
        active_charts.insert(0, new_chart)
        session['active_charts'] = active_charts
        session['current_chart_index'] = 0
        session['last_report'] = f"{title}\n\n{res_text}"
        session['current_chart_data'] = new_chart
        
        return jsonify({'success': True, 'message': 'Hesaplama başarılı!'})
    
        
    except Exception as e:
        print(f"❌ İlerletim Hatası: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/search_database', methods=['POST'])
def api_search_database():
    try:
        filters = request.get_json().get('filters', [])
        all_charts = load_json_data(DATA_FILE)
        matched_charts = []
        if not filters: return jsonify({'success': True, 'results': all_charts})
        
        for person in all_charts:
            try:
                house_code = 'P'; zodiac_type = 'Astronomik'
                tz = float(person.get('tz', 0))
                _, chart_data = ASTRO_MOTOR_NESNESİ.calculate_chart_data(person['year'], person['month'], person['day'], person['hour'], person['minute'], tz, person['lat'], person['lon'], None, house_code, zodiac_type)
                if not chart_data: continue
                is_match = True
                for f in filters:
                    target_planet = f.get('planet'); target_sign = f.get('sign'); target_deg = f.get('degree')
                    criteria_met = False
                    planets_to_check = []
                    if target_planet and target_planet != "Hepsi": planets_to_check.append(target_planet)
                    else: planets_to_check = list(chart_data['planets'].keys())
                    
                    for p_name in planets_to_check:
                        if p_name not in chart_data['planets']: continue
                        p_info = chart_data['planets'][p_name]; p_sign = p_info[3]; p_deg = int(p_info[2])
                        sign_match = True
                        if target_sign and target_sign != "Hepsi":
                            if p_sign != target_sign: sign_match = False
                        deg_match = True
                        if target_deg and target_deg != "":
                            if p_deg != int(target_deg): deg_match = False
                        if sign_match and deg_match: criteria_met = True; break
                    
                    if not criteria_met: is_match = False; break
                if is_match: matched_charts.append(person)
            except: pass
        return jsonify({'success': True, 'results': matched_charts, 'count': len(matched_charts)})
    except Exception as e: return jsonify({'success': False, 'error': str(e)})

@app.route('/', methods=['GET', 'POST'])
def home():
    active_tab = request.args.get('tab', 'natal') 
    if 'active_charts' not in session: session['active_charts'] = []
    
    # İLK AÇILIŞTA OTOMATİK ASTRONOMİK TRANSİT HARİTA YÜKLE
    if len(session['active_charts']) == 0 and request.method == 'GET':
        try:
            now = datetime.now()
            # İstanbul koordinatları
            lat, lon, tz = 41.0082, 28.9784, 3.0
            
            # Astronomik Transit harita hesapla
            res_text, t_data = ASTRO_MOTOR_NESNESİ.calculate_chart_data(
                now.year, now.month, now.day, now.hour, now.minute, 
                tz, lat, lon, None, 'P', 'Astronomik'
            )
            
            if t_data:
                t_data['map_type'] = 'transit'
                transit_chart = {
                    'name': f"Astronomik Transit ({now.day}.{now.month}.{now.year})", 
                    'year': now.year, 'month': now.month, 'day': now.day, 
                    'hour': now.hour, 'minute': now.minute, 
                    'tz_offset': tz, 'lat': lat, 'lon': lon, 
                    'location_name': 'İstanbul, Türkiye', 
                    'zodiac_type': 'Astronomik',
                    'house_system': 'Placidus', 
                    'id': 1, 
                    'type': 'transit',
                    'map_type': 'transit'
                }
                
                session['active_charts'] = [transit_chart]
                session['current_chart_index'] = 0
                session['last_chart'] = t_data
                session['last_report'] = f"ASTRONOMİK TRANSİT\n\n" + res_text
                session['current_chart_data'] = transit_chart
                active_tab = 'aktif'  # Aktif listesine yönlendir
        except Exception as e:
            print(f"Otomatik transit yükleme hatası: {e}")
    
    context = get_common_context()
    context['active_tab'] = active_tab

    if request.method == 'POST':
        if active_tab == 'natal':
            try:
                year = int(request.form.get('year')); month = int(request.form.get('month')); day = int(request.form.get('day'))
                hour = int(request.form.get('hour')); minute = int(request.form.get('minute'))
                tz_offset = float(request.form.get('tz_offset', 0)); lat = float(request.form.get('lat', 0)); lon = float(request.form.get('lon', 0))
                name = request.form.get('name'); loc_name = request.form.get('location_name')
                zodiac = request.form.get('zodiac_type', 'Astronomik')
                h_sys = request.form.get('house_system_name')
                house_code = ASTRO_MOTOR_NESNESİ.HOUSE_SYSTEMS.get(h_sys, 'P')
                res_text, chart_data = ASTRO_MOTOR_NESNESİ.calculate_chart_data(year, month, day, hour, minute, tz_offset, lat, lon, None, house_code, zodiac)
                if chart_data:
                    chart_data['map_type'] = 'natal'  # Harita tipini chart_data'ya da ekle
                    
                    # DÜZENLEME MODU KONTROLÜ
                    if session.get('edit_mode') and session.get('edit_index') is not None:
                        # DÜZENLEME MODU: Mevcut haritayı güncelle
                        edit_index = session.get('edit_index')
                        current_charts = session.get('active_charts', [])
                        
                        if 0 <= edit_index < len(current_charts):
                            # Mevcut haritayı güncelle (ID'yi koru)
                            existing_id = current_charts[edit_index].get('id', edit_index + 1)
                            updated_chart = {
                                'id': existing_id,
                                'name': name, 
                                'year': year, 
                                'month': month, 
                                'day': day, 
                                'hour': hour, 
                                'minute': minute, 
                                'tz_offset': tz_offset, 
                                'lat': lat, 
                                'lon': lon, 
                                'location_name': loc_name, 
                                'zodiac_type': zodiac, 
                                'house_system': h_sys, 
                                'type': 'natal', 
                                'map_type': 'natal'
                            }
                            
                            current_charts[edit_index] = updated_chart
                            session['active_charts'] = current_charts
                            session['current_chart_index'] = edit_index
                            session['current_chart_data'] = updated_chart
                        
                        # Düzenleme modunu kapat
                        session.pop('edit_mode', None)
                        session.pop('edit_index', None)
                    else:
                        # NORMAL MOD: Yeni harita ekle
                        new_chart = {
                            'id': len(session.get('active_charts', [])) + 1, 
                            'name': name, 
                            'year': year, 
                            'month': month, 
                            'day': day, 
                            'hour': hour, 
                            'minute': minute, 
                            'tz_offset': tz_offset, 
                            'lat': lat, 
                            'lon': lon, 
                            'location_name': loc_name, 
                            'zodiac_type': zodiac, 
                            'house_system': h_sys, 
                            'type': 'natal', 
                            'map_type': 'natal'
                        }
                        current_charts = session.get('active_charts', [])
                        current_charts.insert(0, new_chart)
                        session['active_charts'] = current_charts
                        session['current_chart_index'] = 0
                        session['current_chart_data'] = new_chart
                    
                    session['last_report'] = res_text
                    session['last_chart'] = chart_data
                    active_tab = 'aktif'
                else: session['report_error'] = res_text 
            except Exception as e: 
                session['report_error'] = f"Hata: {e}"; traceback.print_exc() 

        elif active_tab == 'instant_transit':
            try:
                # 1. Form Verilerini Al
                yr = int(request.form.get('bar_year')); mo = int(request.form.get('bar_month')); dy = int(request.form.get('bar_day'))
                hr = int(request.form.get('bar_hour')); mn = int(request.form.get('bar_minute'))
                lat = float(request.form.get('bar_lat', 0)); lon = float(request.form.get('bar_lon', 0)); tz = float(request.form.get('bar_tz', 0))
                
                # 2. Transit Tipini Kontrol Et (DÜZELTME BURADA)
                # Frontend'den "Drakonik" gelirse, motorun anladığı "Drakonik 28" (Yıldızsal) formatına çevir.
                raw_type = request.form.get('transit_type', 'Astronomik')
                
                if raw_type == 'Drakonik':
                    t_type = 'Drakonik 28'
                else:
                    t_type = raw_type

                # 3. Hesaplamayı Yap (t_type artık doğru formatta)
                res, t_data = ASTRO_MOTOR_NESNESİ.calculate_chart_data(yr, mo, dy, hr, mn, tz, lat, lon, None, 'P', t_type)
                
                if t_data:
                    t_data['map_type'] = 'transit'  # Harita tipini chart_data'ya ekle
                    transit_chart = {
                        'name': f"Transit ({dy}.{mo}.{yr} {hr}:{mn})", 
                        'year': yr, 'month': mo, 'day': dy, 'hour': hr, 'minute': mn, 
                        'tz_offset': tz, 'lat': lat, 'lon': lon, 
                        'location_name': request.form.get('bar_loc_name'), 
                        'zodiac_type': t_type,  # Düzelttiğimiz tipi kaydediyoruz
                        'house_system': 'Placidus (P)', 
                        'id': len(session.get('active_charts', [])) + 1, 
                        'type': 'transit',
                        'map_type': 'transit'
                    }
                    
                    current_charts = session.get('active_charts', [])
                    current_charts.insert(0, transit_chart)
                    session['active_charts'] = current_charts
                    session['current_chart_index'] = 0
                    session['last_chart'] = t_data
                    session['last_report'] = f"TRANSİT ({t_type})\n\n" + res
                    session['current_chart_data'] = transit_chart
                    active_tab = 'aktif'
            
            except Exception as e: session['report_error'] = str(e)
        
        elif active_tab == 'sinastri_compute':
             pass

        return redirect(url_for('home', tab=active_tab)) 

    # --- TRANSİT TAHMİNLERİNİ HESAPLA (DÜZELTİLDİ: GÜVENLİ DATA ÇEVRİMİ) ---
    if context.get('last_chart'):
        try:
            c_data = session.get('current_chart_data', {})
            
            # Veri var mı ve yıl bilgisi dolu mu kontrol et
            if c_data and c_data.get('year'):
                try:
                    # String gelme ihtimaline karşı int() çevrimi yapıyoruz
                    safe_year = int(c_data['year'])
                    safe_month = int(c_data['month'])
                    safe_day = int(c_data['day'])
                    safe_hour = int(c_data.get('hour', 12))
                    
                    c_date = datetime.datetime(safe_year, safe_month, safe_day, safe_hour, 0)
                    
                    # Tahmin Motorunu Çalıştır
                    preds = get_transit_predictions(c_date, context['last_chart']['planets'], ASTRO_MOTOR_NESNESİ)
                    context['transit_forecasts'] = preds
                    
                except ValueError as ve:
                    print(f"DEBUG HATA (Tarih Formatı): {ve}")
        except Exception as e:
            print(f"DEBUG HATA (Transit Motoru): {e}")

    context['last_chart'] = session.get('last_chart')
    context['report_error'] = session.pop('report_error', None)
    context['report_success'] = True if context['last_chart'] else False
    return render_template('layout.html', **context)

@app.route('/data')
def page_data():
    all_charts = load_json_data(DATA_FILE)
    selected_id = request.args.get('id', type=int); selected_chart = None; calculated_data_for_drawing = None
    if selected_id:
        selected_chart = next((c for c in all_charts if c['id'] == selected_id), None)
        if selected_chart:
            try:
                house_code = ASTRO_MOTOR_NESNESİ.HOUSE_SYSTEMS.get('Placidus', 'P'); z_type = "Astronomik" 
                _, calc_data = ASTRO_MOTOR_NESNESİ.calculate_chart_data(selected_chart['year'], selected_chart['month'], selected_chart['day'], selected_chart['hour'], selected_chart['minute'], float(selected_chart['tz']), float(selected_chart['lat']), float(selected_chart['lon']), None, house_code, z_type)
                calculated_data_for_drawing = calc_data
            except Exception as e: print(f"Harita hesaplama hatası: {e}")
    zodiac_order = ["Koç", "Boğa", "İkizler", "Yengeç", "Aslan", "Başak", "Terazi", "Akrep", "Yay", "Oğlak", "Kova", "Balık"]; chart_tree = {}
    for chart in all_charts:
        asc = chart.get('asc_sign', 'Bilinmeyen'); sun = chart.get('sun_sign', 'Bilinmeyen')
        if asc in ["Yılancı", "Ophiuchus"]: asc = "Akrep"
        if sun in ["Yılancı", "Ophiuchus"]: sun = "Akrep"
        asc_key = f"Yükselen {asc}"; sun_key = f"Güneş {sun}"
        if asc_key not in chart_tree: chart_tree[asc_key] = {}
        if sun_key not in chart_tree[asc_key]: chart_tree[asc_key][sun_key] = []
        chart_tree[asc_key][sun_key].append(chart)
    context = get_common_context(); context.update({ 'public_charts': all_charts, 'chart_tree': chart_tree, 'zodiac_order': zodiac_order, 'active_page': 'data', 'selected_chart': selected_chart, 'last_chart': calculated_data_for_drawing })
    return render_template('public_data.html', **context)

@app.route('/load_public_chart/<int:id>')
def load_public_chart(id):
    sel = next((c for c in load_json_data(DATA_FILE) if c['id'] == id), None)
    if sel:
        if 'active_charts' not in session: session['active_charts'] = []
        house_code = ASTRO_MOTOR_NESNESİ.HOUSE_SYSTEMS.get('Placidus', 'P'); z_type = "Astronomik"; lat = float(sel['lat']); lon = float(sel['lon']); tz = float(sel['tz'])
        res_text, chart_data = ASTRO_MOTOR_NESNESİ.calculate_chart_data(sel['year'], sel['month'], sel['day'], sel['hour'], sel['minute'], tz, lat, lon, None, house_code, z_type)
        if chart_data:
            new_chart = {'name': sel['name'], 'year': sel['year'], 'month': sel['month'], 'day': sel['day'], 'hour': sel['hour'], 'minute': sel['minute'], 'tz_offset': tz, 'lat': lat, 'lon': lon, 'location_name': sel.get('location_name', ''), 'zodiac_type': z_type, 'house_system': "Placidus", 'id': len(session.get('active_charts', [])) + 1, 'type': 'natal'}
            current_charts = session.get('active_charts', []); current_charts.insert(0, new_chart); session['active_charts'] = current_charts; session['current_chart_index'] = 0; session['last_report'] = res_text; session['last_chart'] = chart_data; session['current_chart_data'] = new_chart
    return redirect(url_for('home', tab='aktif'))

@app.route('/egitimler')
def page_education(): context = get_common_context(); context.update({'courses': load_json_data(COURSES_FILE), 'active_page': 'egitimler'}); return render_template('education.html', **context)

@app.route('/danismanliklar')
def page_consultations(): context = get_common_context(); context.update({'consultations': load_json_data(CONSULTATIONS_FILE), 'active_page': 'danismanliklar'}); return render_template('consultations.html', **context)

@app.route('/iletisim')
def page_contact(): context = get_common_context(); context.update({'contact': load_json_data(CONTACT_FILE), 'active_page': 'iletisim'}); return render_template('contact.html', **context)


@app.route('/set_active_time', methods=['POST'])
def set_active_time():
    active_charts = session.get('active_charts', [])
    idx = session.get('current_chart_index', 0)
    if not active_charts or idx >= len(active_charts): 
        return redirect(url_for('home', tab='aktif'))
    
    chart = active_charts[idx]
    try:
        # 1. Hedef zamanı takvimden al
        dt = datetime.strptime(request.form.get('target_date'), '%Y-%m-%dT%H:%M')
        return process_time_jump(dt, chart, idx, active_charts)
    except Exception as e:
        session['report_error'] = str(e)
        traceback.print_exc()
    return redirect(url_for('home', tab='aktif'))

@app.route('/adjust_active_time', methods=['POST']) 
def adjust_active_time():
    active_charts = session.get('active_charts', [])
    idx = session.get('current_chart_index', 0)
    if not active_charts or idx >= len(active_charts): 
        return redirect(url_for('home', tab='aktif'))
    
    chart = active_charts[idx]
    try:
        u = request.form.get('unit')
        a = int(request.form.get('amount', 1))
        
        # Mevcut zamanı al ve birim kadar kaydır
        dt = datetime(chart['year'], chart['month'], chart['day'], chart['hour'], chart['minute'])
        if u == 'minute': dt += relativedelta(minutes=a)
        elif u == 'hour': dt += relativedelta(hours=a)
        elif u == 'day': dt += relativedelta(days=a)
        elif u == 'week': dt += relativedelta(weeks=a)
        elif u == 'month': dt += relativedelta(months=a)
        elif u == 'year': dt += relativedelta(years=a)
        
        return process_time_jump(dt, chart, idx, active_charts)
    except Exception as e:
        session['report_error'] = str(e)
        traceback.print_exc()
    return redirect(url_for('home', tab='aktif'))

def process_time_jump(dt, chart, idx, active_charts):
    """
    Hem Single hem Dual ilerletim haritalarını tekniklerine göre günceller.
    HATA DÜZELTMESİ: Natal tarih ile Görüntülenen tarih (Display Date) ayrıştırıldı.
    """
    chart_type = str(chart.get('type', '')).lower()
    chart_name = chart.get('name', '').lower()
    
    # Teknik bayrakları
    is_secondary = 'secondary' in chart_type or 'secondary' in chart_name or 'ikincil' in chart_name
    is_solar_arc = 'solar_arc' in chart_type or 'solar_arc' in chart_name or 'güneş yayı' in chart_name
    is_kader = 'kader' in chart_type or 'kader' in chart_name
    is_karma = 'karma' in chart_type or 'karma' in chart_name
    
    # --- KRİTİK ADIM: NATAL TARİHİ KORUMA ---
    # Eğer haritada 'natal_year' yoksa (ilk kez açılıyorsa), mevcut 'year' bilgisini natal olarak etiketle.
    # Bu sayede 'year' değişse bile doğum tarihi sabit kalır.
    if 'natal_year' not in chart:
        chart['natal_year'] = chart['year']
        chart['natal_month'] = chart['month']
        chart['natal_day'] = chart['day']
        chart['natal_hour'] = chart['hour']
        chart['natal_minute'] = chart['minute']

        # --- 2. NATAL_DT TANIMLAMA (BURAYA EKLE) ---
    # Bu değişken hesaplamaların kök tarihidir.
    natal_dt = datetime(
        int(chart['natal_year']), 
        int(chart['natal_month']), 
        int(chart['natal_day']), 
        int(chart.get('natal_hour', 12)), 
        int(chart.get('natal_minute', 0))
    )

    res = ""
    final_data = None

    # --- SENARYO A: DUAL MOD (SİNASTRİ / COMPOSITE / İLERLETİM) ---
    if chart.get('type') in ['synastry'] or 'progression' in chart_type or 'saved_data' in chart:
        meta1 = chart.get('natal_meta_1')
        meta2 = chart.get('natal_meta_2')
        if not meta1 or not meta2: raise Exception("Meta verileri eksik.")

        # 1. İÇ ÇARK (Natal): Asla değişmez, sabit doğum verisi
        _, data1 = ASTRO_MOTOR_NESNESİ.calculate_chart_data(
            meta1['year'], meta1['month'], meta1['day'], meta1['hour'], meta1['minute'], 
            float(meta1['tz_offset']), float(meta1['lat']), float(meta1['lon']), None, 
            ASTRO_MOTOR_NESNESİ.HOUSE_SYSTEMS.get(meta1.get('house_system'), 'P'), 
            meta1.get('zodiac_type', 'Astronomik')
        )
        
        if is_secondary:
            # --- SECONDARY DÜZELTMESİ BAŞLANGIÇ ---
            
            # 1. Yaşanılan Gerçek Süreyi Bul (Hedef Tarih - Doğum Tarihi)
            time_lived = dt - natal_dt 
            lived_seconds = time_lived.total_seconds()
            
            # 2. Bu süreyi "İlerletilmiş Gün"e çevir (Day for a Year)
            # Formül: (Yaşanılan Saniye / Bir Yıldaki Saniye) = Eklenecek Gün Sayısı
            days_to_add = lived_seconds / SECONDS_IN_YEAR
            
            # 3. İlerletilmiş Tarihi (Progressed Date) Bul
            # Doğum tarihine hesaplanan gün sayısını ekle
            prog_dt = natal_dt + timedelta(days=days_to_add)
            
            print(f"DEBUG SEC: Hedef={dt}, Natal={natal_dt}, Eklenecek Gün={days_to_add:.4f}, ProgTarih={prog_dt}")

            # 4. Motoru İlerletilmiş Tarih ile Çalıştır
            res, data2 = ASTRO_MOTOR_NESNESİ.calculate_chart_data(
                prog_dt.year, prog_dt.month, prog_dt.day, prog_dt.hour, prog_dt.minute, 
                float(meta1['tz_offset']), float(meta2['lat']), float(meta2['lon']), None, 
                ASTRO_MOTOR_NESNESİ.HOUSE_SYSTEMS.get(meta2.get('house_system'), 'P'), 
                meta2.get('zodiac_type', 'Astronomik')
            )
            
            # İsimlendirme ve Gösterim
            data2['name'] = f"İkincil İlerletim ({dt.year})"
            data2['display_date_str'] = dt.strftime("%d.%m.%Y") # Ekranda hedef tarihi (2026) göster
            
        elif is_solar_arc:
            # Solar Arc direkt motor fonksiyonunu çağırır
            res, data2 = ASTRO_MOTOR_NESNESİ.calculate_solar_arc_progression(
                meta1['year'], meta1['month'], meta1['day'], meta1['hour'], meta1['minute'], float(meta1['tz_offset']),
                dt.year, dt.month, dt.day, # Hedef Tarih
                float(meta2['lat']), float(meta2['lon']), 
                ASTRO_MOTOR_NESNESİ.HOUSE_SYSTEMS.get(meta2.get('house_system'), 'P'), 
                meta2.get('zodiac_type', 'Astronomik')
            )
            data2['name'] = f"Güneş Yayı ({dt.year})"
            
        else:
            # Standart Transit (Dış çark o anki gökyüzü)
            res, data2 = ASTRO_MOTOR_NESNESİ.calculate_chart_data(
                dt.year, dt.month, dt.day, dt.hour, dt.minute, 
                float(meta2['tz_offset']), float(meta2['lat']), float(meta2['lon']), None, 
                ASTRO_MOTOR_NESNESİ.HOUSE_SYSTEMS.get(meta2.get('house_system'), 'P'), 
                meta2.get('zodiac_type', 'Astronomik')
            )
            data2['name'] = f"Transit ({dt.strftime('%d.%m.%Y')})"
        
        # Ekrandaki tarihi güncelle (Transit tarihi)
        data2['display_date_str'] = dt.strftime("%d.%m.%Y %H:%M")
        data1['name'] = meta1['name']
        
        synastry_package = {
            'type': 'synastry', 'chart1': data1, 'chart2': data2,
            'houses': data1.get('houses', {}), 'cusps': data1.get('cusps', {}), 'boundaries': data1.get('boundaries', [])
        }
        chart['saved_data'] = synastry_package
        final_data = synastry_package
        
        # Meta2'yi güncelle (Transit konumu olarak kalsın diye)
        chart['natal_meta_2']['year'] = dt.year
        chart['natal_meta_2']['month'] = dt.month
        chart['natal_meta_2']['day'] = dt.day
        chart['natal_meta_2']['hour'] = dt.hour
        chart['natal_meta_2']['minute'] = dt.minute

        # --- YENİ: DÖNÜM NOKTASI ZAMAN ATLAMASI ---
    elif is_kader or is_karma:
        # 1. Yaşanılan Süreyi (Yıl) Hesapla
        natal_dt = datetime(chart.get('natal_year', chart['year']), 
                            chart.get('natal_month', chart['month']), 
                            chart.get('natal_day', chart['day']), 
                            chart.get('natal_hour', chart['hour']), 
                            chart.get('natal_minute', chart['minute']))
        
        age_in_years = (dt - natal_dt).days / 365.2425
        direction = "forward" if is_kader else "backward"
        
        # 2. İlgili baz veriyi al (Dual ise meta1, Single ise chart verisi)
        # Not: calculation_base_natal yukarıda 'secondary' kısmında yaptığın gibi 
        # natal koordinatlarda ve hedef zodyakta önceden hesaplanmış olmalı.
        _, base_natal = ASTRO_MOTOR_NESNESİ.calculate_chart_data(
            natal_dt.year, natal_dt.month, natal_dt.day, natal_dt.hour, natal_dt.minute,
            float(chart['tz_offset']), float(chart['lat']), float(chart['lon']), None, 
            ASTRO_MOTOR_NESNESİ.HOUSE_SYSTEMS.get(chart.get('house_system'), 'P'), 
            chart.get('zodiac_type', 'Astronomik')
        )

        # 3. Matematiksel Kaydırmayı Uygula (1 Yıl = 1 Derece)
        data2 = calculate_donum_noktasi_logic(base_natal, age_in_years, direction)
        
        title_suffix = "Kader" if is_kader else "Karma"
        data2['name'] = f"Dönüm Noktası ({title_suffix} - {dt.year})"
        data2['display_date_str'] = dt.strftime("%d.%m.%Y")
        
        # Dual mod paketlemesi için final_data ata
        final_data = data2

    # --- SENARYO B: SINGLE MOD (TEKLİ HARİTA) ---
    else:
        # Natal bilgileri ARTIK GÜVENLİ: 'natal_year' anahtarından alıyoruz.
        # Eğer natal_year yoksa, chart['year'] kullanılır (fallback)
        n_year = chart.get('natal_year', chart['year'])
        n_month = chart.get('natal_month', chart['month'])
        n_day = chart.get('natal_day', chart['day'])
        n_hour = chart.get('natal_hour', chart['hour'])
        n_min = chart.get('natal_minute', chart['minute'])

        natal_dt = datetime(n_year, n_month, n_day, n_hour, n_min)

        if is_secondary:
            # Single Secondary
            age_seconds = (dt - natal_dt).total_seconds()
            days_to_add = age_seconds / 31556925.0
            prog_dt = natal_dt + timedelta(days=days_to_add)

            res, final_data = ASTRO_MOTOR_NESNESİ.calculate_chart_data(
                prog_dt.year, prog_dt.month, prog_dt.day, prog_dt.hour, prog_dt.minute,
                float(chart['tz_offset']), float(chart['lat']), float(chart['lon']), None,
                ASTRO_MOTOR_NESNESİ.HOUSE_SYSTEMS.get(chart.get('house_system'), 'P'), 
                chart.get('zodiac_type', 'Astronomik')
            )
            final_data['display_date_str'] = dt.strftime("%d.%m.%Y (Sec)")
            final_data['name'] = f"{chart_name} (Sec. {dt.year})"
            
        elif is_solar_arc:
            # Single Solar Arc
            res, final_data = ASTRO_MOTOR_NESNESİ.calculate_solar_arc_progression(
                n_year, n_month, n_day, n_hour, n_min, float(chart['tz_offset']),
                dt.year, dt.month, dt.day,
                float(chart['lat']), float(chart['lon']), 
                ASTRO_MOTOR_NESNESİ.HOUSE_SYSTEMS.get(chart.get('house_system'), 'P'), 
                chart.get('zodiac_type', 'Astronomik')
            )
            final_data['display_date_str'] = dt.strftime("%d.%m.%Y (SA)")
            final_data['name'] = f"{chart_name} (SA {dt.year})"

        else:
            # Standart Transit (Single Mode'da Transit Harita olarak davranır)
            res, final_data = ASTRO_MOTOR_NESNESİ.calculate_chart_data(
                dt.year, dt.month, dt.day, dt.hour, dt.minute, 
                float(chart['tz_offset']), float(chart['lat']), float(chart['lon']), None, 
                ASTRO_MOTOR_NESNESİ.HOUSE_SYSTEMS.get(chart.get('house_system'), 'P'), 
                chart.get('zodiac_type', 'Astronomik')
            )
            final_data['display_date_str'] = dt.strftime("%d.%m.%Y")


    # --- KAYDETME ---
    # Ekranda "Şu an hangi zamandayız?" bilgisini tutmak için 'year/month' güncellenir.
    # AMA 'natal_year' vb. asla dokunulmaz, böylece kök veri bozulmaz.
    chart.update({'year': dt.year, 'month': dt.month, 'day': dt.day, 'hour': dt.hour, 'minute': dt.minute})
    
    active_charts[idx] = chart
    session['active_charts'] = active_charts
    session['last_chart'] = final_data
    session['last_report'] = res
    session['current_chart_data'] = chart
    session.modified = True
    
    return redirect(url_for('home', tab='aktif'))

@app.route('/set_active_chart/<int:index>')
def set_active_chart(index):
    al = session.get('active_charts', [])
    if al and 0 <= index < len(al):
        sel = al[index]
        session['current_chart_index'] = index
        session['current_chart_data'] = sel
        if sel.get('type') in ['synastry', 'composite'] or 'saved_data' in sel:
            session['last_chart'] = sel.get('saved_data', {})
        else:
            txt, data = ASTRO_MOTOR_NESNESİ.calculate_chart_data(
                sel['year'], sel['month'], sel['day'], sel['hour'], sel['minute'], 
                float(sel['tz_offset']), float(sel['lat']), float(sel['lon']), None, 
                ASTRO_MOTOR_NESNESİ.HOUSE_SYSTEMS.get(sel.get('house_system'), 'P'), 
                sel.get('zodiac_type', 'Astronomik')
            )
            session['last_chart'] = data
            session['last_report'] = txt
        session.modified = True
    return redirect(url_for('home', tab='aktif'))

@app.route('/api/load_chart/<int:index>')
def api_load_chart(index):
    """AJAX ile harita yükle - sayfa yenilenmeden"""
    try:
        al = session.get('active_charts', [])
        if not al or index < 0 or index >= len(al):
            return jsonify({'success': False, 'error': 'Harita bulunamadı'})
        
        sel = al[index]
        session['current_chart_index'] = index
        session['current_chart_data'] = sel
        
        if sel.get('type') in ['synastry', 'composite'] or 'saved_data' in sel:
            chart_data = sel.get('saved_data', {})
            session['last_chart'] = chart_data
            report_text = "Sinastri/Kompozit Harita"
        else:
            txt, data = ASTRO_MOTOR_NESNESİ.calculate_chart_data(
                sel['year'], sel['month'], sel['day'], sel['hour'], sel['minute'], 
                float(sel['tz_offset']), float(sel['lat']), float(sel['lon']), None, 
                ASTRO_MOTOR_NESNESİ.HOUSE_SYSTEMS.get(sel.get('house_system'), 'P'), 
                sel.get('zodiac_type', 'Astronomik')
            )
            chart_data = data
            report_text = txt
            session['last_chart'] = data
            session['last_report'] = txt
        
        session.modified = True
        
        return jsonify({
            'success': True,
            'chart_data': chart_data,
            'chart_info': sel
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ============================================================================
# 🔮 DANIŞMANLIK PANELİ ROTALARI (Öneri 2)
# ============================================================================

@app.route('/danismanlik')
def danismanlik_page():
    # Ana sistemdeki motor nesnesinin adı ASTRO_MOTOR_NESNESİ olduğu için onu gönderiyoruz
    active_charts = session.get('active_charts', [])
    last_chart = session.get('last_chart', None)
    
    return render_template(
        "danismanlik_layout.html", 
        active_page="natal",
        motor=ASTRO_MOTOR_NESNESİ,      # İsmi düzelttik
        active_charts=active_charts,
        last_chart=last_chart,
        is_logged_in=True,
        display_name=session.get('display_name', 'Kullanıcı'),
        active_tab=request.args.get('tab', 'natal')
    )

# ============================================================================
# 🔮 DANIŞMANLIK ÜST MENÜ SİSTEMİ (MODÜLER YAPI)
# ============================================================================

@app.route('/danismanlik/natal')
def danismanlik_natal():
    context = get_common_context() # Ana sistemdeki verileri çek (is_logged_in vb.)
    return render_template("danismanlik_layout.html", 
                           active_page="natal", 
                           motor=ASTRO_MOTOR_NESNESİ,
                           **context)

@app.route('/danismanlik/ongoru')
def danismanlik_ongoru():
    context = get_common_context()
    return render_template("danismanlik_layout.html", 
                           active_page="ongoru", 
                           motor=ASTRO_MOTOR_NESNESİ,
                           **context)

@app.route('/danismanlik/sinastri')
def danismanlik_sinastri_analiz():
    context = get_common_context()
    # Sol menüdeki sinastri ile karışmaması için active_page'i farklı isimlendiriyoruz
    return render_template("danismanlik_layout.html", 
                           active_page="sinastri_analiz", 
                           motor=ASTRO_MOTOR_NESNESİ,
                           **context)

@app.route('/danismanlik/reenkarnasyon')
def danismanlik_reenkarnasyon_analiz():
    context = get_common_context()
    return render_template("danismanlik_layout.html", 
                           active_page="reenkarnasyon", 
                           motor=ASTRO_MOTOR_NESNESİ,
                           **context)

@app.route('/delete_active_chart/<int:index>')
def delete_active_chart(index):
    active_charts = session.get('active_charts', [])
    
    if 0 <= index < len(active_charts):
        # 1. Listeden sil
        del active_charts[index]
        
        # 2. Session'ı güncelle
        session['active_charts'] = active_charts
        session.modified = True 
        
        # Eğer silinen harita aktif haritaysa veya liste kısaldıysa indeksleri düzelt
        current_index = session.get('current_chart_index', 0)
        
        # Eğer şu anki indeks, yeni listenin boyunu aşıyorsa (örn: sonuncuyu sildik)
        if current_index >= len(active_charts):
            session['current_chart_index'] = max(0, len(active_charts) - 1)
        
        # Eğer liste tamamen boşaldıysa, ekrandaki haritayı temizle
        if len(active_charts) == 0:
            session.pop('last_chart', None)
            session.pop('last_report', None)
            session.pop('current_chart_data', None)
            
        # Eğer silinen harita, tam olarak ekranda açık olan haritaysa
        elif current_index == index:
            # Yeni aktif haritayı (veya yerine geçeni) yükle ki ekran boş kalmasın
            new_index = min(index, len(active_charts) - 1)
            if new_index >= 0:
                return redirect(url_for('set_active_chart', index=new_index))
    
    return redirect(url_for('home', tab='aktif'))

@app.route('/bulk_delete_charts', methods=['POST'])
def bulk_delete_charts():
    """Toplu harita silme - Büyükten küçüğe sıralı indeksleri siler"""
    try:
        data = request.get_json()
        indices = data.get('indices', [])
        
        if not indices:
            return jsonify({'success': False, 'error': 'Silinecek harita seçilmedi'})
        
        active_charts = session.get('active_charts', [])
        
        # Büyükten küçüğe sıralı geldiği için direkt silebiliriz
        for index in indices:
            if 0 <= index < len(active_charts):
                del active_charts[index]
        
        # Session'ı güncelle
        session['active_charts'] = active_charts
        session.modified = True
        
        # Eğer liste boşaldıysa, session'ı temizle
        if len(active_charts) == 0:
            session.pop('last_chart', None)
            session.pop('last_report', None)
            session.pop('current_chart_data', None)
            session['current_chart_index'] = 0
        else:
            # Aktif indeksi düzelt
            current_index = session.get('current_chart_index', 0)
            if current_index >= len(active_charts):
                session['current_chart_index'] = len(active_charts) - 1
        
        return jsonify({'success': True, 'message': f'{len(indices)} harita silindi'})
        
    except Exception as e:
        print(f"Toplu silme hatası: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/edit_active_chart/<int:index>')
def edit_active_chart(index):
    if 'active_charts' in session and len(session['active_charts']) > index:
        session['current_chart_data'] = session['active_charts'][index]
        session['edit_mode'] = True  # Düzenleme modu aktif
        session['edit_index'] = index  # Hangi harita düzenleniyor
        session.modified = True
        return redirect(url_for('home', tab='natal'))
    return redirect(url_for('home', tab='aktif'))

# Route kaldırıldı - Kullanıcı sistemi artık yok

# Route kaldırıldı - Kullanıcı sistemi artık yok

# Route kaldırıldı - Kullanıcı sistemi artık yok

@app.route('/logout')
def logout():
    # Session'ı temizle
    session.clear()
    return redirect(url_for('home'))

# ============================================================================
# 🔄 AJAX API: SAYFA YENİLEMESİZ HARİTA HESAPLAMA
# ============================================================================

# ============================================================================
# 🔄 AJAX API: SAYFA YENİLEMESİZ HARİTA HESAPLAMA (GÜNCELLENDİ)
# ============================================================================

@app.route('/api/calculate_natal', methods=['POST'])
def api_calculate_natal():
    """AJAX ile natal harita hesapla - sayfa yenilenmeden"""
    try:
        # 1. GÜVENLİK ZIRHI: silent=True ile Flask'ın HTML hata sayfası atmasını engelliyoruz
        data = request.get_json(silent=True)
        if data is None:
            data = request.form # JSON başarısız olursa standart Form verisini dene

        if not data or 'year' not in data:
            return jsonify({'success': False, 'error': 'Frontend veri gönderemedi veya format hatalı.'})

        year = int(data.get('year'))
        month = int(data.get('month'))
        day = int(data.get('day'))
        hour = int(data.get('hour'))
        minute = int(data.get('minute'))
        tz_offset = float(data.get('tz_offset', 0))
        lat = float(data.get('lat', 0))
        lon = float(data.get('lon', 0))
        name = data.get('name', 'Bilinmeyen')
        location_name = data.get('location_name', '')
        zodiac_type = data.get('zodiac_type', 'Astronomik')
        house_system = data.get('house_system', 'Placidus')
        
        house_code = ASTRO_MOTOR_NESNESİ.HOUSE_SYSTEMS.get(house_system, 'P')
        
        # Harita hesapla
        res_text, chart_data = ASTRO_MOTOR_NESNESİ.calculate_chart_data(
            year, month, day, hour, minute, tz_offset, lat, lon, 
            None, house_code, zodiac_type
        )
        
        if not chart_data:
            return jsonify({'success': False, 'error': 'Harita motoru sonuç üretemedi.'})
        
        chart_data['map_type'] = 'natal'
        
        # Düzenleme modu kontrolü
        if session.get('edit_mode') and session.get('edit_index') is not None:
            edit_index = session.get('edit_index')
            active_charts = session.get('active_charts', [])
            
            if 0 <= edit_index < len(active_charts):
                existing_id = active_charts[edit_index].get('id', edit_index + 1)
                updated_chart = {
                    'id': existing_id,
                    'name': name,
                    'year': year, 'month': month, 'day': day,
                    'hour': hour, 'minute': minute,
                    'tz_offset': tz_offset, 'lat': lat, 'lon': lon,
                    'location_name': location_name,
                    'zodiac_type': zodiac_type,
                    'house_system': house_system,
                    'type': 'natal',
                    'map_type': 'natal'
                }
                
                active_charts[edit_index] = updated_chart
                session['active_charts'] = active_charts
                session['current_chart_index'] = edit_index
                session['current_chart_data'] = updated_chart
            
            session.pop('edit_mode', None)
            session.pop('edit_index', None)
        else:
            # Yeni harita ekle
            new_chart = {
                'id': len(session.get('active_charts', [])) + 1,
                'name': name,
                'year': year, 'month': month, 'day': day,
                'hour': hour, 'minute': minute,
                'tz_offset': tz_offset, 'lat': lat, 'lon': lon,
                'location_name': location_name,
                'zodiac_type': zodiac_type,
                'house_system': house_system,
                'type': 'natal',
                'map_type': 'natal'
            }
            
            active_charts = session.get('active_charts', [])
            active_charts.insert(0, new_chart)
            session['active_charts'] = active_charts
            session['current_chart_index'] = 0
            session['current_chart_data'] = new_chart
        
        session['last_report'] = res_text
        session['last_chart'] = chart_data
        session.modified = True
        
        return jsonify({
            'success': True,
            'chart_data': chart_data,
            'message': 'Harita başarıyla hesaplandı'
        })
        
    except Exception as e:
        print(f"API Natal Hatası: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/calculate_transit', methods=['POST'])
def api_calculate_transit():
    """AJAX ile transit harita hesapla - sayfa yenilenmeden"""
    try:
        # 1. GÜVENLİK ZIRHI:
        data = request.get_json(silent=True)
        if data is None:
            data = request.form

        if not data or 'year' not in data:
            return jsonify({'success': False, 'error': 'Frontend veri gönderemedi veya format hatalı.'})
        
        year = int(data.get('year'))
        month = int(data.get('month'))
        day = int(data.get('day'))
        hour = int(data.get('hour'))
        minute = int(data.get('minute'))
        tz_offset = float(data.get('tz_offset', 0))
        lat = float(data.get('lat', 0))
        lon = float(data.get('lon', 0))
        location_name = data.get('location_name', '')
        
        raw_type = data.get('transit_type', 'Astronomik')
        
        # Drakonik düzeltmesi
        if raw_type == 'Drakonik':
            transit_type = 'Drakonik 28'
        else:
            transit_type = raw_type
        
        # Harita hesapla
        res_text, chart_data = ASTRO_MOTOR_NESNESİ.calculate_chart_data(
            year, month, day, hour, minute, tz_offset, lat, lon,
            None, 'P', transit_type
        )
        
        if not chart_data:
            return jsonify({'success': False, 'error': 'Transit hesaplanamadı'})
        
        chart_data['map_type'] = 'transit'
        
        transit_chart = {
            'name': f"Transit ({day}.{month}.{year} {hour}:{minute})",
            'year': year, 'month': month, 'day': day,
            'hour': hour, 'minute': minute,
            'tz_offset': tz_offset, 'lat': lat, 'lon': lon,
            'location_name': location_name,
            'zodiac_type': transit_type,
            'house_system': 'Placidus',
            'id': len(session.get('active_charts', [])) + 1,
            'type': 'transit',
            'map_type': 'transit'
        }
        
        active_charts = session.get('active_charts', [])
        active_charts.insert(0, transit_chart)
        session['active_charts'] = active_charts
        session['current_chart_index'] = 0
        session['last_chart'] = chart_data
        session['last_report'] = f"TRANSİT ({transit_type})\n\n{res_text}"
        session['current_chart_data'] = transit_chart
        session.modified = True
        
        return jsonify({
            'success': True,
            'chart_data': chart_data,
            'message': 'Transit başarıyla hesaplandı'
        })
        
    except Exception as e:
        print(f"API Transit Hatası: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/get_active_charts', methods=['GET'])
def api_get_active_charts():
    """Aktif haritalar listesini JSON olarak döndür"""
    try:
        active_charts = session.get('active_charts', [])
        current_index = session.get('current_chart_index', 0)
        
        return jsonify({
            'success': True,
            'charts': active_charts,
            'current_index': current_index
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    # use_reloader=False eklemek bu çakışmayı önler
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
