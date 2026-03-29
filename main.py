# LeadNova uçuşa hazır! 🚀
from flask import Flask, request, jsonify, render_template
import os
import datetime
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

MAIN_MENU = """*LeadNova System’e hoş geldiniz!* 🚀

Hangi sistem formatını kullanmak istersiniz?
1️⃣ Sanayi
2️⃣ Emlak
3️⃣ Güzellik Merkezi
4️⃣ Tur Hizmeti
5️⃣ Müşteri Planlama Sistemi
6️⃣ Bahis Sitesi Kurulum – Analiz"""

SUB_MENUS = {
    "1": "Sanayi Demo Sistemine Hoş Geldiniz. İşleminizi seçin:\n1- Hırdavat Grubu\n2- Randevu Al\n3- Canlı Destek\n4- Motor – Redüktör",
    "2": "Emlak Demo Sistemine Hoş Geldiniz. İşleminizi seçin:\n1- Satılık Portföy\n2- Kiralık Portföy\n3- Canlı Destek",
    "3": "Güzellik Merkezi Demo Sistemine Hoş Geldiniz. İşleminizi seçin:\n1- İşlemlerimiz\n2- Randevu Al\n3- Canlı Destek",
    "4": "Tur Hizmeti Demo Sistemine Hoş Geldiniz. İşleminizi seçin:\n1- Aktif Seferler\n2- Özel Turlar\n3- Canlı Destek",
    "5": "Müşteri Planlama Sistemine Hoş Geldiniz. İşleminizi seçin:\n1- Whatsapp Otomasyon\n2- Web Sitesi\n3- Yazılım Hizmetleri\n4- Bot Kurulum\n5- Müşteri Kaybetmeyen Strateji",
    "6": "Bahis Sitesi Kurulum ve Analiz Sistemine Hoş Geldiniz. Detaylar için uzman ekibimize aktarılıyorsunuz..."
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
    # Kullanıcı ilk defa yazıyorsa veya "menü" yazdıysa
    if session_id not in user_states or incoming_msg.lower() == "menü":
        user_states[session_id] = "MAIN_MENU"
        return MAIN_MENU

    current_state = user_states[session_id]

    # Ana menüdeyse ve bir seçenek seçtiyse
    if current_state == "MAIN_MENU":
        if incoming_msg in SUB_MENUS:
            user_states[session_id] = f"SUB_MENU_{incoming_msg}"
            return SUB_MENUS[incoming_msg]
        else:
            return "Lütfen geçerli bir numara tuşlayın (1-6).\n\n" + MAIN_MENU

    # Alt menülerden birindeyse ve "Randevu Al" (2) seçildiyse (Sanayi veya Güzellik)
    if current_state in ["SUB_MENU_1", "SUB_MENU_3"]:
        if incoming_msg == "2":
            user_states[session_id] = "SELECT_DATE"
            return DATE_MENU

    # Kullanıcı gün seçimi yapıyorsa
    if current_state == "SELECT_DATE":
        if incoming_msg in ["1", "2", "3"]:
            # Seçilen günü state içinde tutuyoruz ki bir sonraki adımda hatırlayalım
            user_states[session_id] = f"SELECT_TIME_{incoming_msg}"
            return TIME_MENU
        else:
            return "Lütfen geçerli bir gün seçin (1-3).\n\n" + DATE_MENU

    # State 'SELECT_TIME_' ile başlıyorsa
    if current_state.startswith("SELECT_TIME_"):
        if incoming_msg in ["1", "2", "3", "4"]:
            date_choice = current_state.split("_")[-1] # Bir önceki adımda sakladığımız gün (1, 2 veya 3)
            
            # Google Calendar'a ekle!
            success = create_calendar_event(date_choice, incoming_msg, session_id)
            
            user_states[session_id] = "COMPLETED" 
            if success:
                return "✅ Harika! Randevunuz başarıyla oluşturuldu ve yetkililerimize bildirildi.\n\nAna menüye dönmek için 'menü' yazabilirsiniz."
            else:
                return "❌ Takvime kaydedilirken bir sorun oluştu. Lütfen daha sonra tekrar deneyin."
        else:
            return "Lütfen geçerli bir saat seçin (1-4).\n\n" + TIME_MENU

    # Kullanıcı bir menüde sıkıştıysa geri dönüş
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
