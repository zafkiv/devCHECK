import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('NEYNAR_API_KEY')
CLIENT_ID = os.getenv('NEYNAR_CLIENT_ID')

print(f"🔑 API Key: {API_KEY[:10]}...{API_KEY[-5:]}")
print(f"🆔 Client ID: {CLIENT_ID[:10] if CLIENT_ID else 'NOT SET'}...")

headers = {
    'accept': 'application/json',
    'x-api-key': API_KEY
}

# Если есть Client ID, добавляем его
if CLIENT_ID:
    headers['client_id'] = CLIENT_ID
    headers['x-neynar-experimental'] = 'true'
    print("✅ Using Client ID")

# Тест: получить пользователя
print("\n🧪 Testing Neynar API v2 with Client ID\n")

url = "https://api.neynar.com/v2/farcaster/user/bulk"
params = {'fids': '3'}

response = requests.get(url, headers=headers, params=params)
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:500]}")

if response.status_code == 200:
    print("\n✅ SUCCESS! API is working with Client ID")
else:
    print(f"\n❌ Error: {response.status_code}")