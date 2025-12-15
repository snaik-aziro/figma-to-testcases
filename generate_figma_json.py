import json
import os
import requests

try:
    # Read token securely
    FIGMA_TOKEN = os.getenv("FIGMA_TOKEN")
    if not FIGMA_TOKEN:
        raise ValueError("FIGMA_TOKEN environment variable not set")

    file_key = "z8KzX9eaO53rDOb887HYWv"
    node_id = "217:2583"

    url = f"https://api.figma.com/v1/files/{file_key}/nodes"
    headers = {
        "X-Figma-Token": FIGMA_TOKEN
    }
    params = {
        "ids": node_id
    }

    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()  # HTTP errors (4xx, 5xx)

    data = response.json()

    # Save response to file
    output_file = f"figma_node_{node_id.replace(':', '_')}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(json.dumps(data, indent=2))
    print(f"\nResponse saved to: {output_file}")

except Exception as e:
    print(f"❌ Unexpected error: {e}")