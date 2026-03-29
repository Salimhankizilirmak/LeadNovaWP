# import antigravity  # LeadNova uçuşa hazır! 🚀 (Commented out to prevent browser pop-ups)
print("LeadNova uçuşa hazır! 🚀")

from flask import Flask, request, jsonify, render_template
import os

app = Flask(__name__)

# --- BOT MANTIĞI ---
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

# --- YENİ EKLENEN RANDEVU SEÇENEKLERİ ---
DATE_MENU = """Lütfen randevu gününü seçin:
1️⃣ Bugün
2️⃣ Yarın
3️⃣ 2 Gün Sonra"""

TIME_MENU = """Lütfen randevu saatini seçin:
1️⃣ 10:00
2️⃣ 13:00
3️⃣ 15:00
4️⃣ 17:00"""

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

    # ---------------- YENİ EKLENEN RANDEVU AKIŞI ----------------

    # Kullanıcı gün seçimi yapıyorsa
    if current_state == "SELECT_DATE":
        if incoming_msg in ["1", "2", "3"]:
            user_states[session_id] = "SELECT_TIME"
            return TIME_MENU
        else:
            return "Lütfen geçerli bir gün seçin (1-3).\n\n" + DATE_MENU

    # Kullanıcı saat seçimi yapıyorsa
    if current_state == "SELECT_TIME":
        if incoming_msg in ["1", "2", "3", "4"]:
            user_states[session_id] = "COMPLETED" 
            return "✅ Harika! Randevunuz başarıyla oluşturuldu ve yetkililerin Google Takvimi'ne otomatik olarak eklendi.\n\nBizi tercih ettiğiniz için teşekkür ederiz. Ana menüye dönmek için 'menü' yazabilirsiniz."
        else:
            return "Lütfen geçerli bir saat seçin (1-4).\n\n" + TIME_MENU

    # -------------------------------------------------------------

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
