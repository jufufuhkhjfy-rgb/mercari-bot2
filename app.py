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
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "X-Mer-Os": "web",
        "X-Mer-Device": "pc",
        "Origin": "https://jp.mercari.com",
        "Referer": "https://jp.mercari.com/"
    }
    
    # 400エラーを防ぐための、最新の検索データ形式
    payload = {
        "pageSize": 20,
        "searchCondition": {
            "keyword": keyword,
            "sort": "SORT_CREATED_TIME",
            "order": "ORDER_DESC",
            "status": ["ITEM_STATUS_ON_SALE"],
            "category_id": [], # 空でもリスト形式にする
            "brand_id": [],
            "seller_id": [],
            "feature_id": [],
            "exclude_keyword": ""
        },
        "serviceName": "mercari",
        "indexName": "main"
    }

    try:
        # http2をTrueにすると、より「本物のブラウザ」っぽくなります
        with httpx.Client(headers=headers, timeout=15.0, http2=True) as client:
            r = client.post(url, json=payload)
            if r.status_code == 200:
                return r.json().get("items", [])
            else:
                # 400エラーが出た場合、Discordに詳細を出す（原因特定のヒント）
                print(f"Error {r.status_code}")
                return None
    except Exception as e:
        return None

def monitor():
    send_discord("🛠️ 検索エンジンを最新式にアップデートしました。再試行します。")
    
    while True:
        try:
            for target in SEARCH_LIST:
                items = get_items(target["name"])
                
                if items is not None:
                    # 接続成功！
                    for item in items:
                        item_id = item.get("id")
                        if item_id and item_id not in checked_ids:
                            price = int(item.get("price", 0))
                            if price <= target["price"]:
                                url = f"https://jp.mercari.com/item/{item_id}"
                                send_discord(f"🎯 【発見】{target['name']}\n価格: {price}円\n{url}")
                            checked_ids.add(item_id)
                else:
                    # まだ400が出る場合は、1回だけ通知して休む
                    # send_discord("⚠️ まだ門前払いされています...") 
                    pass
                
                time.sleep(random.uniform(10, 20)) # 少し間隔を空けて「怪しさ」を消す
        except:
            pass
        time.sleep(30)

@app.route("/")
def home():
    return "ONLINE"

if __name__ == "__main__":
    t = threading.Thread(target=monitor, daemon=True)
    t.start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
