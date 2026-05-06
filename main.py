import os
import json
import requests
from datetime import datetime
import time

NAVER_CLIENT_ID = os.environ.get("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

SEARCH_TARGETS = [
    {"keyword": "닌자스피너", "min_price": 27000, "max_price": 30000},
    {"keyword": "포켓몬카드", "min_price": 27000, "max_price": 30000}
]

DISPLAY_COUNT = 100   
MAX_ITEMS = 300       
HISTORY_FILE = "history.json"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"})

def get_naver_shopping_data(keyword):
    url = "https://openapi.naver.com/v1/search/shop.json"
    headers = {"X-Naver-Client-Id": NAVER_CLIENT_ID, "X-Naver-Client-Secret": NAVER_CLIENT_SECRET}
    all_items = []
    
    for start_idx in range(1, MAX_ITEMS + 1, DISPLAY_COUNT):
        params = {"query": keyword, "display": DISPLAY_COUNT, "start": start_idx, "sort": "date"}
        res = requests.get(url, headers=headers, params=params)
        
        if res.status_code == 200:
            data = res.json().get('items', [])
            all_items.extend(data)
            if len(data) < DISPLAY_COUNT: break
        else: break
        time.sleep(0.1)
    return all_items

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            try: return json.load(f)
            except: return {}
    return {}

def save_history(history_data):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history_data, f, ensure_ascii=False, indent=4)

def main():
    history = load_history()
    history_updated = False

    for target in SEARCH_TARGETS:
        keyword = target["keyword"]
        min_price = target["min_price"]
        max_price = target["max_price"]
        items = get_naver_shopping_data(keyword)
        
        if keyword not in history:
            history[keyword] = []
            
        current_product_ids = []
        new_items_found = False

        for item in items:
            product_id = item.get('productId')
            price = int(item.get('lprice', 0))
            
            if min_price <= price <= max_price:
                current_product_ids.append(product_id)
                
                if product_id not in history[keyword]:
                    new_items_found = True
                    title = item.get('title').replace("<b>", "").replace("</b>", "")
                    link = item.get('link')
                    
                    message = (
                        f"🚨 <b>[{keyword}] 조건 부합 신규 상품</b>\n\n"
                        f"▪️ <b>상품명:</b> {title}\n"
                        f"▪️ <b>가격:</b> {price:,}원\n"
                        f"🔗 <a href='{link}'>바로가기</a>"
                    )
                    send_telegram_message(message)

        if new_items_found or not history[keyword]:
            history[keyword].extend([pid for pid in current_product_ids if pid not in history[keyword]])
            history[keyword] = history[keyword][-MAX_ITEMS:]
            history_updated = True

    if history_updated:
        save_history(history)

if __name__ == "__main__":
    main()
