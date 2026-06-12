import requests
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

url = "https://script.google.com/macros/s/AKfycbybMkJ1-1aLxXWaMtBltI3Qpf7Va4cVkdrCNxzM-HRXwcOIQ9QjDSDPxqmDtwv2D1A3/exec"

response = requests.get(url, allow_redirects=True)
with open("data-score-wiki.json", "w", encoding="utf-8") as f:
    f.write(response.text)

print("✅ data-score-wiki.json 已更新")