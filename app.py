import os
import time
import threading
import requests
import random
from flask import Flask

# --- 設定 ---
SEARCH_SETTINGS = {
    "妖怪ウォッチ 真打": 99999,
    "妖怪ウォッチ スキヤキ": 3000,
    "妖怪ウォッチ スシ": 1000,
    "妖怪ウォッチ テンプラ": 1000,
    "妖怪ウォッチ 白犬隊": 1200,
    "妖怪ウォッチ 赤猫団": 2200
}

WEBHOOK_URL = "https://discordapp.com/api/webhooks/1476433652094341267/UVroNGFXVuigrRSmbFwebk0zCqNMC7XJJqh3obWt0MYXCk2s7qMhpG1ErqbjSfcitjoD"
app = Flask(__name__)
checked_ids = set()

def send_discord(msg):
    try:
        requests.post(WEBHOOK_URL, json={"content": msg}, timeout=10)
    except:
        pass

def get_items(keyword):
    # 🔍 ログ：ここを通っているか確認
    print(f">>> [API呼出開始] キーワード: {keyword}")
    
    url = "https://api.mercari.jp/v2/entities:search"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Mer-Os": "web",
        "X-Mer-Device": "pc"
    }

    payload = {
        "pageSize": 20,
        "searchCondition": {
            "keyword": keyword,
            "sort": "SORT_CREATED_TIME",
            "order": "ORDER_DESC",
            "status": ["ITEM_STATUS_ON_SALE"],
        },
        "serviceName": "mercari",
        "indexName": "main"
    }

    try:
        # verify=False を追加（SSLエラーで黙るのを防ぐ）
        r = requests.post(url, headers=headers, json=payload, timeout=15, verify=True)
        print(f">>> [API応答] Status: {r.status_code}")
        
        if r.status_code != 200:
            return []
        
        return r.json().get("items", [])
    except Exception as e:
        # ❌ ここでエラー内容を絶対に出す
        print(f"!!! [API接続失敗] 原因: {e}")
        return []

def monitor():
    # 🚀 ここがログに出ればスレッドは動いている
    print("=== MONITOR THREAD STARTED ===")
    send_discord("📢 監視スレッドが正常に開始されました")

    while True:
        try:
            for keyword, max_price in SEARCH_SETTINGS.items():
                items = get_items(keyword)
                print(f"--- {keyword}: {len(items)}件ヒット ---")
                
                for item in items:
                    item_id = item.get("id")
                    if item_id in checked_ids: continue
                    
                    price = int(item.get("price", 0))
                    if price <= max_price:
                        item_url = f"https://jp.mercari.com/item/{item_id}"
                        send_discord(f"🔥 **発見**\n{keyword}\n{price}円\n{item_url}")
                        checked_ids.add(item_id)
                
                time.sleep(3) # 次のキーワードまで待機

            print("=== 一巡完了。待機します ===")
        except Exception as e:
            print(f"!!! [LOOP ERROR] {e}")

        time.sleep(20)

@app.route("/")
def home():
    return "ALIVE"

if __name__ == "__main__":
    # スレッドを確実に外出し
    monitor_thread = threading.Thread(target=monitor, daemon=True)
    monitor_thread.start()
    
    port = int(os.environ.get("PORT", 10000))
    # debug=False にして安定させる
    app.run(host="0.0.0.0", port=port, debug=False)
