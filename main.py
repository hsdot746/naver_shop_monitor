import os
import json
import requests
from datetime import datetime
import time
import sys # 로그 강제 출력을 위해 추가

# 1. API 키 설정
NAVER_CLIENT_ID = os.environ.get("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# 2. 🎯 모니터링 타겟 설정
SEARCH_TARGETS = [
    {"keyword": "포켓몬카드 닌자스피너", "min_price": 27000, "max_price": 30000}
]

# 3. 데이터 최적화 설정
DISPLAY_COUNT = 100
MAX_ITEMS = 100
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
        else:
            print(f"❌ 네이버 API 에러: {res.status_code}", flush=True)
            break
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
    #print(f"🚀 모니터링 프로세스를 시작합니다... ({datetime.now()})", flush=True)
    #send_telegram_message("⚙️ 5분 주기 모니터링이 정상적으로 작동 중입니다.")
    
    history = load_history()
    history_updated = False

    for target in SEARCH_TARGETS:
        keyword = target["keyword"]
        min_price = target["min_price"]
        max_price = target["max_price"]
        
        print(f"🔍 검색 중: {keyword} (가격 범위: {min_price}원 ~ {max_price}원)", flush=True)
        items = get_naver_shopping_data(keyword)
        print(f"📦 수집된 전체 상품 수: {len(items)}개", flush=True)
        
        if keyword not in history:
            history[keyword] = []
            
        current_product_ids = []
        new_items_count = 0

        for item in items:
            product_id = item.get('productId')
            price = int(item.get('lprice', 0))
            
            if min_price <= price <= max_price:
                current_product_ids.append(product_id)
                
                if product_id not in history[keyword]:
                    new_items_count += 1
                    title = item.get('title').replace("<b>", "").replace("</b>", "")
                    link = item.get('link')
                    
                    message = (
                        f"🚨 <b>신규 소싱 감지</b>\n\n"
                        f"▪️ <b>상품명:</b> {title}\n"
                        f"▪️ <b>가격:</b> {price:,}원\n"
                        f"🔗 <a href='{link}'>바로가기</a>"
                    )
                    send_telegram_message(message)

        print(f"✨ 조건에 맞는 신규 상품 {new_items_count}개를 발견하여 알림을 보냈습니다.", flush=True)

        if new_items_count > 0 or not history[keyword]:
            history[keyword].extend([pid for pid in current_product_ids if pid not in history[keyword]])
            history[keyword] = history[keyword][-MAX_ITEMS:]
            history_updated = True

    if history_updated:
        save_history(history)
        print("💾 새로운 상품 이력을 저장했습니다.", flush=True)
    
    print("✅ 모니터링이 완료되었습니다.", flush=True)

if __name__ == "__main__":
    main()
