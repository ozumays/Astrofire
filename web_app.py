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
# 🌍 SWISS EPHEMERIS YOL AYARI (GLOBAL VE GARANTİ)
# ============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EPHE_FOLDER = os.path.join(BASE_DIR, 'ephe')
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

# ========================================================
# 💾 YARDIMCI FONKSİYON: AKTİF HARİTALARI KAYDET
# ========================================================
def sync_active_charts_to_db():
    """Session'daki aktif haritaları users.json dosyasına yazar."""
    if 'logged_in_email' in session:
        email = session['logged_in_email']
        user_data = user_manager.get_user_data_by_email(email)
        
        if user_data:
            # Session'daki listeyi al, veritabanına koy
            user_data['active_charts'] = session.get('active_charts', [])
            user_manager.save_user_data(email, user_data)
            print(f"💾 [SYNC] {email} için aktif haritalar veritabanına kaydedildi.")

# ============================================================================
# 🔮 TRANSİT TAHMİN MOTORU
# ============================================================================
def get_transit_predictions(chart_date, current_planets, motor_instance):
    if not current_planets or not chart_date: return []

    fast_movers = ['Ay', 'Merkür', 'Venüs', 'Güneş', 'Mars']
    predictions = []
    
    for mover_name in fast_movers:
        if mover_name not in current_planets: continue
        for target_name, target_data in current_planets.items():
            if mover_name == target_name: continue
            
            target_abs_deg = float(target_data[0])
            target_sign_str, target_deg_val, _ = get_relative_degree(target_abs_deg, 'Astronomik')

            max_days = 180  
            step_days = 1   
            tolerance = 1.5
            if mover_name == 'Ay': 
                max_days = 30 
                tolerance = 10.0 
            
            found_date = None
            is_retro_trap = False 
            
            temp_date = chart_date
            for i in range(1, max_days):
                temp_date += timedelta(days=step_days)
                try:
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
                    'mover': mover_name, 'target': target_name,
                    'target_sign': target_sign_str, 'target_deg': target_deg_val,    
                    'days_later': found_date, 'is_retro': is_retro_trap
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
        form_email = request.form.get('email', '').strip().lower()
        form_password = request.form.get('password', '').strip()
        if form_email in ADMIN_EMAILS:
            if form_password == ADMIN_PASSWORD:
                session['admin_access'] = True; return redirect(url_for('admin_dashboard'))
            else: return render_template('admin_login.html', error=f"Şifre Hatalı!")
        else: return render_template('admin_login.html', error=f"Email Listede Yok!")
    return render_template('admin_login.html')

@app.route('/yonetim/dashboard')
def admin_dashboard():
    if not session.get('admin_access'): return redirect(url_for('admin_login_page'))
    user_manager.load_archive_from_disk()
    return render_template('admin_dashboard.html', users=user_manager.get_all_users(), public_charts=load_json_data(DATA_FILE), courses=load_json_data(COURSES_FILE), contact=load_json_data(CONTACT_FILE))

@app.route('/yonetim/logout')
def admin_logout():
    session.pop('admin_access', None); return redirect(url_for('admin_login_page'))

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
            
            raw_answers = request.form.get('answers_bulk', '')
            if raw_answers: target['answers'] = re.split(r'\n\s*\n', raw_answers.strip())

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
# 🔑 LOGIN / REGISTER ROTALARI
# ============================================================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # 1. Giriş Doğrulama (Hata korumalı)
        # user_manager bazen sadece True/False, bazen (True, "Mesaj") dönebilir.
        # İkisini de kapsayacak güvenli kod:
        login_result = user_manager.validate_login(email, password)
        
        success = False
        error_msg = "Email veya şifre hatalı."
        
        if isinstance(login_result, tuple):
            # Eğer (True, "Giriş Başarılı") gibi gelirse
            success = login_result[0]
            error_msg = login_result[1]
        else:
            # Eğer sadece True veya False gelirse
            success = login_result
        
        if success:
            # 2. Kullanıcı Verisini Çek
            # validate_login data dönmüyorsa, datayı ayrıca çekiyoruz (En garantisi)
            user_data = user_manager.get_user_data_by_email(email)
            
            if not user_data:
                return render_template('login.html', error="Kullanıcı verisi alınamadı.")

            session['logged_in'] = True
            session['logged_in_email'] = email
            session['display_name'] = user_data.get('name', 'Kullanıcı')
            
            # --- 3. AKTİF HARİTALARI GERİ YÜKLE ---
            saved_active = user_data.get('active_charts', [])
            
            # Eğer gelen veri liste değilse (hata önlemi) boş liste yap
            if not isinstance(saved_active, list):
                saved_active = []
                
            session['active_charts'] = saved_active
            # -----------------------------------
            
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error=error_msg)

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone', '') 
        
        success, message = user_manager.register_user(name, email, password, phone)
        
        if success:
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
# 🔄 API: RETURN HESAPLAMA (GÜNCELLENDİ: TROPIKAL / ASTRONOMİK / DRAKONİK)
# ============================================================================
@app.route('/api/calculate_returns', methods=['POST'])
def api_calculate_returns():
    try:
        print("\n--- RETURN HESAPLAMA BAŞLADI ---")
        data = request.get_json()
        
        raw_id = data.get('natal_chart_id')
        natal_chart_id = int(raw_id) if raw_id is not None else -1
        
        start_year = int(data.get('start_year'))
        end_year = int(data.get('end_year'))
        planet_name = data.get('planet_name')
        target_zodiac = data.get('zodiac_type', 'Tropikal') 
        
        print(f"İstek: ID={natal_chart_id}, Gezegen={planet_name}, Yıl={start_year}-{end_year}, Tip={target_zodiac}")

        natal_chart = None
        active_charts = session.get('active_charts', [])
        
        if 0 <= natal_chart_id < len(active_charts):
            natal_chart = active_charts[natal_chart_id]
            print("-> Kaynak: Aktif Oturum Haritası")
            
        if not natal_chart:
            all_public = load_json_data(DATA_FILE)
            natal_chart = next((c for c in all_public if c['id'] == natal_chart_id), None)
            if natal_chart: print("-> Kaynak: Veri Bankası")

        if not natal_chart:
            return jsonify({'success': False, 'error': 'Harita bulunamadı.'})
        
        # Global EPHE_PATH'i kullan
        if 'EPHE_PATH' in globals():
             swe.set_ephe_path(f"{EPHE_PATH}:{BASE_DIR}")
        
        tz_val = float(natal_chart.get('tz', natal_chart.get('tz_offset', 0)))
        utc_hour = natal_chart['hour'] + (natal_chart['minute']/60.0) - tz_val
        tjd_natal = swe.julday(natal_chart['year'], natal_chart['month'], natal_chart['day'], utc_hour)
        
        p_map = {'Güneş': swe.SUN, 'Ay': swe.MOON, 'Merkür': swe.MERCURY, 'Venüs': swe.VENUS, 'Mars': swe.MARS, 'Jüpiter': swe.JUPITER, 'Satürn': swe.SATURN}
        pid = p_map.get(planet_name, swe.SUN)
        
        calc_flags = swe.FLG_SWIEPH | swe.FLG_SPEED
        target_lon = 0
        
        if target_zodiac == 'Astronomik':
            swe.set_sid_mode(swe.SIDM_FAGAN_BRADLEY, 0, 0)
            calc_flags |= swe.FLG_SIDEREAL
            res = swe.calc_ut(tjd_natal, pid, calc_flags)
            target_lon = res[0][0]
            
        elif target_zodiac == 'Drakonik':
            swe.set_sid_mode(0, 0, 0) 
            p_res = swe.calc_ut(tjd_natal, pid, swe.FLG_SWIEPH | swe.FLG_SPEED)[0][0]
            n_res = swe.calc_ut(tjd_natal, swe.MEAN_NODE, swe.FLG_SWIEPH | swe.FLG_SPEED)[0][0]
            target_lon = (p_res - n_res) % 360.0
            
        else:
            swe.set_sid_mode(0, 0, 0)
            res = swe.calc_ut(tjd_natal, pid, calc_flags)
            target_lon = res[0][0]
        
        def get_current_pos(t):
            if target_zodiac == 'Drakonik':
                pp = swe.calc_ut(t, pid, swe.FLG_SWIEPH | swe.FLG_SPEED)[0][0]
                nn = swe.calc_ut(t, swe.MEAN_NODE, swe.FLG_SWIEPH | swe.FLG_SPEED)[0][0]
                return (pp - nn) % 360.0
            else:
                return swe.calc_ut(t, pid, calc_flags)[0][0]

        returns = []
        curr_jd = swe.julday(start_year, 1, 1)
        limit_jd = swe.julday(end_year + 1, 1, 1)
        step = 0.5 if pid == swe.MOON else 2.0
        
        safety = 0
        while curr_jd < limit_jd and safety < 20000:
            safety += 1
            
            p1 = get_current_pos(curr_jd)
            p2 = get_current_pos(curr_jd + step)
            
            d1 = (p1 - target_lon + 180) % 360 - 180
            d2 = (p2 - target_lon + 180) % 360 - 180
            
            if (d1 * d2 < 0) and (abs(d1 - d2) < 180):
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
            
            sync_active_charts_to_db() # <--- KAYDETME EKLENDİ
            
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
def api_search_celestial_events():
    try:
        import os 
        data = request.json
        year = int(data.get('year', 2025))
        zodiac_type = data.get('zodiac_type', 'Tropikal') 
        eclipses = []
        phases = []
        
        # EPHE_PATH zaten global, ama tekrar set edelim garanti olsun
        if 'EPHE_PATH' in globals():
             swe.set_ephe_path(f"{EPHE_PATH}:{BASE_DIR}")
        
        def get_zodiac_pos(julian_day, body_id):
            swe.set_sid_mode(0, 0, 0)
            res = swe.calc_ut(julian_day, body_id)[0]
            deg_trop = res[0]
            final_deg = deg_trop
            
            if zodiac_type == 'Astronomik':
                swe.set_sid_mode(swe.SIDM_FAGAN_BRADLEY, 0, 0)
                res_sid = swe.calc_ut(julian_day, body_id)[0]
                final_deg = res_sid[0]
            elif zodiac_type == 'Drakonik':
                node_res = swe.calc_ut(julian_day, 10)[0]
                node_deg = node_res[0]
                final_deg = (deg_trop - node_deg + 360) % 360
            return final_deg

        def get_sign_name(degree):
            signs = ["Koç", "Boğa", "İkizler", "Yengeç", "Aslan", "Başak", "Terazi", "Akrep", "Yay", "Oğlak", "Kova", "Balık"]
            idx = int(degree // 30); rem = degree % 30; d = int(rem); m = int((rem - d) * 60)
            return f"{d}° {signs[idx]} {m}'"

        tjd_start = swe.julday(year, 1, 1); tjd_end = swe.julday(year, 12, 31)
        
        # Güneş Tutulmaları
        tjd = tjd_start
        while tjd < tjd_end:
            res = swe.sol_eclipse_when_glob(tjd)
            if res[0] == swe.FLG_SWIEPH:
                t_eclipse = res[1][0]
                if t_eclipse > tjd_end: break
                y, m, d, h_dec = swe.revjul(t_eclipse)
                h = int(h_dec); mn = int((h_dec - h) * 60)
                deg = get_zodiac_pos(t_eclipse, swe.SUN); sign_str = get_sign_name(deg)
                eclipses.append({"title": "Güneş Tutulması", "date_str": f"{d:02d}.{m:02d}.{y} {h:02d}:{mn:02d}", "sign_info": sign_info_fmt(sign_str, zodiac_type), "year":y, "month":m, "day":d, "hour":h, "minute":mn})
                tjd = t_eclipse + 25
            else: tjd += 25

        # Ay Tutulmaları
        tjd = tjd_start
        while tjd < tjd_end:
            res = swe.lun_eclipse_when(tjd)
            if res[0] == swe.FLG_SWIEPH:
                t_eclipse = res[1][0]
                if t_eclipse > tjd_end: break
                y, m, d, h_dec = swe.revjul(t_eclipse)
                h = int(h_dec); mn = int((h_dec - h) * 60)
                deg = get_zodiac_pos(t_eclipse, swe.MOON); sign_str = get_sign_name(deg)
                eclipses.append({"title": "Ay Tutulması", "date_str": f"{d:02d}.{m:02d}.{y} {h:02d}:{mn:02d}", "sign_info": sign_info_fmt(sign_str, zodiac_type), "year":y, "month":m, "day":d, "hour":h, "minute":mn})
                tjd = t_eclipse + 25
            else: tjd += 25

        # Yeni Ay / Dolunay
        t_search = tjd_start
        while t_search < tjd_end:
            res_sun = swe.calc_ut(t_search, swe.SUN)[0][0]; res_moon = swe.calc_ut(t_search, swe.MOON)[0][0]
            diff = (res_moon - res_sun + 360) % 360
            days_to_new = (360 - diff) / 12.2; days_to_full = (180 - diff + 360) % 360 / 12.2
            
            if days_to_new < days_to_full: target_tjd = t_search + days_to_new; type_str = "Yeni Ay"
            else: target_tjd = t_search + days_to_full; type_str = "Dolunay"
            
            for _ in range(3):
                r_sun = swe.calc_ut(target_tjd, swe.SUN)[0][0]; r_moon = swe.calc_ut(target_tjd, swe.MOON)[0][0]
                d_diff = (r_moon - r_sun + 360) % 360
                if type_str == "Dolunay":
                    err = (d_diff - 180)
                    while err > 180: err -= 360
                    while err < -180: err += 360
                else:
                    err = d_diff
                    if err > 180: err -= 360
                target_tjd -= (err / 12.19)
            
            if target_tjd >= tjd_start and target_tjd <= tjd_end:
                is_eclipse = False
                for ec in eclipses:
                    e_y, e_m, e_d = ec["year"], ec["month"], ec["day"]
                    t_y, t_m, t_d, _ = swe.revjul(target_tjd)
                    if e_y == t_y and e_m == t_m and abs(e_d - t_d) < 2: is_eclipse = True; break
                
                if not is_eclipse:
                    y, m, d, h_dec = swe.revjul(target_tjd)
                    h = int(h_dec); mn = int((h_dec - h) * 60)
                    deg = get_zodiac_pos(target_tjd, swe.MOON); sign_str = get_sign_name(deg)
                    phases.append({"title": type_str, "date_str": f"{d:02d}.{m:02d}.{y} {h:02d}:{mn:02d}", "sign_info": sign_info_fmt(sign_str, zodiac_type), "year":y, "month":m, "day":d, "hour":h, "minute":mn})
            
            t_search = target_tjd + 14
            
        eclipses.sort(key=lambda x: (x['year'], x['month'], x['day'])); phases.sort(key=lambda x: (x['year'], x['month'], x['day']))
        return jsonify({'success': True, 'eclipses': eclipses, 'phases': phases})
    except Exception as e: return jsonify({'success': False, 'error': str(e)})

def sign_info_fmt(sign_str, z_type): return f"{sign_str} ({z_type})"

@app.route('/load_celestial_event', methods=['POST'])
def load_celestial_event():
    try:
        title = request.form.get('title')
        year = int(request.form.get('year')); month = int(request.form.get('month')); day = int(request.form.get('day'))
        hour = int(request.form.get('hour')); minute = int(request.form.get('minute'))
        
        res_text, chart_data = ASTRO_MOTOR_NESNESİ.calculate_chart_data(year, month, day, hour, minute, 0.0, 0.0, 0.0, None, "P", "Astronomik")
        if chart_data:
            new_chart = {'id': len(session.get('active_charts', [])) + 1, 'name': title, 'year': year, 'month': month, 'day': day, 'hour': hour, 'minute': minute, 'tz_offset': 0.0, 'lat': 0.0, 'lon': 0.0, 'location_name': "Evrensel (UTC 0)", 'zodiac_type': "Astronomik", 'house_system': "Placidus", 'type': 'event'}
            current_charts = session.get('active_charts', [])
            current_charts.insert(0, new_chart)
            session['active_charts'] = current_charts
            
            sync_active_charts_to_db() # <--- KAYDETME EKLENDİ
            
            session['current_chart_index'] = 0; session['last_report'] = res_text; session['last_chart'] = chart_data; session['current_chart_data'] = new_chart
            return redirect(url_for('home', tab='aktif'))
    except Exception as e: print(e)
    return redirect(url_for('home'))

# ... (SİNASTRİ ve DİĞER ROTALAR AYNI KALDI) ...

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
                    
                    sync_active_charts_to_db() # <--- BURASI KRİTİK, EKLENDİ
                    
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
                
                raw_type = request.form.get('transit_type', 'Astronomik')
                t_type = 'Drakonik 28' if raw_type == 'Drakonik' else raw_type

                res, t_data = ASTRO_MOTOR_NESNESİ.calculate_chart_data(yr, mo, dy, hr, mn, tz, lat, lon, None, 'P', t_type)
                
                if t_data:
                    transit_chart = {'name': f"Transit ({dy}.{mo}.{yr} {hr}:{mn})", 'year': yr, 'month': mo, 'day': dy, 'hour': hr, 'minute': mn, 'tz_offset': tz, 'lat': lat, 'lon': lon, 'location_name': request.form.get('bar_loc_name'), 'zodiac_type': t_type, 'house_system': 'Placidus (P)', 'id': len(session.get('active_charts', [])) + 1, 'type': 'transit'}
                    
                    current_charts = session.get('active_charts', [])
                    current_charts.insert(0, transit_chart)
                    session['active_charts'] = current_charts
                    
                    sync_active_charts_to_db() # <--- BURASI KRİTİK, EKLENDİ
                    
                    session['current_chart_index'] = 0; session['last_chart'] = t_data; session['last_report'] = f"TRANSİT ({t_type})\n\n" + res; session['current_chart_data'] = transit_chart; active_tab = 'aktif'
            except Exception as e: session['report_error'] = str(e)
        
        elif active_tab == 'sinastri_compute':
             pass

        return redirect(url_for('home', tab=active_tab)) 

    # --- TRANSİT TAHMİNLERİNİ HESAPLA ---
    if context.get('last_chart'):
        try:
            c_data = session.get('current_chart_data', {})
            if c_data and c_data.get('year'):
                try:
                    safe_year = int(c_data['year']); safe_month = int(c_data['month']); safe_day = int(c_data['day']); safe_hour = int(c_data.get('hour', 12))
                    c_date = datetime.datetime(safe_year, safe_month, safe_day, safe_hour, 0)
                    preds = get_transit_predictions(c_date, context['last_chart']['planets'], ASTRO_MOTOR_NESNESİ)
                    context['transit_forecasts'] = preds
                except ValueError as ve: print(f"DEBUG HATA (Tarih Formatı): {ve}")
        except Exception as e: print(f"DEBUG HATA (Transit Motoru): {e}")

    context['last_chart'] = session.get('last_chart')
    context['report_error'] = session.pop('report_error', None)
    context['report_success'] = True if context['last_chart'] else False
    return render_template('layout.html', **context)

# ... (DİĞER ROTALAR AYNI KALDI) ...

@app.route('/delete_active_chart/<int:index>')
def delete_active_chart(index):
    active_charts = session.get('active_charts', [])
    if 0 <= index < len(active_charts):
        del active_charts[index]
        session['active_charts'] = active_charts
        session.modified = True 
        
        sync_active_charts_to_db() # <--- VERİTABANINDAN DA SİL
        
        current_index = session.get('current_chart_index', 0)
        if current_index >= len(active_charts):
            session['current_chart_index'] = max(0, len(active_charts) - 1)
        
        if len(active_charts) == 0:
            session.pop('last_chart', None); session.pop('last_report', None); session.pop('current_chart_data', None)
        elif current_index == index:
            new_index = min(index, len(active_charts) - 1)
            if new_index >= 0: return redirect(url_for('set_active_chart', index=new_index))
    
    return redirect(url_for('home', tab='aktif'))

# ... (SONDAKİ MAIN BLOĞU AYNI) ...

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000)) 
    app.run(host='0.0.0.0', port=port, debug=True)

