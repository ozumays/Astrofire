import math
import traceback
import os
import sys
from datetime import datetime, timedelta, timezone

# ============================================================================
# 📂 YARDIMCI FONKSİYONLAR
# ============================================================================

# Eğer yardimcilar.py yoksa hata vermesin diye buraya basic halini koyuyoruz
try:
    from yardimcilar import decimal_to_dms_string
except ImportError:
    def decimal_to_dms_string(deg):
        d = int(deg)
        m = int((deg - d) * 60)
        return f"{d}° {m}'"

# ============================================================================
# 📂 KLASÖR VE SWISSEPH AYARLARI
# ============================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EPHE_PATH = os.path.join(BASE_DIR, 'ephe')
os.environ['SE_EPHE_PATH'] = EPHE_PATH

try:
    import swisseph as swe
    swe.set_ephe_path(EPHE_PATH)
    HAS_SWEPH = True
except ImportError:
    swe = None
    HAS_SWEPH = False

# ============================================================================
# ⭐ SABİT VERİLER (YILDIZLAR, GEZEGENLER, SINIRLAR)
# ============================================================================

try:
    from fixed_stars_data import FIXED_STARS_CALC_LIST
    FIXED_STARS_LIST = FIXED_STARS_CALC_LIST
except ImportError:
    FIXED_STARS_LIST = ["Aldebaran", "Regulus", "Antares", "Fomalhaut", "Sirius", "Spica", "Vega"]

PLANET_IDS_MAP = {
    "Güneş": (swe.SUN, '☉'), "Ay": (swe.MOON, '☽'), "Merkür": (swe.MERCURY, '☿'),
    "Venüs": (swe.VENUS, '♀'), "Mars": (swe.MARS, '♂'), "Jüpiter": (swe.JUPITER, '♃'),
    "Satürn": (swe.SATURN, '♄'), "Uranüs": (swe.URANUS, '⛢'),
    "Neptün": (swe.NEPTUNE, '♆'), "Plüton": (swe.PLUTO, '♇'),
    "Kuzey Düğümü": (swe.MEAN_NODE, '☊')
}

ASTEROID_IDS_MAP = {
    "Chiron": (swe.CHIRON, '⚷'), 
    "Ceres": (swe.CERES, '⚳'), 
    "Pallas": (swe.PALLAS, '⚴'),
    "Juno": (swe.JUNO, '⚵'), 
    "Vesta": (swe.VESTA, '⚶'),
    "Eros": (10433, '⚺'),      
    "Psyche": (10016, 'ψ'),    
    "Lilith (Ast)": (11181, '⚸') 
}

# --- ASTRONOMİK SINIRLAR ---
BASE_IAU_1930_BOUNDARIES = [
    ("Koç", 28.69, 53.42), ("Boğa", 53.42, 90.14), ("İkizler", 90.14, 117.99),
    ("Yengeç", 117.99, 138.04), ("Aslan", 138.04, 173.85), ("Başak", 173.85, 217.81),
    ("Terazi", 217.81, 241.05), ("Akrep", 241.05, 266.24), ("Yay", 266.24, 299.66),    
    ("Oğlak", 299.66, 327.49), ("Kova", 327.49, 351.65), ("Balık", 351.65, 28.69)
]

PRESESYON_HIZI_YILLIK = 0.0139694
CURRENT_BOUNDARIES = []

def update_boundaries_for_year(target_year):
    global CURRENT_BOUNDARIES
    years_diff = target_year - 1930
    shift_amount = years_diff * PRESESYON_HIZI_YILLIK
    updated_list = []
    for name, start, end in BASE_IAU_1930_BOUNDARIES:
        new_start = (start + shift_amount) % 360.0
        new_end = (end + shift_amount) % 360.0
        updated_list.append((name, new_start, new_end))
    CURRENT_BOUNDARIES = updated_list

def get_aries_start_degree_for_year(target_year):
    years_diff = target_year - 1930
    shift_amount = years_diff * PRESESYON_HIZI_YILLIK
    return (28.69 + shift_amount) % 360.0

def get_relative_degree(lon, zodiac_type="Astronomik"):
    lon %= 360
    if zodiac_type == "Tropical":
        signs = ["Koç", "Boğa", "İkizler", "Yengeç", "Aslan", "Başak", "Terazi", "Akrep", "Yay", "Oğlak", "Kova", "Balık"]
        idx = int(lon / 30)
        return signs[idx % 12], lon % 30, decimal_to_dms_string(lon % 30)

    # Astronomik ve Drakonik tipler için Astronomik sınırlar kullanılır
    boundaries = CURRENT_BOUNDARIES if CURRENT_BOUNDARIES else BASE_IAU_1930_BOUNDARIES
    for name, start, end in boundaries:
        if start < end:
            if start <= lon < end: return name, lon - start, decimal_to_dms_string(lon - start)
        else:
            if lon >= start or lon < end: 
                deg = (lon - start + 360) % 360
                return name, deg, decimal_to_dms_string(deg)
    return "Bilinmeyen", 0.0, "0° 00'"

# ============================================================================
# ⚙️ ANA MOTOR SINIFI
# ============================================================================

class AstroHesaplamaMotoru:
    def __init__(self):
        self.PLANET_IDS = PLANET_IDS_MAP
        self.ASTEROID_IDS = ASTEROID_IDS_MAP
        self.FIXED_STARS = FIXED_STARS_LIST
        self.HOUSE_SYSTEMS = {"Koch (K)": 'K', "Whole Sign (W)": 'W', "Placidus (P)": 'P'}
    
    def get_house_of_point(self, lon, houses_dict):
        for i in range(1, 13):
            c_start = houses_dict[f'CUSP{i}']
            c_next = houses_dict[f'CUSP{(i%12)+1}']
            if c_start < c_next:
                if c_start <= lon < c_next: return i
            else:
                if lon >= c_start or lon < c_next: return i
        return 0

    def calculate_whole_sign_cusps(self, asc_lon, zodiac_type):
        asc_sign_name, _, _ = get_relative_degree(asc_lon, zodiac_type)
        whole_sign_cusps = {}; cusp_lons = []

        if zodiac_type == "Tropical":
            signs_order = ["Koç", "Boğa", "İkizler", "Yengeç", "Aslan", "Başak", "Terazi", "Akrep", "Yay", "Oğlak", "Kova", "Balık"]
            try: start_index = signs_order.index(asc_sign_name)
            except: start_index = 0
            for i in range(12):
                val = ((start_index + i) * 30.0) % 360.0
                whole_sign_cusps[f'CUSP{i+1}'] = val
                cusp_lons.append(val)
        else:
            boundaries = CURRENT_BOUNDARIES if CURRENT_BOUNDARIES else BASE_IAU_1930_BOUNDARIES
            start_index = 0
            for i, (name, s, e) in enumerate(boundaries):
                if name == asc_sign_name: start_index = i; break
            for i in range(12):
                current_idx = (start_index + i) % len(boundaries)
                cusp_val = boundaries[current_idx][1]
                whole_sign_cusps[f'CUSP{i+1}'] = cusp_val
                cusp_lons.append(cusp_val)
        return cusp_lons, whole_sign_cusps

    # --- 1. TEKLİ HARİTA HESAPLAMA ---
    def calculate_chart_data(self, year, month, day, hour, minute, tz_offset, lat, lon, active_charts_ref, house_system_code, zodiak_type="Astronomik"):
        if not HAS_SWEPH: return "Kütüphane eksik.", None
        update_boundaries_for_year(year)
        positions = {"planets": {}, "cusps": {}, "houses": {}, "fixed_stars": {}}
        
        try:
            local_dt_naive = datetime(year, month, day, hour, minute)
            utc_dt = local_dt_naive - timedelta(hours=tz_offset)
            jd_ut = swe.utc_to_jd(utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour, utc_dt.minute, utc_dt.second, 1)[1]
        except Exception as e: return f"Zaman hesaplama hatası: {e}", None

        try:
            cusps_tropical, ascmc_tropical = swe.houses(jd_ut, lat, lon, b'P')
            asc_raw = ascmc_tropical[0]; mc_raw = ascmc_tropical[1]
            nn_raw = swe.calc_ut(jd_ut, swe.MEAN_NODE, swe.FLG_SWIEPH | swe.FLG_SPEED)[0][0] % 360

            shift_delta = 0.0
            
            if zodiak_type == "Drakonik 28":
                aries_start_deg = get_aries_start_degree_for_year(year)
                shift_delta = aries_start_deg - nn_raw
            elif zodiak_type == "Drakonik 0":
                shift_delta = 0.0 - nn_raw

        except Exception as e: return f"Ev sistemi hatası: {e}", None

        asc_calc = (asc_raw + shift_delta) % 360.0
        mc_calc = (mc_raw + shift_delta) % 360.0
        
        if house_system_code == 'W':
            _, ws_dict = self.calculate_whole_sign_cusps(asc_calc, zodiak_type)
            for k, v in ws_dict.items():
                positions['houses'][k] = v; positions['cusps'][k] = v
        else:
            sys_code = house_system_code.encode('utf-8')
            cusps_calc_raw, _ = swe.houses(jd_ut, lat, lon, sys_code)
            for i in range(1, 13):
                raw_val = cusps_calc_raw[i-1]
                final_val = (raw_val + shift_delta) % 360.0
                positions['houses'][f'CUSP{i}'] = final_val; positions['cusps'][f'CUSP{i}'] = final_val

        positions["cusps"]["ASC"] = asc_calc; positions["cusps"]["MC"] = mc_calc
        positions["cusps"]["NN"] = (nn_raw + shift_delta) % 360.0

        PLANET_FLAG = swe.FLG_SWIEPH | swe.FLG_SPEED
        
        for isim, (swe_id, glyph) in self.PLANET_IDS.items():
            abs_degree = 0.0; speed = 0.0
            if isim == 'Kuzey Düğümü': abs_degree = positions["cusps"]["NN"]
            else:
                try:
                    calc_res, flg = swe.calc_ut(jd_ut, swe_id, PLANET_FLAG)
                    tropical_deg = calc_res[0] % 360.0; speed = calc_res[3]
                    abs_degree = (tropical_deg + shift_delta) % 360.0
                except: pass

            const, rel_deg, rel_fmt = get_relative_degree(abs_degree, zodiak_type)
            is_retro = speed < 0 if isim not in ["Güneş", "Ay", "Kuzey Düğümü"] else False
            rx_glyph = "R" if is_retro else ""
            house_num = self.get_house_of_point(abs_degree, positions['houses'])
            positions["planets"][isim] = (abs_degree, glyph, rel_deg, const, rel_fmt, rx_glyph, f"{house_num}. Ev")

        for isim, (swe_id, glyph) in self.ASTEROID_IDS.items():
            try:
                calc_res, flg = swe.calc_ut(jd_ut, swe_id, PLANET_FLAG)
                tropical_deg = calc_res[0] % 360.0; speed = calc_res[3]
                abs_degree = (tropical_deg + shift_delta) % 360.0
                const, rel_deg, rel_fmt = get_relative_degree(abs_degree, zodiak_type)
                is_retro = speed < 0; rx_glyph = "R" if is_retro else ""
                house_num = self.get_house_of_point(abs_degree, positions['houses'])
                positions["planets"][isim] = (abs_degree, glyph, rel_deg, const, rel_fmt, rx_glyph, f"{house_num}. Ev")
            except: pass

        try:
            sn_lon = (positions["cusps"]["NN"] + 180) % 360.0
            const_sn, rel_sn, fmt_sn = get_relative_degree(sn_lon, zodiak_type)
            house_sn = self.get_house_of_point(sn_lon, positions['houses'])
            positions["planets"]["Güney Düğümü"] = (sn_lon, '☋', rel_sn, const_sn, fmt_sn, "", f"{house_sn}. Ev")
        except: pass
        
        for star_name in self.FIXED_STARS:
            try:
                search_name = star_name if "," in star_name else star_name + ","
                star_res = swe.fixstar_ut(search_name, jd_ut, swe.FLG_SWIEPH)
                if star_res[1]: 
                    tropical_deg = star_res[0][0] % 360.0
                    abs_degree = (tropical_deg + shift_delta) % 360.0
                    const, rel_deg, rel_fmt = get_relative_degree(abs_degree, zodiak_type)
                    house_num = self.get_house_of_point(abs_degree, positions['houses'])
                    positions["fixed_stars"][star_name] = (abs_degree, '*', rel_deg, const, rel_fmt, "", f"{house_num}. Ev")
            except: pass

        final_boundaries = []
        if zodiak_type == "Tropical": 
            final_boundaries = [("Koç",0,30), ("Boğa",30,60), ("İkizler",60,90), ("Yengeç",90,120), ("Aslan",120,150), ("Başak",150,180), ("Terazi",180,210), ("Akrep",210,240), ("Yay",240,270), ("Oğlak",270,300), ("Kova",300,330), ("Balık",330,360)]
        else: 
            final_boundaries = CURRENT_BOUNDARIES if CURRENT_BOUNDARIES else BASE_IAU_1930_BOUNDARIES
        positions["boundaries"] = [{"name": b[0], "start": b[1], "end": b[2]} for b in final_boundaries]

        return "Hesaplama Başarılı", positions

    # --- 2. SİNASTRİ AÇILARI (BU METOD ARTIK SINIFIN İÇİNDE) ---
    def calculate_synastry_aspects(self, chart1, chart2):
        """
        İki harita arasındaki açıları hesaplar.
        chart1 ve chart2 = calculate_chart_data'dan dönen 'positions' sözlükleri olmalıdır.
        """
        report = []
        
        ASPECTS = {
            'Kavuşum': {'orb': 8, 'angle': 0},
            'Karşıt':  {'orb': 8, 'angle': 180},
            'Üçgen':   {'orb': 8, 'angle': 120},
            'Kare':    {'orb': 7, 'angle': 90},
            'Sekstil': {'orb': 5, 'angle': 60}
        }

        PLANETS = ['Güneş', 'Ay', 'Merkür', 'Venüs', 'Mars', 'Jüpiter', 
                   'Satürn', 'Uranüs', 'Neptün', 'Plüton', 'Kuzey Düğümü']

        p1_list = chart1.get('planets', {})
        p2_list = chart2.get('planets', {})

        for p1_name in PLANETS:
            if p1_name not in p1_list: continue
            
            data1 = p1_list[p1_name]
            deg1 = data1[0]  
            sign1 = data1[3] 

            for p2_name in PLANETS:
                if p2_name not in p2_list: continue
                
                data2 = p2_list[p2_name]
                deg2 = data2[0]
                sign2 = data2[3]

                diff = abs(deg1 - deg2)
                if diff > 180: diff = 360 - diff

                for asp, params in ASPECTS.items():
                    if (params['angle'] - params['orb']) <= diff <= (params['angle'] + params['orb']):
                        orb_val = abs(diff - params['angle'])
                        
                        report.append({
                            'p1': p1_name, 'p1_sign': sign1,
                            'p2': p2_name, 'p2_sign': sign2,
                            'aspect': asp, 'orb': round(orb_val, 2),
                            'text': f"{p1_name} ({sign1}) - {p2_name} ({sign2}): {asp}"
                        })
                        break 
        return report

    # --- 3. HARİTA BİRLEŞTİRME (MULTI WHEEL / KOMPOZİT) ---
    def calculate_synastry_chart(self, c1, c2, c3=None, c_type="Sinastri"):
        # c1 ve c2 veritabanı veya hesaplama sonucu nesnelerdir.
        # Genelde 'data' anahtarı içinde saklanır.
        d1 = c1.get('data') if isinstance(c1, dict) else c1
        d2 = c2.get('data') if isinstance(c2, dict) else c2
        d3 = c3.get('data') if isinstance(c3, dict) and c3 else c3
        
        if not d1 or not d2: return "Veri eksik", None

        if c_type == "Sinastri":
            result_data = {
                'type': 'multi-wheel',
                'ring_count': 2,
                'p1': d1['planets'],
                'p2': d2['planets'],
                'cusps': d1['cusps'],
                'houses': d1['houses']
            }
            if d3:
                result_data['ring_count'] = 3
                result_data['p3'] = d3['planets']
            return "Çoklu Harita", result_data

        elif c_type == "Kompozit":
            comp = {}
            all_planets = list(d1['planets'].keys())
            for p in all_planets:
                if p in d2['planets']:
                    deg1 = d1['planets'][p][0]; deg2 = d2['planets'][p][0]
                    
                    if d3 and p in d3['planets']:
                        deg3 = d3['planets'][p][0]
                        x = (math.cos(math.radians(deg1)) + math.cos(math.radians(deg2)) + math.cos(math.radians(deg3)))
                        y = (math.sin(math.radians(deg1)) + math.sin(math.radians(deg2)) + math.sin(math.radians(deg3)))
                        mid = math.degrees(math.atan2(y, x)) % 360.0
                    else:
                        diff = abs(deg1 - deg2)
                        mid = ((deg1 + deg2 + 360)/2 if diff > 180 else (deg1+deg2)/2) % 360
                    
                    const, rel, fmt = get_relative_degree(mid, "Astronomik")
                    glyph = d1['planets'][p][1]
                    comp[p] = (mid, glyph, rel, const, fmt, "", "")
            
            return "Kompozit", {'type': 'single', 'planets': comp, 'cusps': {}, 'houses': {}}
        
        return "Hata", None

    # --- 4. SECONDARY PROGRESSION (İKİNCİL İLERLETİM) ---
    def calculate_secondary_progression(self, natal_year, natal_month, natal_day, 
                                       natal_hour, natal_minute, natal_tz,
                                       target_year, target_month, target_day,
                                       lat, lon, house_system_code='P', zodiac_type='Astronomik'):
        """
        Secondary Progression: Her yaşanan yıl = Doğum gününden 1 gün sonrası
        Örnek: 30 yaşındaysanız, doğum gününüzden 30 gün sonraki gezegen pozisyonları kullanılır
        """
        from datetime import date
        
        # Yaşı hesapla
        birth_date = date(natal_year, natal_month, natal_day)
        target_date = date(target_year, target_month, target_day)
        age_in_days = (target_date - birth_date).days
        age_in_years = age_in_days / 365.25
        
        # Doğum tarihinden age_in_years gün sonrası = progression tarihi
        prog_date = birth_date + timedelta(days=int(age_in_years))
        
        # O tarihteki gezegen pozisyonlarını hesapla (doğum saati kullanılır)
        return self.calculate_chart_data(
            prog_date.year, prog_date.month, prog_date.day,
            natal_hour, natal_minute, natal_tz,
            lat, lon, None, house_system_code, zodiac_type
        )
    
    # --- 5. SOLAR ARC PROGRESSION (GÜNEŞ YAYI) ---
    def calculate_solar_arc_progression(self, natal_year, natal_month, natal_day,
                                       natal_hour, natal_minute, natal_tz,
                                       target_year, target_month, target_day,
                                       lat, lon, house_system_code='P', zodiac_type='Astronomik'):
        """
        Solar Arc: Doğumdan bugüne kadar geçen her yıl için tüm gezegenlere 1 derece eklenir
        """
        from datetime import date
        
        # 1. Natal haritayı hesapla
        _, natal_data = self.calculate_chart_data(
            natal_year, natal_month, natal_day, natal_hour, natal_minute, natal_tz,
            lat, lon, None, house_system_code, zodiac_type
        )
        
        if not natal_data:
            return "Natal hesaplama başarısız", None
        
        # 2. Yaşı hesapla
        birth_date = date(natal_year, natal_month, natal_day)
        target_date = date(target_year, target_month, target_day)
        age_in_years = (target_date - birth_date).days / 365.25
        
        # 3. Solar Arc = age_in_years derece
        arc_degrees = age_in_years
        
        # 4. Yeni pozisyonları oluştur (her gezegene arc_degrees ekle)
        progressed_data = {
            'planets': {},
            'cusps': {},
            'houses': {},
            'fixed_stars': {},
            'boundaries': natal_data.get('boundaries', [])
        }
        
        # Gezegenleri ilerlet
        for planet_name, planet_data in natal_data['planets'].items():
            natal_lon = planet_data[0]
            progressed_lon = (natal_lon + arc_degrees) % 360.0
            
            # Yeni burç bilgisini hesapla
            const, rel_deg, rel_fmt = get_relative_degree(progressed_lon, zodiac_type)
            
            # Ev numarasını hesapla (evler de ilerletilecek, o yüzden eski ev sistemini kullan)
            progressed_data['planets'][planet_name] = (
                progressed_lon,  # yeni derece
                planet_data[1],  # glyph
                rel_deg,         # relative degree
                const,           # burç adı
                rel_fmt,         # formatted string
                planet_data[5],  # retrograde
                planet_data[6]   # ev bilgisi güncellenecek
            )
        
        # Ev köşelerini ilerlet
        for cusp_key, cusp_lon in natal_data['cusps'].items():
            progressed_cusp_lon = (cusp_lon + arc_degrees) % 360.0
            progressed_data['cusps'][cusp_key] = progressed_cusp_lon
            progressed_data['houses'][cusp_key] = progressed_cusp_lon
        
        # Ev numaralarını güncelle
        for planet_name in progressed_data['planets']:
            p_lon = progressed_data['planets'][planet_name][0]
            house_num = self.get_house_of_point(p_lon, progressed_data['houses'])
            
            # Tuple'ı listeye çevir, güncelle, tekrar tuple yap
            temp_list = list(progressed_data['planets'][planet_name])
            temp_list[6] = f"{house_num}. Ev"
            progressed_data['planets'][planet_name] = tuple(temp_list)
        
        # Sabit yıldızlar için (isteğe bağlı - genelde kullanılmaz ama ekleyelim)
        for star_name, star_data in natal_data.get('fixed_stars', {}).items():
            natal_star_lon = star_data[0]
            progressed_star_lon = (natal_star_lon + arc_degrees) % 360.0
            const, rel_deg, rel_fmt = get_relative_degree(progressed_star_lon, zodiac_type)
            house_num = self.get_house_of_point(progressed_star_lon, progressed_data['houses'])
            
            progressed_data['fixed_stars'][star_name] = (
                progressed_star_lon,
                star_data[1],
                rel_deg,
                const,
                rel_fmt,
                star_data[5],
                f"{house_num}. Ev"
            )
        
        return f"Solar Arc Progression: {arc_degrees:.2f}° eklenmiştir", progressed_data

    # --- 6. RETURN (DÖNÜŞ) HARİTASI ---
    def find_return_charts(self, natal_jd, planet_id, start_year, end_year, target_lon, flags=swe.FLG_SWIEPH):
        returns = []
        current_scan_jd = swe.julday(start_year, 1, 1)
        limit_jd = swe.julday(end_year + 1, 1, 1)
        
        period_map = {
            swe.SUN: 365.242, swe.MOON: 27.32, swe.MERCURY: 88, 
            swe.VENUS: 225, swe.MARS: 687, swe.JUPITER: 4333, swe.SATURN: 10759
        }
        avg_period = period_map.get(planet_id, 365.25)
        
        safety_break = 0
        while current_scan_jd < limit_jd and safety_break < 5000:
            safety_break += 1
            t_check = current_scan_jd
            step = 1.0 if planet_id == swe.MOON else 5.0
            if planet_id in [swe.MERCURY, swe.VENUS]: step = 2.0
            
            search_window = avg_period * 1.1
            found_in_cycle = False
            
            for _ in range(int(search_window / step) + 5):
                try:
                    pos1 = swe.calc_ut(t_check, planet_id, flags)[0][0]
                    pos2 = swe.calc_ut(t_check + step, planet_id, flags)[0][0]
                except:
                    t_check += step; continue
                
                diff1 = (pos1 - target_lon + 180) % 360 - 180
                diff2 = (pos2 - target_lon + 180) % 360 - 180
                
                if (diff1 * diff2 < 0) and (abs(diff1 - diff2) < 180):
                    low = t_check; high = t_check + step
                    found_jd = high
                    for _ in range(20):
                        mid = (low + high) / 2.0
                        p_mid = swe.calc_ut(mid, planet_id, flags)[0][0]
                        diff_mid = (p_mid - target_lon + 180) % 360 - 180
                        p_low = swe.calc_ut(low, planet_id, flags)[0][0]
                        d_low = (p_low - target_lon + 180) % 360 - 180
                        if d_low * diff_mid < 0: high = mid
                        else: low = mid
                        found_jd = high
                    
                    y, m, d, h_dec = swe.revjul(found_jd)
                    h = int(h_dec); mn = int((h_dec - h) * 60)
                    
                    if start_year <= y <= end_year:
                        returns.append({
                            'year': y, 'month': m, 'day': d, 
                            'hour': h, 'minute': mn, 'jd': found_jd,
                            'date_str': f"{d:02d}.{m:02d}.{y} {h:02d}:{mn:02d}"
                        })
                    
                    found_in_cycle = True
                    jump_factor = 0.8 if planet_id in [swe.MERCURY, swe.VENUS] else 0.9
                    current_scan_jd = found_jd + (avg_period * jump_factor)
                    break
                t_check += step
            if not found_in_cycle: current_scan_jd += avg_period
    
        return returns

# Global Nesne
ASTRO_MOTOR_NESNESİ = AstroHesaplamaMotoru()
__all__ = ['ASTRO_MOTOR_NESNESİ', 'get_relative_degree']
