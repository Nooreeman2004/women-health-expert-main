"""
Test FastAPI Endpoints

Simple test script for API endpoints.
"""

import requests
import json

BASE_URL = "http://localhost:8000"


def test_health():
    """Test health endpoint."""
    print("="*60)
    print("TEST: Health Check")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/api/v1/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()


def test_stats():
    """Test stats endpoint."""
    print("="*60)
    print("TEST: Stats")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/api/v1/stats")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()


def test_chat():
    """Test chat endpoint."""
    print("="*60)
    print("TEST: Chat Endpoint")
    print("="*60)
    
    # First message
    payload1 = {
        "message": "What are the symptoms of menopause?",
        "use_rag": True
    }
    
    print(f"Request 1: {payload1['message']}")
    response1 = requests.post(f"{BASE_URL}/api/v1/chat", json=payload1)
    print(f"Status: {response1.status_code}")
    
    if response1.status_code == 200:
        data1 = response1.json()
        session_id = data1['session_id']
        print(f"Session ID: {session_id}")
        print(f"Response: {data1['response'][:200]}...")
        print(f"Metadata: {json.dumps(data1['metadata'], indent=2)}")
        print()
        
        # Follow-up message with same session
        payload2 = {
            "message": "How can I manage hot flashes?",
            "session_id": session_id,
            "use_rag": True
        }
        
        print(f"Request 2 (same session): {payload2['message']}")
        response2 = requests.post(f"{BASE_URL}/api/v1/chat", json=payload2)
        print(f"Status: {response2.status_code}")
        
        if response2.status_code == 200:
            data2 = response2.json()
            print(f"Response: {data2['response'][:200]}...")
            print(f"Metadata: {json.dumps(data2['metadata'], indent=2)}")
    else:
        print(f"Error: {response1.text}")
    
    print()


def test_chat_no_rag():
    """Test chat without RAG."""
    print("="*60)
    print("TEST: Chat Without RAG")
    print("="*60)
    
    payload = {
        "message": "I have cramps, what should I take?",
        "use_rag": False
    }
    
    print(f"Request: {payload['message']}")
    response = requests.post(f"{BASE_URL}/api/v1/chat", json=payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {data['response'][:300]}...")
        print(f"Metadata: {json.dumps(data['metadata'], indent=2)}")
    else:
        print(f"Error: {response.text}")
    
    print()


def main():
    """Run all tests."""
    print("\n🧪 FASTAPI ENDPOINT TESTS\n")
    
    try:
        test_health()
        test_stats()
        test_chat()
        test_chat_no_rag()
        
        print("="*60)
        print("✅ ALL TESTS COMPLETED")
        print("="*60)
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to API")
        print("Make sure the server is running: python main.py")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
