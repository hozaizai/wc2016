import requests
from bs4 import BeautifulSoup
import json
import re
import os
from urllib.parse import urlparse, urlunparse
from datetime import date

# ==========================================
# 0. 工具函數：正規化 URL（去除 query string）
# ==========================================
def normalize_url(url):
    if not url:
        return ""
    parsed = urlparse(url)
    return urlunparse(parsed._replace(query="", fragment=""))

# ==========================================
# 1. 爬蟲功能：從 HKET adhoc 搜尋頁取得最新資料
# ==========================================
def fetch_hket_news():
    url = "https://service.hket.com/search/result?dis=adhoc&keyword=%E4%B8%96%E7%95%8C%E7%9B%832026"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = soup.find_all('div', class_='template_item hket-col-xs-60 hket-col-sm-30 hket-col-lg-20')
        
        print(f"找到 {len(articles)} 個文章區塊")
        
        results = []
        for article in articles:
            try:
                # 提取標題與網址
                title_tag = article.find('a')
                if not title_tag:
                    continue
                
                article_title = title_tag.get_text(strip=True)
                article_url = title_tag.get('href')
                if article_url and article_url.startswith('/'):
                    article_url = 'https://inews.hket.com' + article_url
                # 去除原有 query string，加上固定追蹤參數
                if article_url:
                    article_url = normalize_url(article_url) + '?r=worldcup2026'
                
                # 提取圖片
                img_tag = article.find('img')
                article_image = ""
                if img_tag:
                    article_image = img_tag.get('data-src') or img_tag.get('src') or ""
                
                # 如果圖片網址為空，則使用預設圖片
                if not article_image:
                    article_image = "images/default.jpg"
                
                # 提取日期
                date_div = article.find('div', class_='listing-date')
                article_time = ""
                if date_div:
                    spans = date_div.find_all('span')
                    span_texts = [s.get_text(strip=True) for s in spans]
                    # 情況一：包含「今日」→ 用當天日期
                    if any('今日' in t for t in span_texts):
                        article_time = date.today().strftime('%Y/%m/%d')
                    else:
                        # 情況二：找 yyyy/mm/dd 或 yyyy-mm-dd 格式
                        full_text = ' '.join(span_texts)
                        date_match = re.search(r'\d{4}[-/]\d{2}[-/]\d{2}', full_text)
                        if date_match:
                            article_time = date_match.group(0)
                
                results.append({
                    "articletitle": article_title,
                    "articletime": article_time,
                    "articleurl": article_url,
                    "articleimage": article_image
                })
            except Exception as e:
                continue
                
        return results

    except Exception as e:
        print(f"連線或解析網頁時發生錯誤: {e}")
        return []

# ==========================================
# 2. 檔案更新功能：比對並寫入 JSON 檔案
# ==========================================
def update_json_file(scraped_data, filename="data-article-news.json"):
    if not scraped_data:
        print("沒有抓取到任何資料，取消更新。")
        return

    existing_data = []
    
    # 步驟 A：讀取舊檔案內容
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 使用正則表達式，精準抓出 var data = [...] 裡面的陣列內容
        data_match = re.search(r'var data = (\[.*?\]);', content, re.DOTALL)
        if data_match:
            try:
                existing_data = json.loads(data_match.group(1))
            except json.JSONDecodeError:
                print("解析舊檔案的 data 失敗，將重新建立。")
    
    # 步驟 B：比對資料，用 normalize_url 去除 query string 後再比對，避免誤判重複
    existing_urls = {normalize_url(item.get("articleurl", "")) for item in existing_data}
    
    new_items = []
    for item in scraped_data:
        if normalize_url(item["articleurl"]) not in existing_urls:
            new_items.append(item)
            
    if not new_items:
        print("沒有發現新文章，檔案維持原樣。")
        return
        
    print(f"找到 {len(new_items)} 篇新文章，準備更新檔案...")
    
    # 步驟 C：將新資料加在最前面，舊資料接在後面，再按日期降序排列（最新的在最上）
    merged_data = new_items + existing_data
    def parse_date(item):
        t = item.get("articletime", "")
        # 統一把 yyyy-mm-dd 轉成 yyyy/mm/dd 方便比較
        return t.replace("-", "/") if t else "0000/00/00"
    updated_data = sorted(merged_data, key=parse_date, reverse=True)
    
    # 步驟 D：製作 focusData (永遠只取 updated_data 的前 3 筆)
    focus_data = []
    for item in updated_data[:3]:
        focus_data.append({
            "title": item["articletitle"],
            "url": item["articleurl"],
            "tag": "焦點"
        })
        
    # 步驟 E：轉換回 JSON 格式字串，並組合回 JavaScript 變數格式
    focus_json_str = json.dumps(focus_data, ensure_ascii=False, indent=4)
    data_json_str = json.dumps(updated_data, ensure_ascii=False, indent=4)
    
    final_file_content = f"var focusData = {focus_json_str};\nvar data = {data_json_str};"
    
    # 步驟 F：寫入檔案覆蓋舊內容
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(final_file_content)
        
    print("更新成功！檔案已寫入。")

# ==========================================
# 3. 執行主程式
# ==========================================
if __name__ == "__main__":
    # 永遠以 script 所在資料夾為工作目錄，避免 right-click 執行時路徑錯誤
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    scraped_news = fetch_hket_news()
    update_json_file(scraped_news)
