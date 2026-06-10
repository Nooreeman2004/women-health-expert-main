import requests
import json
import uuid

BASE_URL = "http://localhost:8000/api/v1"

def chat(message, session_id=None):
    payload = {"message": message}
    if session_id:
        payload["session_id"] = session_id
    response = requests.post(f"{BASE_URL}/chat", json=payload)
    return response.json()

print("--- ADVANCED FEATURES TEST ---")

# 1. Test Persistence & Memory
session_id = f"test-persis-{uuid.uuid4()}"
print(f"\n[PHASE 1] Persistence Test (Session: {session_id})")
r1 = chat("My name is Sarah and I am currently 40 years old.", session_id=session_id)
print(f"Turn 1 Response: {r1.get('response')}")

r2 = chat("What did I just tell you about myself?", session_id=session_id)
print(f"Turn 2 Response: {r2.get('response')}")

if "Sarah" in r2.get('response') and "40" in r2.get('response'):
    print("✅ SUCCESS: Personality memory works.")
else:
    print("❌ FAILURE: Personality memory lost.")

# 2. Test Red Flag Acknowledgment (Combo response)
print(f"\n[PHASE 2] Red Flag Combo Test")
r3 = chat("I have been having some vaginal discharge that seems unusual, and also I have severe chest pain today.", session_id=session_id)
response_text = r3.get('response')
print(f"Turn 3 Response (Red Flag):\n{response_text}")

contains_discharge_info = "discharge" in response_text.lower() or "unusual" in response_text.lower()
contains_warning = "urgent medical attention" in response_text.lower() or "chest pain" in response_text.lower()

if contains_warning:
    print("✅ SUCCESS: Warning present.")
else:
    print("❌ FAILURE: Warning missing.")

if contains_discharge_info:
    print("✅ SUCCESS: Educational content present.")
else:
    print("⚠️ PARTIAL: Only warning present, or LLM was too brief.")

# 3. Test Context-Aware Clarification
print(f"\n[PHASE 3] Clarification Test")
r4 = chat("It is yellow.", session_id=session_id)
print(f"Turn 4 Response (Short follow-up): {r4.get('response')}")

if "I'd like to help you better" in r4.get('response'):
    print("❌ FAILURE: Bot asked for clarification on a contextual answer.")
else:
    print("✅ SUCCESS: Bot accepted short answer in context.")
