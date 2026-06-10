import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1/chat"

def chat(message, session_id=None):
    payload = {"message": message, "use_rag": True}
    if session_id:
        payload["session_id"] = session_id
    response = requests.post(BASE_URL, json=payload)
    return response.json()

print("Starting User Profile Verification...")

# Turn 1: Share specific facts
print("\nTurn 1: Sharing age and symptoms")
res1 = chat("Hello, I am 45 years old and I've been feeling very tired lately.")
session_id = res1.get("session_id")
print(f"AI: {res1.get('response')[:100]}...")

# Wait a moment for background profile extraction to finish
print(" (Waiting for profile extraction...)")
time.sleep(2)

# Turn 2: Mention another fact
print("\nTurn 2: Mentioning more symptoms")
res2 = chat("I also have some mild joint pain in the mornings.", session_id)
print(f"AI: {res2.get('response')[:100]}...")
print(" (Waiting for profile extraction...)")
time.sleep(2)

# Turn 3: Change topic completely
print("\nTurn 3: Changing topic to diet")
res3 = chat("What kind of foods are high in Vitamin D?", session_id)
print(f"AI: {res3.get('response')[:100]}...")

# Turn 4: The Test - Ask the bot what it knows about me
print("\nTurn 4: THE TEST - Asking about extracted facts")
res4 = chat("Based on everything I've said so far, how old am I and what symptoms did I report?", session_id)
response_text = res4.get('response')
print(f"AI: {response_text}")

if "45" in response_text and ("tired" in response_text.lower() or "fatigue" in response_text.lower()):
    print("\n✅ SUCCESS: The bot extracted and remembered the age and symptoms!")
else:
    print("\n❌ FAILURE: The bot missed some key details.")

if "joint pain" in response_text.lower():
    print("✅ SUCCESS: The bot also remembered the joint pain!")
else:
    print("⚠️ PARTIAL: The bot missed the joint pain, but may have caught the primary symptoms.")
