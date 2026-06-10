import requests
import json

# Test multi-turn conversation with the same session
BASE_URL = "http://localhost:8000/api/v1/chat"

print("=" * 80)
print("TESTING MULTI-TURN CONVERSATION")
print("=" * 80)

# Message 1: Initial query
print("\n[MESSAGE 1] Sending: 'my periods are late'")
response1 = requests.post(BASE_URL, json={
    "message": "my periods are late",
    "use_rag": True
})
data1 = response1.json()
session_id = data1.get("session_id")
print(f"Session ID: {session_id}")
print(f"AI Response: {data1.get('response')[:100]}...")

# Message 2: Follow-up
print("\n[MESSAGE 2] Sending: '28 days' (should remember we're talking about periods)")
response2 = requests.post(BASE_URL, json={
    "message": "28 days",
    "session_id": session_id,
    "use_rag": True
})
data2 = response2.json()
print(f"Session ID: {data2.get('session_id')}")
print(f"AI Response: {data2.get('response')[:100]}...")

# Message 3: More context
print("\n[MESSAGE 3] Sending: 'this has been happening for 2 months'")
response3 = requests.post(BASE_URL, json={
    "message": "this has been happening for 2 months",
    "session_id": session_id,
    "use_rag": True
})
data3 = response3.json()
print(f"Session ID: {data3.get('session_id')}")
print(f"AI Response: {data3.get('response')[:100]}...")

print("\n" + "=" * 80)
print("TEST COMPLETE - Check backend logs for debug output")
print("=" * 80)
