# import antigravity  # LeadNova uçuşa hazır! 🚀 (Commented out to prevent browser pop-ups)
print("LeadNova uçuşa hazır! 🚀")

from flask import Flask, request, jsonify
# Google Calendar entegrasyonu için eklenecekler
# from googleapiclient.discovery import build

app = Flask(__name__)

# Kullanıcıların hangi menüde olduğunu tutacağımız basit bir sözlük (İleride Veritabanına alınacak)
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

def handle_message(phone_number, incoming_msg):
    # Kullanıcı ilk defa yazıyorsa veya "menü" yazdıysa
    if phone_number not in user_states or incoming_msg.lower() == "menü":
        user_states[phone_number] = "MAIN_MENU"
        return MAIN_MENU

    current_state = user_states[phone_number]

    # Ana menüdeyse ve bir seçenek seçtiyse
    if current_state == "MAIN_MENU":
        if incoming_msg in SUB_MENUS:
            user_states[phone_number] = f"SUB_MENU_{incoming_msg}"
            return SUB_MENUS[incoming_msg]
        else:
            return "Lütfen geçerli bir numara tuşlayın (1-6).\n\n" + MAIN_MENU

    # Alt menülerden birindeyse ve "Randevu" (2) seçildiyse (Örnek: Güzellik merkezi veya Sanayi)
    if current_state in ["SUB_MENU_1", "SUB_MENU_3"]:
        if incoming_msg == "2":
            user_states[phone_number] = "AWAITING_DATE"
            return "Lütfen randevu almak istediğiniz tarihi ve saati yazın (Örn: 25 Ekim 14:00). Takviminize otomatik eklenecektir."

    # Kullanıcı bir menüde sıkıştıysa geri dönüş
    return "Ana menüye dönmek için 'menü' yazabilirsiniz."

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    # WhatsApp (Meta/Twilio vb.) API'sinden gelen veriyi parse et
    phone_number = data.get('sender')
    incoming_msg = data.get('message')
    
    if not phone_number or not incoming_msg:
        return jsonify({"status": "error", "message": "Missing sender or message"}), 400
        
    response_text = handle_message(phone_number, incoming_msg)
    
    # Burada yanıtı WhatsApp API üzerinden geri gönderme kodu olacak
    # send_whatsapp_message(phone_number, response_text)
    
    print(f"Response for {phone_number}: {response_text}")
    
    return jsonify({"status": "success", "response": response_text}), 200

if __name__ == '__main__':
    app.run(port=5000, debug=True)
