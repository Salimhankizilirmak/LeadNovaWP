from main import handle_message, user_states, MAIN_MENU, SUB_MENUS, DATE_MENU, TIME_MENU, INFO_PROMPTS
import datetime

def test():
    session_id = "test_user_step2"
    
    print("--- Test 1: Start Menu ---")
    res = handle_message(session_id, "menu")
    assert res == MAIN_MENU
    
    print("\n--- Test 2: Emlak -> Bilgi Al (AWAITING_INFO) ---")
    res = handle_message(session_id, "1") # Emlak
    assert res == SUB_MENUS["1"]
    res = handle_message(session_id, "1") # Satılık Evler
    assert res == INFO_PROMPTS["emlak_satilik"]
    assert user_states[session_id] == "AWAITING_INFO"
    res = handle_message(session_id, "İstanbul, 5M, 3+1")
    assert "Bilgileriniz başarıyla alınmıştır" in res
    assert user_states[session_id] == "COMPLETED"
    
    print("\n--- Test 3: Klinik -> Randevu (SELECT_DATE) ---")
    user_states[session_id] = "MAIN_MENU"
    handle_message(session_id, "3") # Klinik
    res = handle_message(session_id, "5") # Randevu
    assert res == DATE_MENU
    assert user_states[session_id] == "SELECT_DATE"
    
    print("\n--- Test 4: Güzellik -> Lazer -> Randevu ---")
    user_states[session_id] = "MAIN_MENU"
    handle_message(session_id, "2") # Güzellik
    res = handle_message(session_id, "1") # Lazer
    assert "Lazer epilasyon hakkında" in res
    res = handle_message(session_id, "2") # Randevu
    assert res == DATE_MENU
    
    print("\n--- Test 5: Date Selection -> Time Selection ---")
    res = handle_message(session_id, "2") # Yarın
    assert res == TIME_MENU
    assert user_states[session_id] == "SELECT_TIME_2"
    
    print("\n--- Step 2 Logic Tests Passed! ---")

if __name__ == "__main__":
    test()
