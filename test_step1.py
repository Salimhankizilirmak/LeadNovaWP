from main import handle_message, user_states, MAIN_MENU, SUB_MENUS

def test():
    session_id = "test_user_123"
    
    print("--- Test 1: Start Menu ---")
    res1 = handle_message(session_id, "merhaba")
    print(res1)
    assert res1 == MAIN_MENU
    
    print("\n--- Test 2: Select Emlak (1) ---")
    res2 = handle_message(session_id, "1")
    print(res2)
    assert res2 == SUB_MENUS["1"]
    
    print("\n--- Test 3: Common Live Support (0) from Sub-menu ---")
    res3 = handle_message(session_id, "0")
    print(res3)
    assert "müşteri temsilcimize aktarıyorum" in res3
    
    print("\n--- Step 1 Tests Passed! ---")

if __name__ == "__main__":
    test()
