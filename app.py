import os
import time
import threading
import httpx
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
        with httpx.Client(timeout=10.0) as client:
            client.post(WEBHOOK_URL, json={"content": text})
    except:
        pass

def get_items(keyword):
    url = "https://api.mercari.jp/v2/entities:search"
    # 【最重要】ブラウザの動きを完全に再現するヘッダー
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
        "Content-Type": "application/json",
        "Origin": "https://jp.mercari.com",
        "Referer": "https://jp.mercari.com/",
        "DNT": "1",
        "X-Mer-Os": "web",
        "X-Mer-Device": "pc"
    }
    
    payload = {
        "pageSize": 20,
        "searchCondition": {
            "keyword": keyword,
            "status": ["ITEM_STATUS_ON_SALE"],
            "sort": "SORT_CREATED_TIME",
            "order": "ORDER_DESC"
        },
        "serviceName": "mercari",
        "indexName": "main"
    }

    try:
        # HTTP/2を有効にしてよりブラウザに近づける
        with httpx.Client(headers=headers, timeout=15.0, verify=False, http2=True) as client:
            r = client.post(url, json=payload)
            if r.status_code == 200:
                return r.json().get("items", [])
            else:
                # エラーが出たら詳細を送る（デバッグ用）
                print(f"Error {r.status_code}")
                return None
    except Exception as e:
        print(f"Exception: {e}")
        return None

def monitor():
    send_discord("🔥 セキュリティ突破モードで再起動しました。")
    
    while True:
        try:
            for target in SEARCH_LIST:
                items = get_items(target["name"])
                
                # itemsがNone（エラー）じゃなければ成功
                if items is not None:
                    for item in items:
                        item_id = item.get("id")
                        if item_id and item_id not in checked_ids:
                            price = int(item.get("price", 0))
                            if price <= target["price"]:
                                url = f"https://jp.mercari.com/item/{item_id}"
                                send_discord(f"🎯 【発見】{target['name']}\n価格: {price}円\n{url}")
                            checked_ids.add(item_id)
                else:
                    # 400エラー等で失敗している場合
                    pass 
                
                time.sleep(random.uniform(5, 10)) # 動きをランダムにして機械っぽさを消す
        except:
            pass
        time.sleep(30)

@app.route("/")
def home():
    return "WORKING"

if __name__ == "__main__":
    t = threading.Thread(target=monitor, daemon=True)
    t.start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
