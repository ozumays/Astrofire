from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
from flask_session import Session 
import os 
import json
import datetime 
from datetime import timedelta 
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
import user_manager

app = Flask(__name__)
app.secret_key = 'super_secret_astro_key_for_session' 
app.jinja_env.add_extension('jinja2.ext.do')

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
# 🚀 EPHEMERIS AYARLARI
# ============================================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
ephe_path = os.path.join(current_dir, 'ephe')

has_sepl = os.path.exists(os.path.join(ephe_path, 'sepl_18.se1'))
has_semo = os.path.exists(os.path.join(ephe_path, 'semo_18.se1'))

if has_sepl and has_semo:
    print(f"✅ Ephemeris Dosyaları Bulundu: {ephe_path}")
    swe.set_ephe_path(ephe_path)
    CALC_MODE = swe.FLG_SWIEPH | swe.FLG_SPEED 
else:
    print(f"⚠️ Ephemeris Dosyaları Eksik. Moshier moduna geçiliyor.")
    swe.set_ephe_path('') 
    CALC_MODE = swe.FLG_MOSEPH 

# ============================================================================
# 🚀 SESSION VE DOSYA AYARLARI
# ============================================================================
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flask_session')
Session(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER_COURSES = os.path.join(BASE_DIR, 'static', 'uploads', 'courses')
UPLOAD_FOLDER_CONTACT = os.path.join(BASE_DIR, 'static', 'uploads', 'contact')
UPLOAD_FOLDER_CHARTS = os.path.join(BASE_DIR, 'static', 'uploads', 'charts')

app.config['UPLOAD_FOLDER_COURSES'] = UPLOAD_FOLDER_COURSES
app.config['UPLOAD_FOLDER_CONTACT'] = UPLOAD_FOLDER_CONTACT
app.config['UPLOAD_FOLDER_CHARTS'] = UPLOAD_FOLDER_CHARTS

os.makedirs(UPLOAD_FOLDER_COURSES, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_CONTACT, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_CHARTS, exist_ok=True)

ADMIN_EMAILS = ["astrozumaay@hotmail.com"] 
ADMIN_PASSWORD = "Ckv12wj1G.."  # <-- BURAYI KENDİNE GÖRE DEĞİŞTİR
DATA_FILE = 'data_public_charts.json'       
COURSES_FILE = 'data_courses.json'
CONTACT_FILE = 'data_contact.json'

# --- YARDIMCI FONKSİYONLAR ---
def load_json_data(filename):
    if not os.path.exists(filename): return {} if filename == CONTACT_FILE else []
    try: 
        with open(filename, 'r', encoding='utf-8') as f: return json.load(f)
    except: return {} if filename == CONTACT_FILE else []

def save_json_data(filename, data):
    with open(filename, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=4)

def get_current_user_email(): return session.get('logged_in_email')
def get_user_display_name(email):
    user_data = user_manager.get_user_data_by_email(email)
    return user_data['name'] if user_data else "Misafir"

def get_common_context():
    email = get_current_user_email()
    folder_list = user_manager.get_user_folder_list(email) if email else ["Genel"]
    return {
        'user_email': email, 'is_logged_in': bool(email),
        'display_name': get_user_display_name(email) if email else None,
        'motor': ASTRO_MOTOR_NESNESİ,
        'active_charts': session.get('active_charts', []),
        'current_chart_data': session.get('current_chart_data'),
        'user_folders': folder_list,
        'is_admin': lambda: email in ADMIN_EMAILS,
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
    if session.get('admin_access') == True: return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        if request.form.get('email') in ADMIN_EMAILS:
            success, _ = user_manager.try_login(request.form.get('email'), request.form.get('password'), False)
            if success: session['admin_access'] = True; return redirect(url_for('admin_dashboard'))
            else: return render_template('admin_login.html', error="Hatalı şifre!")
        else: return render_template('admin_login.html', error="Yetkisiz erişim!")
    return render_template('admin_login.html')

@app.route('/yonetim/dashboard')
def admin_dashboard():
    if not session.get('admin_access'): return redirect(url_for('admin_login_page'))
    return render_template('admin_dashboard.html', users=user_manager.get_all_users(), public_charts=load_json_data(DATA_FILE), courses=load_json_data(COURSES_FILE), contact=load_json_data(CONTACT_FILE))

@app.route('/yonetim/logout')
def admin_logout():
    session.pop('admin_access', None)
    return redirect(url_for('admin_login_page'))

@app.route('/admin/update_contact', methods=['POST'])
def admin_update_contact():
    if not session.get('admin_access'): return redirect(url_for('admin_login_page'))
    cd = load_json_data(CONTACT_FILE); 
    if not isinstance(cd, dict): cd = {}
    cd.update({k: request.form.get(k) for k in ['bio','phone','email','instagram','youtube','website']})
    if 'photo' in request.files:
        f = request.files['photo']
        if f and f.filename != '': 
            fn = secure_filename(f.filename); un = f"profile_{random.randint(1000,9999)}_{fn}"; f.save(os.path.join(app.config['UPLOAD_FOLDER_CONTACT'], un)); cd['photo'] = un
    save_json_data(CONTACT_FILE, cd)
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add_chart', methods=['POST'])
def admin_add_chart():
    if not session.get('admin_access'): return redirect(url_for('admin_login_page'))
    try:
        name = request.form.get('name'); category_input = request.form.get('category', 'Genel')
        bio = request.form.get('bio', ''); location_name = request.form.get('location_name', '')
        day = int(request.form.get('day')); month = int(request.form.get('month')); year = int(request.form.get('year'))
        hour = int(request.form.get('hour')); minute = int(request.form.get('minute')); lat = float(request.form.get('lat')); lon = float(request.form.get('lon')); tz = float(request.form.get('tz'))
        image_filename = ""
        if 'chart_image' in request.files:
            f = request.files['chart_image']
            if f and f.filename != '': fn = secure_filename(f.filename); un = f"chart_{random.randint(10000,99999)}_{fn}"; f.save(os.path.join(app.config['UPLOAD_FOLDER_CHARTS'], un)); image_filename = un
        bio_images = []
        for i in range(1, 4):
            key = f'bio_image_{i}'
            if key in request.files:
                f = request.files[key]
                if f and f.filename != '': fn = secure_filename(f.filename); un = f"bio_{random.randint(1000,9999)}_{fn}"; f.save(os.path.join(app.config['UPLOAD_FOLDER_CHARTS'], un)); bio_images.append(un)
                else: bio_images.append("")
            else: bio_images.append("")
        _, calc_data = ASTRO_MOTOR_NESNESİ.calculate_chart_data(year, month, day, hour, minute, tz, lat, lon, None, 'P', 'Astronomik')
        asc_sign = "Bilinmeyen"; sun_sign = "Bilinmeyen"
        if calc_data:
            asc_deg = calc_data['cusps']['ASC']; asc_sign, _, _ = get_relative_degree(asc_deg, 'Astronomik')
            sun_deg = calc_data['planets']['Güneş'][0]; sun_sign, _, _ = get_relative_degree(sun_deg, 'Astronomik')
            if asc_sign in ["Yılancı", "Ophiuchus"]: asc_sign = "Akrep"
            if sun_sign in ["Yılancı", "Ophiuchus"]: sun_sign = "Akrep"
        
        # --- CEVAPLARI İŞLE ---
        raw_answers = request.form.get('answers_bulk', '')
        answers_list = re.split(r'\n\s*\n', raw_answers.strip()) if raw_answers else []

        new_c = {"id": random.randint(10000, 99999), "name": name, "category": category_input, "asc_sign": asc_sign, "sun_sign": sun_sign, "bio": bio, "image": image_filename, "bio_images": bio_images, "year": year, "month": month, "day": day, "hour": hour, "minute": minute, "lat": lat, "lon": lon, "tz": tz, "location_name": location_name, "answers": answers_list}
        charts = load_json_data(DATA_FILE); charts.append(new_c); save_json_data(DATA_FILE, charts)
    except Exception as e: print(f"Hata: {e}")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit_chart/<int:id>', methods=['POST'])
def admin_edit_chart(id):
    if not session.get('admin_access'): return redirect(url_for('admin_login_page'))
    try:
        charts = load_json_data(DATA_FILE); target = next((c for c in charts if c['id'] == id), None)
        if target:
            target.update({k: request.form.get(k) for k in ['name','category','bio','location_name']})
            target.update({k: int(request.form.get(k)) for k in ['day','month','year','hour','minute']})
            target.update({k: float(request.form.get(k)) for k in ['lat','lon','tz']})
            
            # CEVAPLARI GÜNCELLE
            raw_answers = request.form.get('answers_bulk', '')
            if raw_answers:
                target['answers'] = re.split(r'\n\s*\n', raw_answers.strip())

            if 'chart_image' in request.files:
                f = request.files['chart_image']
                if f and f.filename != '': fn = secure_filename(f.filename); un = f"chart_{random.randint(10000,99999)}_{fn}"; f.save(os.path.join(app.config['UPLOAD_FOLDER_CHARTS'], un)); target['image'] = un 
            current_bio_imgs = target.get('bio_images', ["", "", ""])
            while len(current_bio_imgs) < 3: current_bio_imgs.append("")
            for i in range(3):
                key = f'bio_image_{i+1}'
                if key in request.files:
                    f = request.files[key]
                    if f and f.filename != '': fn = secure_filename(f.filename); un = f"bio_{random.randint(1000,9999)}_{fn}"; f.save(os.path.join(app.config['UPLOAD_FOLDER_CHARTS'], un)); current_bio_imgs[i] = un
            target['bio_images'] = current_bio_imgs
            _, calc_data = ASTRO_MOTOR_NESNESİ.calculate_chart_data(target['year'], target['month'], target['day'], target['hour'], target['minute'], target['tz'], target['lat'], target['lon'], None, 'P', 'Astronomik')
            if calc_data:
                asc_deg = calc_data['cusps']['ASC']; new_asc, _, _ = get_relative_degree(asc_deg, 'Astronomik')
                sun_deg = calc_data['planets']['Güneş'][0]; new_sun, _, _ = get_relative_degree(sun_deg, 'Astronomik')
                target['asc_sign'] = new_asc; target['sun_sign'] = new_sun
            save_json_data(DATA_FILE, charts)
    except Exception as e: print(f"Edit Hatası: {e}")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_chart/<int:id>')
def admin_delete_chart(id):
    if not session.get('admin_access'): return redirect(url_for('admin_login_page'))
    charts = [c for c in load_json_data(DATA_FILE) if c['id'] != id]; save_json_data(DATA_FILE, charts)
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add_course', methods=['POST'])
def admin_add_course():
    if not session.get('admin_access'): return redirect(url_for('admin_login_page'))
    img = "default_course.jpg"
    if 'course_image' in request.files:
        f = request.files['course_image']
        if f and f.filename != '': fn = secure_filename(f.filename); un = f"{random.randint(1000,9999)}_{fn}"; f.save(os.path.join(app.config['UPLOAD_FOLDER_COURSES'], un)); img = un
    courses = load_json_data(COURSES_FILE); courses.append({"id": random.randint(10000, 99999), "title": request.form.get('title'), "date": request.form.get('date'), "description": request.form.get('description'), "link": request.form.get('link', '#'), "image": img}); save_json_data(COURSES_FILE, courses)
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_course/<int:id>')
def admin_delete_course(id):
    if not session.get('admin_access'): return redirect(url_for('admin_login_page'))
    courses = [c for c in load_json_data(COURSES_FILE) if c['id'] != id]; save_json_data(COURSES_FILE, courses)
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_user/<email>')
def admin_delete_user(email):
    if not session.get('admin_access'): return redirect(url_for('admin_login_page'))
    user_manager.delete_registered_user(email); return redirect(url_for('admin_dashboard'))

# ============================================================================
# 🔑 EKSİK OLAN LOGIN ROTASI
# ============================================================================
# web_app.py içindeki login ve register fonksiyonlarını bununla değiştir:

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Eğer zaten giriş yapmışsa direkt ana sayfaya at
    if session.get('logged_in_email'):
        return redirect(url_for('home'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # 1. user_manager ile bilgileri kontrol et
        # (Önce arşivi tazelemesi için user_manager'ı zorlayalım)
        user_manager.load_archive_from_disk() 
        success, message = user_manager.try_login(email, password)
        
        if success:
            # ✅ İŞTE EKSİK OLAN PARÇA BU:
            # Kullanıcının emailini tarayıcı hafızasına (Session) kazıyoruz.
            session['logged_in_email'] = email
            
            # Ana sayfaya gönder
            return redirect(url_for('home'))
        else:
            # Şifre yanlışsa hata mesajıyla sayfayı tekrar göster
            return render_template('login.html', error=message)

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone', '') # Telefonu da alalım
        
        # user_manager ile kaydet
        success, message = user_manager.register_user(name, email, password, phone)
        
        if success:
            # Kayıt başarılıysa login sayfasına gönder ama hata mesajı yerine başarı mesajı verelim
            # (login.html'de session['login_success'] varsa yeşil gösterir)
            session['login_success'] = "Kayıt başarılı! Şimdi giriş yapabilirsin."
            return redirect(url_for('login'))
        else:
             return render_template('login.html', register_error=message)
             
    return render_template('login.html')
    
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
# 🔄 API: RETURN HESAPLAMA (VERİ BANKASI + AKTİF HARİTA DESTEKLİ)
# ============================================================================
@app.route('/api/calculate_returns', methods=['POST'])
def api_calculate_returns():
    try:
        print("\n--- RETURN HESAPLAMA BAŞLADI ---")
        data = request.get_json()
        
        # ID'yi al (String gelebilir, int'e çevir)
        raw_id = data.get('natal_chart_id')
        natal_chart_id = int(raw_id) if raw_id is not None else -1
        
        start_year = int(data.get('start_year'))
        end_year = int(data.get('end_year'))
        planet_name = data.get('planet_name')
        target_zodiac = data.get('zodiac_type', 'Astronomik')
        
        print(f"İstek: ID={natal_chart_id}, Gezegen={planet_name}, Yıl={start_year}-{end_year}")

        # 1. HARİTAYI BUL (Önce Aktif'e, sonra Veri Bankası'na bak)
        natal_chart = None
        
        # A) Aktif Haritalarda Ara (ID küçükse indekstir)
        active_charts = session.get('active_charts', [])
        if 0 <= natal_chart_id < len(active_charts):
            natal_chart = active_charts[natal_chart_id]
            print("-> Kaynak: Aktif Oturum Haritası")
            
        # B) Veri Bankasında Ara (ID büyükse veritabanı ID'sidir)
        if not natal_chart:
            all_public = load_json_data(DATA_FILE)
            natal_chart = next((c for c in all_public if c['id'] == natal_chart_id), None)
            if natal_chart: print("-> Kaynak: Veri Bankası (Data)")

        if not natal_chart:
            print("❌ HATA: Harita bulunamadı!")
            return jsonify({'success': False, 'error': 'Harita bulunamadı.'})
        
        # 2. HESAPLAMA VERİLERİNİ HAZIRLA
        # UTC Saati Hesapla
        tz_val = float(natal_chart.get('tz', natal_chart.get('tz_offset', 0)))
        utc_hour = natal_chart['hour'] + (natal_chart['minute']/60.0) - tz_val
        tjd_natal = swe.julday(natal_chart['year'], natal_chart['month'], natal_chart['day'], utc_hour)
        
        # Gezegen ID
        p_map = {'Güneş': swe.SUN, 'Ay': swe.MOON, 'Merkür': swe.MERCURY, 'Venüs': swe.VENUS, 'Mars': swe.MARS, 'Jüpiter': swe.JUPITER, 'Satürn': swe.SATURN}
        pid = p_map.get(planet_name, swe.SUN)
        
        # 3. MODU AYARLA
        calc_flags = swe.FLG_SWIEPH | swe.FLG_SPEED
        if target_zodiac == 'Astronomik':
            calc_flags |= swe.FLG_SIDEREAL
            swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
        
        # 4. HEDEF DERECEYİ BUL
        res = swe.calc_ut(tjd_natal, pid, calc_flags)
        target_lon = res[0][0]
        
        # Drakonik Özel Durum
        if target_zodiac == 'Drakonik':
            swe.set_sid_mode(0, 0, 0) # Tropikale dön
            r_t = swe.calc_ut(tjd_natal, pid, swe.FLG_SWIEPH | swe.FLG_SPEED)[0][0]
            n_t = swe.calc_ut(tjd_natal, swe.MEAN_NODE, swe.FLG_SWIEPH | swe.FLG_SPEED)[0][0]
            target_lon = (r_t - n_t) % 360.0
        
        # 5. TARAMA MOTORU (Astro Core içindeki fonksiyonu kullanıyoruz)
        # Güvenlik için buraya manuel motoru ekliyorum:
        
        returns = []
        curr_jd = swe.julday(start_year, 1, 1)
        limit_jd = swe.julday(end_year + 1, 1, 1)
        step = 0.5 if pid == swe.MOON else 2.0
        
        safety = 0
        while curr_jd < limit_jd and safety < 20000:
            safety += 1
            
            def get_pos(t):
                if target_zodiac == 'Drakonik':
                    pp = swe.calc_ut(t, pid, swe.FLG_SWIEPH | swe.FLG_SPEED)[0][0]
                    nn = swe.calc_ut(t, swe.MEAN_NODE, swe.FLG_SWIEPH | swe.FLG_SPEED)[0][0]
                    return (pp - nn) % 360.0
                return swe.calc_ut(t, pid, calc_flags)[0][0]

            p1 = get_pos(curr_jd)
            p2 = get_pos(curr_jd + step)
            
            d1 = (p1 - target_lon + 180) % 360 - 180
            d2 = (p2 - target_lon + 180) % 360 - 180
            
            if (d1 * d2 < 0) and (abs(d1 - d2) < 180):
                # Hassas bul
                low = curr_jd; high = curr_jd + step; found = high
                for _ in range(15):
                    mid = (low+high)/2.0
                    pm = get_pos(mid)
                    dm = (pm - target_lon + 180) % 360 - 180
                    if d1 * dm < 0: high = mid
                    else: low = mid
                    found = low
                
                y, m, d, h_dec = swe.revjul(found)
                if start_year <= y <= end_year:
                    date_str = f"{d:02d}.{m:02d}.{y} {int(h_dec):02d}:{int((h_dec-int(h_dec))*60):02d}"
                    print(f"   -> Bulundu: {date_str}")
                    returns.append({'year': y, 'month': m, 'day': d, 'hour': int(h_dec), 'minute': int((h_dec-int(h_dec))*60), 'date_str': date_str})
                
                curr_jd = found + (25.0 if pid==swe.MOON else 300.0)
                continue
            
            curr_jd += step

        print(f"--- BİTTİ: {len(returns)} sonuç ---")
        return jsonify({'success': True, 'returns': returns})

    except Exception as e:
        print(f"API HATASI: {e}")
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
        d = request.get_json(); city = d.get('city')
        now = datetime.datetime.now()
        try: req_year = int(d.get('year', now.year)); req_month = int(d.get('month', now.month)); req_day = int(d.get('day', now.day))
        except: req_year, req_month, req_day = now.year, now.month, now.day
        geolocator = Nominatim(user_agent=f"astro_{random.randint(1000,9999)}"); locs = geolocator.geocode(city, exactly_one=False, limit=5, language='tr', timeout=10)
        if not locs: return jsonify({'success': False, 'message': 'Bulunamadı'})
        res = []; tf = None
        try: tf = TimezoneFinder(in_memory=True)
        except: pass
        for l in locs:
            offset = 0.0; tz_name = "UTC"
            if tf:
                try: 
                    found_tz = tf.timezone_at(lng=l.longitude, lat=l.latitude)
                    if found_tz: tz_name = found_tz; target_dt = datetime.datetime(req_year, req_month, req_day, 12, 0); tz_obj = pytz.timezone(tz_name); dt_aware = tz_obj.localize(target_dt, is_dst=None); offset = dt_aware.utcoffset().total_seconds() / 3600.0
                except: offset = 3.0 if 'Turkey' in l.address or 'Türkiye' in l.address else 0.0
            else: offset = 3.0 if 'Turkey' in l.address or 'Türkiye' in l.address else 0.0
            res.append({'address': l.address, 'lat': l.latitude, 'lon': l.longitude, 'tz_offset': offset, 'tz_name': tz_name})
        return jsonify({'success': True, 'results': res})
    except: return jsonify({'success': False})

@app.route('/api/search_celestial_events', methods=['POST'])
def search_celestial_events():
    try:
        data = request.get_json()
        year = int(data.get('year'))
        results = find_annual_celestial_events(year)
        return jsonify({'success': True, 'eclipses': results['eclipses'], 'phases': results['phases']})
    except Exception as e:
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

        def safe_float(val, default=0.0):
            try:
                if val is None: return default
                return float(val)
            except:
                return default

        def safe_int(val, default=0):
            try:
                if val is None: return default
                return int(val)
            except:
                return default

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
        full_data = content.get('data')
        calc_type = content.get('type')
        
        active_charts = session.get('active_charts', [])
        
        # Orijinal harita meta verilerini Session'dan çek (ILERLETME İÇİN GEREKLİ)
        raw_id1 = full_data.get('data', {}).get('id1') or full_data.get('id1')
        raw_id2 = full_data.get('data', {}).get('id2') or full_data.get('id2')
        
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


@app.route('/api/swap_synastry', methods=['POST'])
def api_swap_synastry():
    """
    Sinastri haritalarında iç ve dış çarkı değiştir.
    chart1 (dış) ile chart2 (iç) yer değiştirir ve evleri yeniden hesaplar.
    """
    try:
        active_charts = session.get('active_charts', [])
        current_index = session.get('current_chart_index', 0)
        
        if current_index < 0 or current_index >= len(active_charts):
            return jsonify({'success': False, 'error': 'Aktif harita bulunamadı.'})
        
        chart = active_charts[current_index]
        
        # Sadece sinastri haritaları için çalış
        if chart.get('type') not in ['synastry', 'composite']:
            return jsonify({'success': False, 'error': 'Bu işlem sadece sinastri haritaları için geçerlidir.'})
        
        # Saved data'yı al
        saved_data = chart.get('saved_data', {})
        if not saved_data:
            return jsonify({'success': False, 'error': 'Harita verileri eksik.'})
        
        # chart1 ve chart2'yi değiştir
        chart1_old = saved_data.get('chart1')
        chart2_old = saved_data.get('chart2')
        
        if not chart1_old or not chart2_old:
            return jsonify({'success': False, 'error': 'Harita verileri eksik.'})
        
        # YER DEĞİŞTİR
        saved_data['chart1'] = chart2_old  # Eski dış -> Yeni iç
        saved_data['chart2'] = chart1_old  # Eski iç -> Yeni dış
        
        # Evleri yeni iç haritadan al (chart1 artık eski chart2)
        saved_data['houses'] = chart2_old.get('houses', {})
        saved_data['cusps'] = chart2_old.get('cusps', {})
        saved_data['boundaries'] = chart2_old.get('boundaries', [])
        
        # Meta verileri de değiştir
        meta1_old = chart.get('natal_meta_1')
        meta2_old = chart.get('natal_meta_2')
        
        if meta1_old and meta2_old:
            chart['natal_meta_1'] = meta2_old
            chart['natal_meta_2'] = meta1_old
        
        # Güncelle
        chart['saved_data'] = saved_data
        active_charts[current_index] = chart
        session['active_charts'] = active_charts
        session['last_chart'] = saved_data
        session['current_chart_data'] = chart
        
        return jsonify({'success': True, 'message': 'Haritalar değiştirildi!'})
        
    except Exception as e:
        print(f"❌ Swap Hatası: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

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
        now = datetime.datetime.now()
        if data.get('target_date'):
            try:
                dt_target = datetime.datetime.strptime(data.get('target_date'), '%Y-%m-%dT%H:%M')
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

        # B) SECONDARY PROGRESSION
        elif technique == 'secondary':
            res_text, prog_data = ASTRO_MOTOR_NESNESİ.calculate_secondary_progression(
                natal_year, natal_month, natal_day, natal_hour, natal_minute, natal_tz,
                now.year, now.month, now.day,
                natal_lat, natal_lon, house_code, target_zodiac
            )
            title = f"İkincil İlerletim ({now.day}.{now.month}.{now.year})"
            
            # Progressed tarih hesabı
            from datetime import date
            birth_date = date(natal_year, natal_month, natal_day)
            target_date_obj = date(now.year, now.month, now.day)
            days_diff = (target_date_obj - birth_date).days
            prog_calc_date = datetime.datetime(natal_year, natal_month, natal_day) + timedelta(days=days_diff)
            prog_year, prog_month, prog_day = prog_calc_date.year, prog_calc_date.month, prog_calc_date.day

        # C) SOLAR ARC
        else: # solar_arc
            res_text, prog_data = ASTRO_MOTOR_NESNESİ.calculate_solar_arc_progression(
                natal_year, natal_month, natal_day, natal_hour, natal_minute, natal_tz,
                now.year, now.month, now.day,
                natal_lat, natal_lon, house_code, target_zodiac
            )
            title = f"Güneş Yayı ({now.year})"

        if not prog_data:
            return jsonify({'success': False, 'error': 'İlerletim hesaplanamadı: ' + res_text})
        
        # Harita adını ve tipini güncelle
        prog_data['name'] = f"{source_chart['name']} - {title}"
        prog_data['zodiac_type'] = target_zodiac 

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
                    new_chart = {'id': len(session.get('active_charts', [])) + 1, 'name': name, 'year': year, 'month': month, 'day': day, 'hour': hour, 'minute': minute, 'tz_offset': tz_offset, 'lat': lat, 'lon': lon, 'location_name': loc_name, 'zodiac_type': zodiac, 'house_system': h_sys, 'type': 'natal'}
                    current_charts = session.get('active_charts', [])
                    current_charts.insert(0, new_chart)
                    session['active_charts'] = current_charts
                    session['current_chart_index'] = 0
                    session['last_report'] = res_text
                    session['last_chart'] = chart_data
                    session['current_chart_data'] = new_chart
                    active_tab = 'aktif' 
                else: session['report_error'] = res_text 
            except Exception as e: 
                session['report_error'] = f"Hata: {e}"; traceback.print_exc() 

        elif active_tab == 'instant_transit':
            try:
                yr = int(request.form.get('bar_year')); mo = int(request.form.get('bar_month')); dy = int(request.form.get('bar_day'))
                hr = int(request.form.get('bar_hour')); mn = int(request.form.get('bar_minute'))
                lat = float(request.form.get('bar_lat', 0)); lon = float(request.form.get('bar_lon', 0)); tz = float(request.form.get('bar_tz', 0))
                t_type = request.form.get('transit_type', 'Astronomik')
                res, t_data = ASTRO_MOTOR_NESNESİ.calculate_chart_data(yr, mo, dy, hr, mn, tz, lat, lon, None, 'P', t_type)
                if t_data:
                    transit_chart = {'name': f"Transit ({dy}.{mo}.{yr} {hr}:{mn})", 'year': yr, 'month': mo, 'day': dy, 'hour': hr, 'minute': mn, 'tz_offset': tz, 'lat': lat, 'lon': lon, 'location_name': request.form.get('bar_loc_name'), 'zodiac_type': t_type, 'house_system': 'Placidus (P)', 'id': len(session.get('active_charts', [])) + 1, 'type': 'transit'}
                    current_charts = session.get('active_charts', [])
                    current_charts.insert(0, transit_chart)
                    session['active_charts'] = current_charts
                    session['current_chart_index'] = 0
                    session['last_chart'] = t_data
                    session['last_report'] = f"TRANSİT\n\n" + res
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

@app.route('/iletisim')
def page_contact(): context = get_common_context(); context.update({'contact': load_json_data(CONTACT_FILE), 'active_page': 'iletisim'}); return render_template('contact.html', **context)

@app.route('/kayitli-haritalar')
def kayitli_haritalar(): 
    if not get_current_user_email(): return redirect(url_for('login'))
    context = get_common_context()
    saved_charts = user_manager.get_user_saved_charts(get_current_user_email())
    context.update({'saved_charts': saved_charts, 'active_page': 'kayitli_haritalar'})
    return render_template('kayitli_haritalar.html', **context)

@app.route('/create_folder', methods=['POST'])
def create_folder():
    email = get_current_user_email()
    if not email: return redirect(url_for('login'))
    if request.form.get('folder_name'): user_manager.create_new_folder(email, request.form.get('folder_name'))
    return redirect(url_for('kayitli_haritalar'))

@app.route('/move_chart', methods=['POST'])
def move_chart():
    email = get_current_user_email()
    if not email: return redirect(url_for('login'))
    if request.form.get('chart_id') and request.form.get('old_folder') and request.form.get('new_folder'):
        user_manager.move_chart_to_folder(email, request.form.get('chart_id'), request.form.get('old_folder'), request.form.get('new_folder'))
    return redirect(url_for('kayitli_haritalar'))

@app.route('/load_chart_to_active/<category>/<chart_id>')
def load_chart_to_active(category, chart_id):
    email = get_current_user_email()
    if not email: return redirect(url_for('login'))
    saved = user_manager.get_user_saved_charts(email)
    sel = next((c for c in saved.get(category, []) if str(c.get('id')) == str(chart_id)), None)
    if sel:
        if 'active_charts' not in session: session['active_charts'] = []
        house_code = ASTRO_MOTOR_NESNESİ.HOUSE_SYSTEMS.get(sel.get('house_system', 'Placidus'), 'P')
        res, data = ASTRO_MOTOR_NESNESİ.calculate_chart_data(sel['year'], sel['month'], sel['day'], sel['hour'], sel['minute'], float(sel['tz_offset']), float(sel['lat']), float(sel['lon']), None, house_code, sel.get('zodiac_type', 'Astronomik'))
        if data:
            new_chart = sel.copy(); new_chart['id'] = len(session.get('active_charts', [])) + 1; new_chart['type'] = 'natal'
            current = session.get('active_charts', []); current.insert(0, new_chart)
            session['active_charts'] = current; session['current_chart_index'] = 0; session['last_chart'] = data; session['last_report'] = res; session['current_chart_data'] = new_chart
            return redirect(url_for('home', tab='aktif'))
    return redirect(url_for('kayitli_haritalar'))

@app.route('/delete_saved_chart/<category>/<chart_id>')
def delete_saved_chart(category, chart_id):
    email = get_current_user_email()
    if not email: return redirect(url_for('login'))
    if hasattr(user_manager, 'delete_user_chart'):
        user_manager.delete_user_chart(email, category, chart_id)
    return redirect(url_for('kayitli_haritalar'))

@app.route('/set_active_time', methods=['POST'])
def set_active_time():
    active_charts = session.get('active_charts', []); idx = session.get('current_chart_index', 0)
    if not active_charts or idx >= len(active_charts): return redirect(url_for('home', tab='aktif'))
    
    chart = active_charts[idx]
    
    try:
        # 1. HEDEF ZAMANI AL
        dt = datetime.datetime.strptime(request.form.get('target_date'), '%Y-%m-%dT%H:%M')
        
        # --- SİNASTRİ KONTROLÜ VE İLERLETME ---
        if chart.get('type') in ['synastry', 'composite']:
            
            meta1 = chart.get('natal_meta_1')
            meta2 = chart.get('natal_meta_2')
            
            if not meta1 or not meta2: raise Exception("Sinastri meta verileri eksik.")

            # İÇ ÇARK (NATAL - meta1): HER ZAMAN SABİT DOĞUM TARİHİYLE HESAPLA
            _, data1 = ASTRO_MOTOR_NESNESİ.calculate_chart_data(
                meta1['year'], meta1['month'], meta1['day'], meta1['hour'], meta1['minute'], 
                float(meta1['tz_offset']), float(meta1['lat']), float(meta1['lon']), None, 
                ASTRO_MOTOR_NESNESİ.HOUSE_SYSTEMS.get(meta1.get('house_system'), 'P'), 
                meta1.get('zodiac_type', 'Astronomik')
            )
            
            # DIŞ ÇARK (PROGRESSED - meta2): YENİ ZAMANLA HESAPLA (İLERLER)
            _, data2 = ASTRO_MOTOR_NESNESİ.calculate_chart_data(
                dt.year, dt.month, dt.day, dt.hour, dt.minute, 
                float(meta2['tz_offset']), float(meta2['lat']), float(meta2['lon']), None, 
                ASTRO_MOTOR_NESNESİ.HOUSE_SYSTEMS.get(meta2.get('house_system'), 'P'), 
                meta2.get('zodiac_type', 'Astronomik')
            )
            
            # İsim ve zodyak bilgisini ekle
            data1['name'] = meta1['name']
            data1['zodiac_type'] = meta1.get('zodiac_type', 'Astronomik')
            data2['name'] = meta2['name']
            data2['zodiac_type'] = meta2.get('zodiac_type', 'Astronomik')
            
            # Sinastri paketini doğru yapıda oluştur
            # chart1 = DIŞ çark (ilerleyen, meta2) 
            # chart2 = İÇ çark (sabit, meta1)
            synastry_package = {
                'type': 'synastry',
                'chart1': data2,  # DIŞ ÇARK (İlerletilmiş)
                'chart2': data1,  # İÇ ÇARK (Sabit)
                'houses': data1.get('houses', {}),
                'cusps': data1.get('cusps', {}),
                'boundaries': data1.get('boundaries', [])
            }
            
            # Session'ı güncelle
            chart['saved_data'] = synastry_package
            
            # Layout.html için güncel zamanı kaydet (chart2'nin zamanı)
            chart['name'] = f"Sinastri: {meta1['name']} & {meta2['name']}"
            chart['year'] = dt.year 
            chart['month'] = dt.month
            chart['day'] = dt.day
            chart['hour'] = dt.hour
            chart['minute'] = dt.minute

            res = "Sinastri İlerletildi"
            data = synastry_package
            
        else:
            # Natal Harita Seçiliyse: Sadece o haritayı ilerlet (Eski Mantık)
            chart.update({'year': dt.year, 'month': dt.month, 'day': dt.day, 'hour': dt.hour, 'minute': dt.minute})
            res, data = ASTRO_MOTOR_NESNESİ.calculate_chart_data(
                chart['year'], chart['month'], chart['day'], chart['hour'], chart['minute'], 
                float(chart['tz_offset']), float(chart['lat']), float(chart['lon']), None, 
                ASTRO_MOTOR_NESNESİ.HOUSE_SYSTEMS.get(chart.get('house_system'), 'P'), 
                chart.get('zodiac_type', 'Astronomik')
            )
            
        # Ortak Session Güncelleme
        active_charts[idx] = chart; 
        session['active_charts'] = active_charts; 
        session['last_chart'] = data; 
        session['last_report'] = res; 
        session['current_chart_data'] = chart

    except Exception as e: 
        session['report_error'] = str(e)
        traceback.print_exc()

    return redirect(url_for('home', tab='aktif'))

@app.route('/adjust_active_time', methods=['POST']) 
def adjust_active_time():
    active_charts = session.get('active_charts', []); idx = session.get('current_chart_index', 0)
    if not active_charts or idx >= len(active_charts): return redirect(url_for('home', tab='aktif'))
    chart = active_charts[idx]
    
    try:
        u = request.form.get('unit'); a = int(request.form.get('amount')); dt = datetime.datetime(chart['year'], chart['month'], chart['day'], chart['hour'], chart['minute'])
        
        # Zamanı ayarla
        if u == 'minute': dt += relativedelta(minutes=a)
        elif u == 'hour': dt += relativedelta(hours=a)
        elif u == 'day': dt += relativedelta(days=a)
        elif u == 'week': dt += relativedelta(weeks=a)
        elif u == 'month': dt += relativedelta(months=a)
        elif u == 'year': dt += relativedelta(years=a)
        
        # --- SİNASTRİ/İLERLETİM KONTROLÜ ---
        if chart.get('type') in ['synastry', 'composite']:
            
            meta1 = chart.get('natal_meta_1')
            meta2 = chart.get('natal_meta_2')
            
            if not meta1 or not meta2: raise Exception("Sinastri meta verileri eksik.")

            # İÇ ÇARK (NATAL - meta1): HER ZAMAN SABİT DOĞUM TARİHİYLE HESAPLA
            _, data1 = ASTRO_MOTOR_NESNESİ.calculate_chart_data(
                meta1['year'], meta1['month'], meta1['day'], meta1['hour'], meta1['minute'], 
                float(meta1['tz_offset']), float(meta1['lat']), float(meta1['lon']), None, 
                ASTRO_MOTOR_NESNESİ.HOUSE_SYSTEMS.get(meta1.get('house_system'), 'P'), 
                meta1.get('zodiac_type', 'Astronomik')
            )
            
            # DIŞ ÇARK (PROGRESSED - meta2): YENİ ZAMANLA HESAPLA (İLERLER)
            _, data2 = ASTRO_MOTOR_NESNESİ.calculate_chart_data(
                dt.year, dt.month, dt.day, dt.hour, dt.minute, 
                float(meta2['tz_offset']), float(meta2['lat']), float(meta2['lon']), None, 
                ASTRO_MOTOR_NESNESİ.HOUSE_SYSTEMS.get(meta2.get('house_system'), 'P'), 
                meta2.get('zodiac_type', 'Astronomik')
            )
            
            # İsim ve zodyak bilgisini ekle
            data1['name'] = meta1['name']
            data1['zodiac_type'] = meta1.get('zodiac_type', 'Astronomik')
            data2['name'] = meta2['name']
            data2['zodiac_type'] = meta2.get('zodiac_type', 'Astronomik')
            
            # Sinastri paketini doğru yapıda oluştur
            synastry_package = {
                'type': 'synastry',
                'chart1': data2,  # DIŞ ÇARK (İlerletilmiş)
                'chart2': data1,  # İÇ ÇARK (Sabit)
                'houses': data1.get('houses', {}),
                'cusps': data1.get('cusps', {}),
                'boundaries': data1.get('boundaries', [])
            }
            
            # Session'ı güncelle
            chart['saved_data'] = synastry_package
            
            # Layout.html için güncel zamanı kaydet
            chart['year'] = dt.year
            chart['month'] = dt.month
            chart['day'] = dt.day
            chart['hour'] = dt.hour
            chart['minute'] = dt.minute
            
            res = "Sinastri İlerletildi"
            data = synastry_package
            
        else:
            # Natal Harita Seçiliyse: (Eski Mantık)
            chart.update({'year': dt.year, 'month': dt.month, 'day': dt.day, 'hour': dt.hour, 'minute': dt.minute})
            res, data = ASTRO_MOTOR_NESNESİ.calculate_chart_data(chart['year'], chart['month'], chart['day'], chart['hour'], chart['minute'], float(chart['tz_offset']), float(chart['lat']), float(chart['lon']), None, ASTRO_MOTOR_NESNESİ.HOUSE_SYSTEMS.get(chart.get('house_system'), 'P'), chart.get('zodiac_type', 'Astronomik'))
            
        # Ortak Session Güncelleme
        active_charts[idx] = chart; session['active_charts'] = active_charts; session['last_chart'] = data; session['last_report'] = res; session['current_chart_data'] = chart
    except Exception as e: session['report_error'] = str(e); traceback.print_exc()
    return redirect(url_for('home', tab='aktif'))

@app.route('/set_active_chart/<int:index>')
def set_active_chart(index):
    al = session.get('active_charts', [])
    if al and 0 <= index < len(al):
        sel = al[index]; session['current_chart_index'] = index; session['current_chart_data'] = sel
        
        if sel.get('type') in ['synastry', 'composite']:
            saved_data = sel.get('saved_data', {})
            session['last_chart'] = saved_data 
            session['last_report'] = sel.get('type').capitalize()
        else:
            txt, data = ASTRO_MOTOR_NESNESİ.calculate_chart_data(sel['year'], sel['month'], sel['day'], sel['hour'], sel['minute'], float(sel['tz_offset']), float(sel['lat']), float(sel['lon']), None, ASTRO_MOTOR_NESNESİ.HOUSE_SYSTEMS.get(sel.get('house_system'), 'P'), sel.get('zodiac_type', 'Astronomik'))
            session['last_chart'] = data; session['last_report'] = txt
            
    return redirect(url_for('home', tab='aktif'))

@app.route('/delete_active_chart/<int:index>')
def delete_active_chart(index):
    active_charts = session.get('active_charts', [])
    if 0 <= index < len(active_charts):
        del active_charts[index]
        session['active_charts'] = active_charts
        
        # Eğer silinen harita aktif haritaysa, ilk haritayı aktif yap
        current_index = session.get('current_chart_index', 0)
        if current_index >= len(active_charts):
            session['current_chart_index'] = max(0, len(active_charts) - 1)
        
        # Eğer liste boşaldıysa, session'ı temizle
        if len(active_charts) == 0:
            session.pop('last_chart', None)
            session.pop('last_report', None)
            session.pop('current_chart_data', None)
        elif current_index == index:
            # Silinen harita aktifse, yeni aktif haritayı yükle
            new_index = min(index, len(active_charts) - 1)
            if new_index >= 0:
                return redirect(url_for('set_active_chart', index=new_index))
    
    return redirect(url_for('home', tab='aktif'))

@app.route('/edit_active_chart/<int:index>')
def edit_active_chart(index):
    if 'active_charts' in session and len(session['active_charts']) > index: session['current_chart_data'] = session['active_charts'][index]; return redirect(url_for('home', tab='natal'))
    return redirect(url_for('home', tab='aktif'))

@app.route('/edit_chart/<category>/<chart_id>')
def edit_chart(category, chart_id):
    if not get_current_user_email(): return redirect(url_for('login'))
    saved = user_manager.get_user_saved_charts(get_current_user_email()); sel = next((c for c in saved.get(category, []) if str(c.get('id')) == str(chart_id)), None)
    if sel: session['current_chart_data'] = {k: sel.get(k) for k in ['name','year','month','day','hour','minute','lat','lon','tz_offset','location_name','zodiac_type','house_system']}
    return redirect(url_for('home', tab='natal'))

@app.route('/save_active_chart/<int:index>')
def save_active_chart(index):
    if not get_current_user_email(): return redirect(url_for('login'))
    active_charts = session.get('active_charts', [])
    if 0 <= index < len(active_charts):
        chart = active_charts[index]
        if chart.get('type') != 'synastry':
            try:
                user_manager.save_chart_to_user_data(get_current_user_email(), chart, 'Genel')
            except: pass
    return redirect(url_for('home', tab='aktif'))

@app.route('/save_chart', methods=['POST'])
def save_chart():
    if not get_current_user_email(): return redirect(url_for('login'))
    try:
        c = session.get('current_chart_data', {}).copy()
        if c.get('type') == 'synastry': return redirect(url_for('home', tab='aktif'))
        c['data'] = session.get('last_chart', {}); c['report_text'] = session.get('last_report', '')
        user_manager.save_chart_to_user_data(get_current_user_email(), c, request.form.get('category_name', 'Genel'))
    except: pass
    return redirect(url_for('home', tab='aktif'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000)) 
    app.run(host='0.0.0.0', port=port, debug=True)








