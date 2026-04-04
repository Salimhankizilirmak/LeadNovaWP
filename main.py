# LeadNova uçuşa hazır! 🚀
from flask import Flask, request, jsonify, render_template
import os
import datetime
from datetime import timezone, timedelta
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from apscheduler.schedulers.background import BackgroundScheduler
import time


app = Flask(__name__)

# --- GOOGLE TAKVİM AYARLARI ---
SCOPES = ['https://www.googleapis.com/auth/calendar']
CREDENTIALS_FILE = 'service_account.json'
# Eğer yukarıdaki adımlarda botu kendi ana takviminle paylaştıysan 'primary' yerine kendi Gmail adresini yazmalısın. 
# (Örn: 'leadnova@gmail.com')
CALENDAR_ID = 'salimhankizilirmak@gmail.com' 

# Kullanıcı durumları
user_states = {}

MAIN_MENU = """*LeadNova Systems’e hoş geldiniz!* 🚀

Size en hızlı şekilde yardımcı olabilmemiz için lütfen sektörünüzü seçin:
1️⃣ Emlak
2️⃣ Güzellik Merkezi
3️⃣ Klinik
4️⃣ Sanayi
5️⃣ Galeri (Araç Satış)

👉 Lütfen bir seçim yapın."""


SUB_MENUS = {
    "1": "🏡 *Emlak hizmetlerimiz:*\n1 - Satılık Evler\n2 - Kiralık Evler\n3 - Satılık Arsalar\n4 - Fiyat Bilgisi Al\n5 - Randevu Oluştur\n0 - Canlı Destek",
    "2": "✨ *Güzellik Merkezi Hizmetlerimiz:*\n1 - Lazer Epilasyon\n2 - Cilt Bakımı\n3 - Ağda\n4 - Kuaför Hizmetleri\n5 - Tırnak / Nail Art\n6 - Fiyat Bilgisi\n7 - Randevu Oluştur\n0 - Canlı Destek",
    "3": "🏥 *Klinik Hizmetlerimiz:*\n1 - Estetik İşlemler\n2 - Diş Tedavileri\n3 - Cilt Uygulamaları\n4 - Bilgi Al\n5 - Randevu Oluştur\n0 - Canlı Destek",
    "4": "⚙️ *Sanayi - Size nasıl yardımcı olabiliriz?*\n1 - Ürün / Hizmet Bilgisi\n2 - Teklif Al\n3 - Proje Danışmanlığı\n4 - Yetkili ile Görüş\n0 - Canlı Destek",
    "5": "🚗 *Galeri - Araç seçeneklerimiz:*\n1 - Satılık Araçlar\n2 - Araç Fiyatları\n3 - Takas İmkanları\n4 - Test Sürüşü / Randevu\n0 - Canlı Destek"
}

# --- TAKİP (FOLLOW-UP) MESAJLARI ---
FOLLOWUP_1_HOUR = "Size yardımcı olabilmemiz için buradayız 🙂\nİsterseniz size özel bilgi verebiliriz."
FOLLOWUP_1_DAY = "🎁 Bugüne özel fırsatlarımız devam ediyor.\nBilgi almak ister misiniz?"

# Zamanlayıcıyı başlatıyoruz
scheduler = BackgroundScheduler(daemon=True)
scheduler.start()

def send_proactive_message(session_id, message_text):
    """
    Bu fonksiyon ileride doğrudan Meta (WhatsApp) API'sine bağlanacak.
    Şu an web demosu kullandığımız için konsola logluyoruz.
    """
    print(f"\n[🚀 OTOMATİK TAKİP MESAJI GÖNDERİLDİ] -> {session_id}")
    print(f"Mesaj: {message_text}\n")

def check_followups():
    """
    Arka planda her dakika çalışıp müşterilerin son etkileşim sürelerini kontrol eden beyin.
    """
    now = datetime.datetime.now()
    for session_id, data in list(user_states.items()):
        # Sadece sözlük (dict) yapısına geçirdiğimiz kullanıcıları kontrol et
        if isinstance(data, dict):
            last_active = data.get("last_active")
            if not last_active: continue
            
            # Eğer müşteri 1 saat (3600 saniye) boyunca yazmadıysa ve 1. takip atılmadıysa
            if not data.get("f1_sent") and (now - last_active).total_seconds() >= 3600:
                send_proactive_message(session_id, FOLLOWUP_1_HOUR)
                data["f1_sent"] = True
                
            # Eğer müşteri 1 gün (86400 saniye) boyunca yazmadıysa ve 2. takip atılmadıysa
            elif not data.get("f2_sent") and (now - last_active).total_seconds() >= 86400:
                send_proactive_message(session_id, FOLLOWUP_1_DAY)
                data["f2_sent"] = True

# Zamanlayıcıya bu kontrol görevini her 1 dakikada bir yapmasını söylüyoruz
scheduler.add_job(check_followups, 'interval', minutes=1)


DATE_MENU = """📅 Randevu oluşturmak için lütfen gün seçiniz:
1️⃣ Bugün
2️⃣ Yarın"""

TIME_MENU = """⏰ Lütfen saat seçiniz:
1️⃣ 10:00
2️⃣ 13:00
3️⃣ 15:00
4️⃣ 18:00"""


def create_calendar_event(date_choice, time_choice, session_id):
    try:
        # Tarihi hesapla
        today = datetime.date.today()
        if date_choice == "1":
            target_date = today
        elif date_choice == "2":
            target_date = today + datetime.timedelta(days=1)
        elif date_choice == "3":
            target_date = today + datetime.timedelta(days=2)
            
        # Saati belirle
        time_mapping = {"1": "10:00:00", "2": "13:00:00", "3": "15:00:00", "4": "18:00:00"}

        target_time = time_mapping[time_choice]
        
        start_datetime = f"{target_date}T{target_time}+03:00" # Türkiye saati
        
        # Bitiş saati (1 saat sonrası)
        start_dt = datetime.datetime.strptime(f"{target_date} {target_time}", "%Y-%m-%d %H:%M:%S")
        end_dt = start_dt + datetime.timedelta(hours=1)
        end_datetime = f"{end_dt.strftime('%Y-%m-%d')}T{end_dt.strftime('%H:%M:%S')}+03:00"

        # API Bağlantısı
        service_account_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
        if service_account_json:
            import json
            service_account_info = json.loads(service_account_json)
            creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
        else:
            creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
            
        service = build('calendar', 'v3', credentials=creds)
        
        event = {
            'summary': f'Müşteri Randevusu ({session_id})',
            'description': 'LeadNova Otomasyon Sisteminden alındı.',
            'start': {'dateTime': start_datetime, 'timeZone': 'Europe/Istanbul'},
            'end': {'dateTime': end_datetime, 'timeZone': 'Europe/Istanbul'},
            'reminders': {
                'useDefault': False,
                'overrides': [{'method': 'popup', 'minutes': 15}],
            },
        }
        
        service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        return True
    except Exception as e:
        print(f"Takvim oluşturma hatası: {e}")
        return False

def handle_message(session_id, incoming_msg):
    incoming_msg = incoming_msg.strip()
    
    # RESET VE YENİ KULLANICI KONTROLÜ
    is_new_user = session_id not in user_states
    is_reset_msg = incoming_msg.lower() in ["menü", "menu", "merhaba", "selam"]

    # KULLANICIYI KAYDETME VE SON AKTİVİTEYİ GÜNCELLEME
    if is_new_user:
        user_states[session_id] = {
            "state": "MAIN_MENU",
            "last_active": datetime.datetime.now(),
            "f1_sent": False,
            "f2_sent": False
        }
    else:
        # Eski basit string yapısını yeni sözlük yapısına çevir (Hata almamak için)
        if not isinstance(user_states[session_id], dict):
            user_states[session_id] = {
                "state": user_states[session_id],
                "last_active": datetime.datetime.now(),
                "f1_sent": False,
                "f2_sent": False
            }
        user_states[session_id]["last_active"] = datetime.datetime.now()

    # Eğer yeni kullanıcıysa veya reset kelimesi yazdıysa ANA MENÜ'ye zorla
    if is_new_user or is_reset_msg:
        user_states[session_id]["state"] = "MAIN_MENU"
        return MAIN_MENU

    # Artık current_state'i sözlüğün içinden okuyoruz
    current_state = user_states[session_id]["state"]

    if incoming_msg == "0":
        user_states[session_id]["state"] = "LIVE_SUPPORT"
        return "Sizi müşteri temsilcimize aktarıyorum. Lütfen bekleyin... 🎧"

    # --- ANA MENÜ ---
    if current_state == "MAIN_MENU":
        if incoming_msg in SUB_MENUS:
            user_states[session_id]["state"] = f"SUB_MENU_{incoming_msg}"
            return SUB_MENUS[incoming_msg]
        else:
            return "Lütfen geçerli bir numara tuşlayın (1-5).\n\n" + MAIN_MENU

    # --- ALT MENÜLER VE VERİ TOPLAMA/RANDEVU YÖNLENDİRMELERİ ---
    
    # 1. EMLAK
    if current_state == "SUB_MENU_1":
        if incoming_msg in ["1", "2", "3"]:
            user_states[session_id]["state"] = "AWAITING_INFO"
            return INFO_PROMPTS["emlak_satilik"]
        elif incoming_msg == "5":
            user_states[session_id]["state"] = "SELECT_DATE"
            return DATE_MENU
            
    # 2. GÜZELLİK MERKEZİ
    elif current_state == "SUB_MENU_2":
        if incoming_msg == "1": # Lazer alt menüsü
            user_states[session_id]["state"] = "SUB_MENU_LAZER"
            return "✨ Lazer epilasyon hakkında:\n1 - Fiyat bilgisi al\n2 - Randevu oluştur\n\n🎁 Bugün randevu oluşturan müşterilerimize özel indirim uygulanmaktadır."
        elif incoming_msg == "7":
            user_states[session_id]["state"] = "SELECT_DATE"
            return DATE_MENU
            
    # 2.1 GÜZELLİK MERKEZİ -> LAZER ALT MENÜSÜ
    elif current_state == "SUB_MENU_LAZER":
        if incoming_msg == "2":
            user_states[session_id]["state"] = "SELECT_DATE"
            return DATE_MENU

    # 3. KLİNİK
    elif current_state == "SUB_MENU_3":
        if incoming_msg == "4":
            user_states[session_id]["state"] = "AWAITING_INFO"
            return INFO_PROMPTS["klinik_bilgi"]
        elif incoming_msg == "5":
            user_states[session_id]["state"] = "SELECT_DATE"
            return DATE_MENU

    # 4. SANAYİ
    elif current_state == "SUB_MENU_4":
        if incoming_msg == "2":
            user_states[session_id]["state"] = "AWAITING_INFO"
            return INFO_PROMPTS["sanayi_teklif"]

    # 5. GALERİ
    elif current_state == "SUB_MENU_5":
        if incoming_msg == "1":
            user_states[session_id]["state"] = "AWAITING_INFO"
            return INFO_PROMPTS["galeri_arac"]
        elif incoming_msg == "4":
            user_states[session_id]["state"] = "SELECT_DATE"
            return DATE_MENU

    # --- VERİ TOPLAMA (Müşteri bilgi girdiğinde) ---
    if current_state == "AWAITING_INFO":
        # Burada müşterinin yazdığı veriyi (incoming_msg) gerçek sistemde veritabanına veya Telegram'a atacağız.
        user_states[session_id]["state"] = "COMPLETED"
        return "✅ Bilgileriniz başarıyla alınmıştır. Uzman ekibimiz sizinle en kısa sürede iletişime geçecektir.\n\nAna menüye dönmek için 'menü' yazabilirsiniz."

    # --- ORTAK RANDEVU SİSTEMİ (Tüm sektörler buraya akar) ---
    if current_state == "SELECT_DATE":
        if incoming_msg in ["1", "2"]:
            user_states[session_id]["state"] = f"SELECT_TIME_{incoming_msg}"
            return TIME_MENU
        else:
            return "Lütfen geçerli bir gün seçin (1-2).\n\n" + DATE_MENU

    if current_state.startswith("SELECT_TIME_"):
        if incoming_msg in ["1", "2", "3", "4"]:
            date_choice = current_state.split("_")[-1]
            
            # --- GEÇMİŞ ZAMAN KONTROLÜ BAŞLANGICI ---
            today = datetime.date.today()
            if date_choice == "1":
                target_date = today
            elif date_choice == "2":
                target_date = today + datetime.timedelta(days=1)
                
            time_mapping = {"1": "10:00:00", "2": "13:00:00", "3": "15:00:00", "4": "18:00:00"}
            target_time_str = time_mapping[incoming_msg]
            
            # Türkiye Saati'ni (UTC+3) ayarla
            tz_tr = timezone(timedelta(hours=3))
            now_tr = datetime.datetime.now(tz_tr) # Şu anki Türkiye saati
            
            # Müşterinin seçtiği tarihi ve saati birleştirip Türkiye saatine çeviriyoruz
            target_dt = datetime.datetime.strptime(f"{target_date} {target_time_str}", "%Y-%m-%d %H:%M:%S")
            target_dt = target_dt.replace(tzinfo=tz_tr)
            
            # EĞER SEÇİLEN ZAMAN ŞU ANDAN KÜÇÜKSE (GEÇMİŞTEYSE) İZİN VERME!
            if target_dt < now_tr:
                return f"❌ Hata: Seçtiğiniz saat ({target_time_str[:5]}) geçmişte kaldı! Lütfen ileri bir saat seçin.\n\n" + TIME_MENU
            # --- GEÇMİŞ ZAMAN KONTROLÜ BİTİŞİ ---

            # Google Calendar'a ekle!
            success = create_calendar_event(date_choice, incoming_msg, session_id)
            
            user_states[session_id]["state"] = "COMPLETED" 
            if success:
                return "✅ Harika! Randevunuz başarıyla oluşturuldu.\n\nAna menüye dönmek için 'menü' yazabilirsiniz."
            else:
                return "❌ Takvime kaydedilirken bir sorun oluştu. Lütfen daha sonra tekrar deneyin."
        else:
            return "Lütfen geçerli bir saat seçin (1-4).\n\n" + TIME_MENU

    return "Ana menüye dönmek için 'menü' yazabilirsiniz."




# --- WEB ARAYÜZÜ ROTASI ---
@app.route('/')
def index():
    return render_template('index.html')

# --- WEB ARAYÜZÜ İÇİN HABERLEŞME ROTASI ---
@app.route('/chat', methods=['POST'])
def web_chat():
    data = request.json
    session_id = data.get('sender') 
    incoming_msg = data.get('message')
    
    if not session_id or not incoming_msg:
        return jsonify({"status": "error", "message": "Eksik veri"}), 400
        
    response_text = handle_message(session_id, incoming_msg)
    return jsonify({"status": "success", "response": response_text}), 200

# --- GERÇEK WHATSAPP (META API) İÇİN ROTAMIZ ---
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    phone_number = data.get('sender')
    incoming_msg = data.get('message')
    
    if not phone_number or not incoming_msg:
        return jsonify({"status": "error"}), 400
        
    response_text = handle_message(phone_number, incoming_msg)
    print(f"Response for {phone_number}: {response_text}")
    return jsonify({"status": "success", "response": response_text}), 200

if __name__ == '__main__':
    # Render'da çalışırken PORT environment variable'ını okumamız gerekir
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
