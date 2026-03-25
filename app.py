import os
import time
import threading
import httpx  # requestsの代わりにhttpxを使用
import random
from flask import Flask

SEARCH_LIST = [
    {"name": "妖怪ウォッチ 真打", "price": 99999},
    {"name": "妖怪ウォッチ スキヤキ", "price": 3000},
    {"name": "妖怪ウォッチ スシ", "price": 1000},
    {"name": "妖怪ウォッチ テンプラ", "price": 1000},
    {"name": "妖怪ウォッチ 白犬隊", "price": 1200},
    {"name": "妖怪ウォッチ 赤猫団", "price": 2200}
]

WEBHOOK_URL = "https://discordapp.com/api/webhooks/1476433652094341267/UVroNGFXVuigrRSmbFwebk0zCqNMC7XJJqh3obWt0MYXCk2s7qMhpG1ErqbjSfcitjoD"
app = Flask(__name__)
checked_ids = set()

def send_discord(text):
    try:
        # Discord送信もhttpxで確実に行う
        with httpx.Client(timeout=5.0) as client:
            client.post(WEBHOOK_URL, json={"content": text})
    except:
        pass

def get_items(keyword):
    print(f"DEBUG: [{keyword}] 検索フェーズ突入")
    url = "https://api.mercari.jp/v2/entities:search"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "X-Mer-Os": "web",
        "X-Mer-Device": "pc",
        "Accept": "application/json"
    }
    payload = {
        "pageSize": 5,
        "searchCondition": {"keyword": keyword, "status": ["ITEM_STATUS_ON_SALE"]},
        "serviceName": "mercari",
        "indexName": "main"
    }
    
    try:
        # httpxを使用して、非常に短いタイムアウトを設定
        with httpx.Client(headers=headers, timeout=3.0, verify=False) as client:
            r = client.post(url, json=payload)
            print(f"DEBUG: 応答ステータス: {r.status_code}")
            if r.status_code == 200:
                return r.json().get("items", [])
    except Exception as e:
        print(f"DEBUG: 接続をスキップしました (原因: {type(e).__name__})")
    return []

def monitor():
    print("LOG: 監視スレッド：最終兵器(httpx)モード始動")
    send_discord("🚀 最終通信テストを開始します。ログを確認してください。")
    
    while True:
        try:
            for target in SEARCH_LIST:
                keyword = target["name"]
                print(f"LOG: 検索中... -> {keyword}")
                items = get_items(keyword)
                
                for item in items:
                    item_id = item.get("id")
                    if not item_id or item_id in checked_ids:
                        continue
                    
                    price = int(item.get("price", 0))
                    if price <= target["price"]:
                        url = f"https://jp.mercari.com/item/{item_id}"
                        send_discord(f"🎯 【{keyword}】\n{price}円\n{url}")
                        checked_ids.add(item_id)
                
                time.sleep(2) # 1単語ごとに一息つく

        except Exception as e:
            print(f"CRITICAL: {e}")
        
        print("LOG: 一巡しました。待機に入ります。")
        time.sleep(30)

@app.route("/")
def home():
    return "STILL ALIVE"

if __name__ == "__main__":
    t = threading.Thread(target=monitor, daemon=True)
    t.start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
