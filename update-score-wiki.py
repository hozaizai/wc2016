import requests
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

url = "https://script.google.com/macros/s/AKfycbyV15RT-DWy_cjlvYPJK-eO67wmcrOKs0DrtO28esuqIldH1ghtRxpD_YDtEC31TYl1eA/exec"

response = requests.get(url, allow_redirects=True)
with open("data-score-wiki.json", "w", encoding="utf-8") as f:
    f.write(response.text)

print("✅ data-score-wiki.json 已更新")
