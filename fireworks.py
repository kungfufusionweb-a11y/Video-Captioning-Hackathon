import httpx, os

api_key = os.environ.get("FIREWORKS_API_KEY", "fw_LyEBwveQEAtmxMyvjjEMK5")
resp = httpx.get(
    "https://api.fireworks.ai/inference/v1/models",
    headers={"Authorization": f"Bearer {api_key}"}
)
print(resp.status_code)
for m in resp.json().get("data", []):
    print(m.get("id"))