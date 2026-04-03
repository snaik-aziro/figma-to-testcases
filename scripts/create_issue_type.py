import requests
from requests.auth import HTTPBasicAuth
import json

EMAIL = "email -********"
API_TOKEN = "token -*****"
BASE_URL = "url need to be added"

auth = HTTPBasicAuth(EMAIL, API_TOKEN)

headers = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}

url = f"{BASE_URL}/rest/api/3/issuetype"

payload = {
    "name": "QA_Test_Case",
    "description": "QA Test Case Type",
    "type": "standard"
}

response = requests.post(url, headers=headers, json=payload, auth=auth)

print(response.status_code)
print(response.text)