from main import handle_message, user_states, MAIN_MENU, check_followups, FOLLOWUP_1_HOUR
import datetime
import time

def test():
    session_id = "test_user_step3"
    
    print("--- Test 1: First Message (Dict creation) ---")
    res = handle_message(session_id, "merhaba")
    assert isinstance(user_states[session_id], dict)
    assert user_states[session_id]["state"] == "MAIN_MENU"
    assert "last_active" in user_states[session_id]
    assert user_states[session_id]["f1_sent"] == False
    
    print("\n--- Test 2: State Update (Dict maintenance) ---")
    handle_message(session_id, "1") # Emlak
    assert user_states[session_id]["state"] == "SUB_MENU_1"
    
    print("\n--- Test 3: Follow-up Simulation (1 hour) ---")
    # Manually age the activity to 61 minutes ago
    user_states[session_id]["last_active"] = datetime.datetime.now() - datetime.timedelta(minutes=61)
    
    # This should trigger the follow-up log in console
    check_followups()
    
    assert user_states[session_id]["f1_sent"] == True
    
    print("\n--- Step 3 Logic Tests Passed! ---")

if __name__ == "__main__":
    test()
