import requests
import json

BASE_URL = "http://localhost:8000/api/v1/chat"

def chat(message, session_id=None):
    payload = {"message": message, "use_rag": True}
    if session_id:
        payload["session_id"] = session_id
    response = requests.post(BASE_URL, json=payload)
    return response.json()

print("Starting Memory Fix Verification...")

# Turn 1: Mention the specific concern
print("\nTurn 1: Mentioning white spot near eye")
res1 = chat("Recently white spot is developing near my eye. i am really worried about it.")
session_id = res1.get("session_id")
print(f"AI: {res1.get('response')[:100]}...")

# Turn 2: Follow up
print("\nTurn 2: Follow up on growth")
res2 = chat("i have been observing it for quite some time and its growing in size,not itching or pain. what can it be?", session_id)
print(f"AI: {res2.get('response')[:100]}...")

# Turn 3: Change topic slightly (cleansing)
print("\nTurn 3: Asking about cleansing")
res3 = chat("how should i keep the area clean?", session_id)
print(f"AI: {res3.get('response')[:100]}...")

# Turn 4: Another topic (sunscreen)
print("\nTurn 4: Asking about sunscreen")
res4 = chat("should i use sunscreen there too?", session_id)
print(f"AI: {res4.get('response')[:100]}...")

# Turn 5: The Test - Ask about the original spot
print("\nTurn 5: THE TEST - Asking what was mentioned earlier")
res5 = chat("recap for me: what did i say was near my eye and what did i tell you about its symptoms?", session_id)
response_text = res5.get('response')
print(f"AI: {response_text}")

if "white spot" in response_text.lower() and "eye" in response_text.lower():
    print("\n✅ SUCCESS: The bot remembered the white spot near the eye!")
else:
    print("\n❌ FAILURE: The bot forgot the white spot near the eye.")

if "growing" in response_text.lower() or "size" in response_text.lower():
    print("✅ SUCCESS: The bot remembered it is growing.")
else:
    print("⚠️ PARTIAL: The bot didn't explicitly mention it's growing, but may have remembered the spot.")
