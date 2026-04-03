import requests
from requests.auth import HTTPBasicAuth

EMAIL = "email -********"
API_TOKEN = "token -********"
BASE_URL = "urlneed to be added"

auth = HTTPBasicAuth(EMAIL, API_TOKEN)

headers = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}

def create_field(name):
    url = f"{BASE_URL}/rest/api/3/field"

    payload = {
        "name": name,
        "type": "com.atlassian.jira.plugin.system.customfieldtypes:textarea",
        "searcherKey": "com.atlassian.jira.plugin.system.customfieldtypes:textsearcher"
    }

    response = requests.post(url, json=payload, headers=headers, auth=auth)

    print(f"{name} → {response.status_code}")
    print(response.text)
    print("-----")


# Create all fields
create_field("QA_Steps")
create_field("QA_Expected")
create_field("QA_Preconditions")
create_field("QA_TestData")