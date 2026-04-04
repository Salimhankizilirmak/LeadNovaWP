# LeadNova uçuşa hazır! 🚀
from flask import Flask, request, jsonify, render_template
import os
import datetime
from datetime import timezone, timedelta
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

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

# --- YENİ BİLGİ TOPLAMA METİNLERİ ---
INFO_PROMPTS = {
    "emlak_satilik": "Size en uygun satılık evleri sunabilmemiz için:\n📍 Lokasyon\n💰 Bütçe\n🏠 Oda sayısı\n\nbilgilerini aralarına virgül koyarak yazabilirsiniz.\n🎁 Bugün başvuru yapan müşterilerimize özel fırsatlar sunulmaktadır.",
    "klinik_bilgi": "Size en doğru bilgiyi verebilmemiz için:\n- İlgilendiğiniz işlem\n- Kısa açıklama\n\nyazabilirsiniz. Uzman ekibimiz sizinle ilgilenecektir.",
    "sanayi_teklif": "Size özel teklif hazırlayabilmemiz için:\n- Talep ettiğiniz ürün / hizmet\n- Adınız\n- Telefon numaranız\n\nbilgilerini yazabilirsiniz. Ekibimiz en kısa sürede dönüş sağlayacaktır.",
    "galeri_arac": "Size uygun araçları sunabilmemiz için:\n🚗 Araç tipi\n💰 Bütçe\n📍 Şehir\n\nbilgilerini yazabilirsiniz."
}


DATE_MENU = """Lütfen randevu gününü seçin:
1️⃣ Bugün
2️⃣ Yarın
3️⃣ 2 Gün Sonra"""

TIME_MENU = """Lütfen randevu saatini seçin:
1️⃣ 10:00
2️⃣ 13:00
3️⃣ 15:00
4️⃣ 17:00"""

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
        time_mapping = {"1": "10:00:00", "2": "13:00:00", "3": "15:00:00", "4": "17:00:00"}
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
    
    # Kullanıcı ilk defa yazıyorsa veya "menü" yazdıysa
    if session_id not in user_states or incoming_msg.lower() in ["menü", "menu", "merhaba", "selam"]:
        user_states[session_id] = "MAIN_MENU"
        return MAIN_MENU

    current_state = user_states[session_id]

    # HER YERDE GEÇERLİ ORTAK CANLI DESTEK (0'a basılırsa)
    if incoming_msg == "0":
        user_states[session_id] = "LIVE_SUPPORT"
        return "Sizi müşteri temsilcimize aktarıyorum. Lütfen bekleyin... 🎧"

    # --- ANA MENÜ KONTROLÜ ---
    if current_state == "MAIN_MENU":
        if incoming_msg in SUB_MENUS:
            user_states[session_id] = f"SUB_MENU_{incoming_msg}"
            return SUB_MENUS[incoming_msg]
        else:
            return "Lütfen geçerli bir numara tuşlayın (1-5).\n\n" + MAIN_MENU

    # Alt menü kontrolü ve diğer durumlar için geçici dönüş
    # (Adım 2'de burası detaylandırılacak)
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
