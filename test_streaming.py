import requests

# Send Message Streaming (POST /v1/agents/:agent_id/messages/stream)
response = requests.post(
    "http://localhost:8283/v1/agents/agent-33418f62-6ec6-4263-8e92-147b27acdb87/messages/stream",
    headers={"Content-Type": "application/json"},
    json={"messages": [{"role": "user", "text": "string"}]},
)

print("status_code:", response.status_code)
print("text:", response.text)
print("json:", response.json())
