# LeadNova uçuşa hazır! 🚀
from flask import Flask, request, jsonify, render_template, render_template_string, session, redirect, url_for
import os
import datetime
from datetime import timezone, timedelta
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from apscheduler.schedulers.background import BackgroundScheduler
import time
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import requests # Gerçek WhatsApp API ile konuşmak için

# .env dosyasındaki şifreleri yükle
load_dotenv()

# Veritabanı URL'sini al
DATABASE_URL = os.environ.get("DATABASE_URL")

app = Flask(__name__)
# Admin panelinde oturumları şifrelemek için rastgele bir güvenlik anahtarı
app.secret_key = "leadnova_cok_gizli_anahtar_2026" 

# Senin Admin panele girmek için kullanacağın ana şifre (Bunu istediğin gibi değiştir)
ADMIN_PASSWORD = "123" 

# --- GOOGLE TAKVİM AYARLARI ---
SCOPES = ['https://www.googleapis.com/auth/calendar']
CREDENTIALS_FILE = 'service_account.json'
# Eğer yukarıdaki adımlarda botu kendi ana takviminle paylaştıysan 'primary' yerine kendi Gmail adresini yazmalısın. 
# (Örn: 'leadnova@gmail.com')
CALENDAR_ID = 'salimhankizilirmak@gmail.com' 

# Kullanıcı durumları (Artık veritabanından yönetiliyor)
# user_states = {}

def get_db_connection():
    # Supabase'e bağlanır ve verileri sözlük (dict) formatında döndürür
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def init_db():
    # Sistem her başladığında çalışır, tablolar yoksa otomatik oluşturur
    conn = get_db_connection()
    cur = conn.cursor()
    
    # 1. Müşteriler (Firmalar) Tablosu
    cur.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            client_id SERIAL PRIMARY KEY,
            company_name VARCHAR(255) NOT NULL,
            phone_number_id VARCHAR(100) UNIQUE NOT NULL,
            whatsapp_token TEXT NOT NULL,
            industry VARCHAR(50) NOT NULL,
            is_active BOOLEAN DEFAULT TRUE
        );
    """)
    
    # 2. Kullanıcıların Durum Tablosu (Botla konuşanların hafızası)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_states (
            session_id VARCHAR(100) PRIMARY KEY,
            state VARCHAR(100) NOT NULL,
            last_active TIMESTAMP NOT NULL,
            f1_sent BOOLEAN DEFAULT FALSE,
            f2_sent BOOLEAN DEFAULT FALSE
        );
    """)
    
    conn.commit()
    cur.close()
    conn.close()

# Uygulama başlarken veritabanı tablolarını hazırla
init_db()

def add_new_client(company_name, phone_number_id, whatsapp_token, industry):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO clients (company_name, phone_number_id, whatsapp_token, industry, is_active)
            VALUES (%s, %s, %s, %s, TRUE)
        """, (company_name, phone_number_id, whatsapp_token, industry))
        conn.commit()
    except Exception as e:
        print(f"Müşteri ekleme hatası: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

def get_all_clients():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM clients ORDER BY client_id DESC")
    clients = cur.fetchall()
    cur.close()
    conn.close()
    return clients

def get_client_by_phone_id(phone_number_id):
    # Gelen mesajın HANGİ müşteriye ait olduğunu veritabanından bulur
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM clients WHERE phone_number_id = %s AND is_active = TRUE", (phone_number_id,))
    client = cur.fetchone()
    cur.close()
    conn.close()
    return client

# --- VERİTABANI HAFIZA FONKSİYONLARI ---
def get_user_state(session_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM user_states WHERE session_id = %s", (session_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user

def update_user_state(session_id, state, f1_sent=False, f2_sent=False):
    conn = get_db_connection()
    cur = conn.cursor()
    now = datetime.datetime.now()
    cur.execute("""
        INSERT INTO user_states (session_id, state, last_active, f1_sent, f2_sent)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (session_id) 
        DO UPDATE SET 
            state = EXCLUDED.state,
            last_active = EXCLUDED.last_active,
            f1_sent = EXCLUDED.f1_sent,
            f2_sent = EXCLUDED.f2_sent;
    """, (session_id, state, now, f1_sent, f2_sent))
    conn.commit()
    cur.close()
    conn.close()

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

def send_whatsapp_message(to_number, text_message, token, phone_number_id):
    """
    Kendi numarasından bağımsız olarak müşterinin özel WhatsApp hattından mesaj gönderir.
    """
    url = f"https://graph.facebook.com/v17.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": text_message}
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        return response.json()
    except Exception as e:
        print(f"WhatsApp mesaj gönderme hatası: {e}")
        return None

def send_proactive_message(session_id, message_text):
    """
    Takip mesajlarını gönderen fonksiyon. Multi-tenant yapısına uygun hale getirildi.
    """
    # session_id formatımız: {client_phone_id}_{customer_phone}
    if "_" in session_id:
        client_phone_id, customer_phone = session_id.split("_")
        client = get_client_by_phone_id(client_phone_id)
        if client:
            send_whatsapp_message(customer_phone, message_text, client['whatsapp_token'], client_phone_id)
            print(f"\n[🚀 OTOMATİK TAKİP MESAJI GÖNDERİLDİ] -> {customer_phone}")
    else:
        print(f"\n[🚀 LOG] Web demosu takip mesajı: {message_text}\n")

# Zamanlayıcıya bu kontrol görevini her 1 dakikada bir yapmasını söylüyoruz
# Zamanlayıcıyı (Follow-Up) veritabanına bağladık
def check_followups():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM user_states")
    users = cur.fetchall()
    now = datetime.datetime.now()
    
    for user in users:
        session_id = user['session_id']
        last_active = user['last_active']
        
        # Eğer müşteri 1 saat boyunca yazmadıysa
        if not user['f1_sent'] and (now - last_active).total_seconds() >= 3600:
            send_proactive_message(session_id, FOLLOWUP_1_HOUR)
            update_user_state(session_id, user['state'], f1_sent=True, f2_sent=user['f2_sent'])
            
        # Eğer müşteri 1 gün boyunca yazmadıysa
        elif not user['f2_sent'] and (now - last_active).total_seconds() >= 86400:
            send_proactive_message(session_id, FOLLOWUP_1_DAY)
            update_user_state(session_id, user['state'], f1_sent=user['f1_sent'], f2_sent=True)
            
    cur.close()
    conn.close()

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

# Mesaj işleyiciyi veritabanına bağladık
def handle_message(session_id, incoming_msg):
    incoming_msg = incoming_msg.strip()
    
    # Supabase'den kullanıcıyı çek
    user = get_user_state(session_id)
    
    is_new_user = not user
    is_reset_msg = incoming_msg.lower() in ["menü", "menu", "merhaba", "selam"]

    # Kullanıcı ilk defa yazıyorsa veya resetlemek istediyse
    if is_new_user or is_reset_msg:
        update_user_state(session_id, "MAIN_MENU")
        return MAIN_MENU

    current_state = user["state"]

    # Durum güncelleyici yardımcı fonksiyon
    def set_state(new_state):
        update_user_state(session_id, new_state, user['f1_sent'], user['f2_sent'])

    if incoming_msg == "0":
        set_state("LIVE_SUPPORT")
        return "Sizi müşteri temsilcimize aktarıyorum. Lütfen bekleyin... 🎧"

    # --- ANA MENÜ ---
    if current_state == "MAIN_MENU":
        if incoming_msg in SUB_MENUS:
            set_state(f"SUB_MENU_{incoming_msg}")
            return SUB_MENUS[incoming_msg]
        else:
            return "Lütfen geçerli bir numara tuşlayın (1-5).\n\n" + MAIN_MENU

    # --- ALT MENÜLER VE VERİ TOPLAMA/RANDEVU YÖNLENDİRMELERİ ---
    
    # 1. EMLAK
    if current_state == "SUB_MENU_1":
        if incoming_msg in ["1", "2", "3"]:
            set_state("AWAITING_INFO")
            return INFO_PROMPTS["emlak_satilik"]
        elif incoming_msg == "5":
            set_state("SELECT_DATE")
            return DATE_MENU
            
    # 2. GÜZELLİK MERKEZİ
    elif current_state == "SUB_MENU_2":
        if incoming_msg == "1": # Lazer alt menüsü
            set_state("SUB_MENU_LAZER")
            return "✨ Lazer epilasyon hakkında:\n1 - Fiyat bilgisi al\n2 - Randevu oluştur\n\n🎁 Bugün randevu oluşturan müşterilerimize özel indirim uygulanmaktadır."
        elif incoming_msg == "7":
            set_state("SELECT_DATE")
            return DATE_MENU
            
    # 2.1 GÜZELLİK MERKEZİ -> LAZER ALT MENÜSÜ
    elif current_state == "SUB_MENU_LAZER":
        if incoming_msg == "2":
            set_state("SELECT_DATE")
            return DATE_MENU

    # 3. KLİNİK
    elif current_state == "SUB_MENU_3":
        if incoming_msg == "4":
            set_state("AWAITING_INFO")
            return INFO_PROMPTS["klinik_bilgi"]
        elif incoming_msg == "5":
            set_state("SELECT_DATE")
            return DATE_MENU

    # 4. SANAYİ
    elif current_state == "SUB_MENU_4":
        if incoming_msg == "2":
            set_state("AWAITING_INFO")
            return INFO_PROMPTS["sanayi_teklif"]

    # 5. GALERİ
    elif current_state == "SUB_MENU_5":
        if incoming_msg == "1":
            set_state("AWAITING_INFO")
            return INFO_PROMPTS["galeri_arac"]
        elif incoming_msg == "4":
            set_state("SELECT_DATE")
            return DATE_MENU

    # --- VERİ TOPLAMA (Müşteri bilgi girdiğinde) ---
    if current_state == "AWAITING_INFO":
        # Burada müşterinin yazdığı veriyi (incoming_msg) gerçek sistemde veritabanına veya Telegram'a atacağız.
        set_state("COMPLETED")
        return "✅ Bilgileriniz başarıyla alınmıştır. Uzman ekibimiz sizinle en kısa sürede iletişime geçecektir.\n\nAna menüye dönmek için 'menü' yazabilirsiniz."

    # --- ORTAK RANDEVU SİSTEMİ (Tüm sektörler buraya akar) ---
    if current_state == "SELECT_DATE":
        if incoming_msg in ["1", "2"]:
            set_state(f"SELECT_TIME_{incoming_msg}")
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
            
            set_state("COMPLETED") 
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

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "leadnova_gizli_2026") # Meta Developer Dashboard'da kullanılacak

# --- META WEBHOOK DOĞRULAMA (GET İSTEĞİ) ---
@app.route('/webhook', methods=['GET'])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("WEBHOOK DOĞRULANDI! ✅")
            return challenge, 200
        else:
            return "Yetkisiz işlem", 403
    return "Hatalı İstek", 400

# --- GERÇEK WHATSAPP MESAJLARINI ALMA VE İŞLEME (POST İSTEĞİ) ---
@app.route('/webhook', methods=['POST'])
def whatsapp_webhook():
    data = request.json
    
    # Meta'dan mı geldi kontrol et
    if "object" in data and data["object"] == "whatsapp_business_account":
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                
                # Bu mesaj HANGİ firmaya geldi?
                metadata = value.get("metadata", {})
                client_phone_id = metadata.get("phone_number_id")
                
                if "messages" in value and client_phone_id:
                    # Veritabanından o firmayı bul
                    client = get_client_by_phone_id(client_phone_id)
                    
                    if not client:
                        print(f"Kayıtlı olmayan numaraya mesaj geldi: {client_phone_id}")
                        continue
                    
                    # Müşteri verilerini al
                    message = value["messages"][0]
                    customer_phone = message["from"] 
                    
                    # Session ID oluştur: Firmayı ve müşteriyi benzersiz yap
                    session_id = f"{client_phone_id}_{customer_phone}"
                    
                    if message["type"] == "text":
                        incoming_msg = message["text"]["body"]
                        
                        # Botun vereceği cevabı hesapla
                        response_text = handle_message(session_id, incoming_msg)
                        
                        # Cevabı o firmaya özel WhatsApp Token'ı ile gerçek WhatsApp'a gönder!
                        send_whatsapp_message(customer_phone, response_text, client['whatsapp_token'], client_phone_id)
                        
        return jsonify({"status": "success"}), 200
    else:
        return jsonify({"status": "error"}), 404

# --- ADMIN PANELİ (GİRİŞ SAYFASI) ---
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return "Hatalı Şifre! <a href='/admin/login'>Tekrar Dene</a>"
            
    # Giriş formu HTML'i (Hızlı olması için doğrudan kodun içine gömüyoruz)
    login_html = """
    <html><head><title>LeadNova Admin Girişi</title></head>
    <body style="font-family: Arial; background-color: #f0f2f5; display:flex; justify-content:center; align-items:center; height:100vh;">
        <div style="background:white; padding:40px; border-radius:10px; box-shadow:0 4px 10px rgba(0,0,0,0.1); text-align:center;">
            <h2>🚀 LeadNova Admin</h2>
            <form method="POST">
                <input type="password" name="password" placeholder="Yönetici Şifresi" required style="padding:10px; width:100%; margin-bottom:15px; border:1px solid #ccc; border-radius:5px;"><br>
                <button type="submit" style="padding:10px 20px; background-color:#008f68; color:white; border:none; border-radius:5px; cursor:pointer; width:100%;">Giriş Yap</button>
            </form>
        </div>
    </body></html>
    """
    return render_template_string(login_html)

# --- ADMIN PANELİ (DASHBOARD VE MÜŞTERİ EKLEME) ---
@app.route('/admin', methods=['GET', 'POST'])
def admin_dashboard():
    # Güvenlik kontrolü: Şifre girilmemişse login sayfasına at
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        # Formdan gelen yeni müşteri verileri
        c_name = request.form.get('company_name')
        c_phone_id = request.form.get('phone_number_id')
        c_token = request.form.get('whatsapp_token')
        c_industry = request.form.get('industry')
        
        if c_name and c_phone_id and c_token and c_industry:
            add_new_client(c_name, c_phone_id, c_token, c_industry)
            return redirect(url_for('admin_dashboard'))

    # Mevcut müşterileri veritabanından çek
    clients = get_all_clients()
    
    # Modern Dashboard HTML'i
    dashboard_html = """
    <html><head><title>LeadNova Müşteri Yönetimi</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f0f2f5; margin: 0; padding: 20px; }
        .container { max-width: 1000px; margin: auto; }
        .card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 20px; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #008f68; color: white; }
        input, select, button { padding: 10px; margin: 5px 0; border: 1px solid #ccc; border-radius: 5px; width: calc(100% - 22px); }
        button { background-color: #008f68; color: white; cursor: pointer; border: none; font-weight: bold; width: 100%; }
        .logout { display: inline-block; margin-top: 10px; color: #d9534f; text-decoration: none; font-weight: bold; }
    </style>
    </head><body>
    <div class="container">
        <h1 style="color:#333;">🚀 LeadNova Yönetim Merkezi</h1>
        
        <div class="card">
            <h3>➕ Yeni Müşteri Ekle</h3>
            <form method="POST" style="display: flex; flex-wrap: wrap; gap: 10px;">
                <div style="flex: 1; min-width: 200px;"><input type="text" name="company_name" placeholder="Firma Adı (Örn: Ahmet Emlak)" required></div>
                <div style="flex: 1; min-width: 200px;"><input type="text" name="phone_number_id" placeholder="Meta Phone ID" required></div>
                <div style="flex: 1; min-width: 200px;"><input type="text" name="whatsapp_token" placeholder="WhatsApp API Token" required></div>
                <div style="flex: 1; min-width: 200px;">
                    <select name="industry" required>
                        <option value="">-- Sektör Seç --</option>
                        <option value="1">Emlak (1)</option>
                        <option value="2">Güzellik Merkezi (2)</option>
                        <option value="3">Klinik (3)</option>
                        <option value="4">Sanayi (4)</option>
                        <option value="5">Galeri (5)</option>
                    </select>
                </div>
                <div style="flex: 100%;"><button type="submit">Sisteme Ekle ve Botu Başlat</button></div>
            </form>
        </div>

        <div class="card">
            <h3>📋 Aktif Müşteriler</h3>
            <table>
                <tr>
                    <th>ID</th><th>Firma Adı</th><th>Phone ID</th><th>Sektör</th><th>Durum</th>
                </tr>
                {% for client in clients %}
                <tr>
                    <td>{{ client.client_id }}</td>
                    <td><strong>{{ client.company_name }}</strong></td>
                    <td>{{ client.phone_number_id }}</td>
                    <td>Sektör {{ client.industry }}</td>
                    <td style="color:green;">Aktif ✅</td>
                </tr>
                {% else %}
                <tr><td colspan="5" style="text-align:center;">Henüz müşteri bulunmuyor.</td></tr>
                {% endfor %}
            </table>
        </div>
        <a href="/admin/logout" class="logout">Çıkış Yap</a>
    </div>
    </body></html>
    """
    return render_template_string(dashboard_html, clients=clients)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    # Render'da çalışırken PORT environment variable'ını okumamız gerekir
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
