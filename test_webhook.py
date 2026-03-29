import requests
import json

def test_webhook():
    url = "http://127.0.0.1:5000/webhook"
    
    # Test cases: (sender, message, expected_in_response)
    test_cases = [
        ("123456", "merhaba", "LeadNova System’e hoş geldiniz"), # First time = Main Menu
        ("123456", "3", "Güzellik Merkezi Demo Sistemine Hoş Geldiniz"), # Next = Sub Menu 3
        ("123456", "2", "Lütfen randevu almak istediğiniz tarihi"), # Next = Appointment
        ("123456", "menü", "LeadNova System’e hoş geldiniz"), # Reset
        ("654321", "başlat", "LeadNova System’e hoş geldiniz"), # First time for new sender
        ("654321", "5", "Müşteri Planlama Sistemine Hoş Geldiniz"), # Choice 5 in Main Menu
    ]
    
    for sender, msg, expected in test_cases:
        print(f"Testing sender {sender} with message '{msg}'...")
        try:
            response = requests.post(url, json={"sender": sender, "message": msg})
            if response.status_code == 200:
                resp_json = response.json()
                content = resp_json.get("response", "")
                if expected.lower() in content.lower():
                    print("✅ Success")
                else:
                    print(f"❌ Failed: Expected '{expected}' in '{content}'")
            else:
                print(f"❌ Failed: Status code {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_webhook()
