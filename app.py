import os
import time
import threading
import httpx
import random
from flask import Flask

# 検索ターゲット
SEARCH_LIST = [
    {"name": "妖怪ウォッチ 真打", "price": 99999},
    {"name": "妖怪ウォッチ スキヤキ", "price": 3000}
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
    # メルカリに「人間だぞ」と思わせるための偽装設定
    url = f"https://api.mercari.jp/v2/entities:search?t={random.random()}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "X-Mer-Os": "web",
        "X-Mer-Device": "pc",
        "Accept-Language": "ja-JP,ja;q=0.9",
        "Accept": "*/*"
    }
    payload = {
        "pageSize": 5,
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
        with httpx.Client(headers=headers, timeout=10.0, verify=False) as client:
            r = client.post(url, json=payload)
            if r.status_code == 200:
                return r.json().get("items", [])
            else:
                # 弾かれた場合はエラーコードをDiscordに送る
                send_discord(f"⚠️ メルカリ接続エラー: ステータスコード {r.status_code}")
    except Exception as e:
        send_discord(f"❌ 通信エラー発生: {str(e)}")
    return []

def monitor():
    # --- 【重要】ここがテスト機能 ---
    send_discord("📢 システム起動！メルカリに接続できるかテストします...")
    test_items = get_items("妖怪ウォッチ 真打")
    if test_items:
        first_item = test_items[0]
        item_url = f"https://jp.mercari.com/item/{first_item['id']}"
        send_discord(f"✅ メルカリ接続成功！\n現在の一番上の商品はこちら:\n{item_url}")
    else:
        send_discord("❌ 商品が取得できませんでした。メルカリにブロックされている可能性があります。")
    # --- テストここまで ---

    while True:
        try:
            for target in SEARCH_LIST:
                items = get_items(target["name"])
                for item in items:
                    item_id = item.get("id")
                    if item_id and item_id not in checked_ids:
                        price = int(item.get("price", 0))
                        if price <= target["price"]:
                            url = f"https://jp.mercari.com/item/{item_id}"
                            send_discord(f"🎯 【新着発見】\n{target['name']}\n{price}円\n{url}")
                        checked_ids.add(item_id)
                time.sleep(5)
        except:
            pass
        time.sleep(30)

@app.route("/")
def home():
    return "BOT IS RUNNING"

if __name__ == "__main__":
    t = threading.Thread(target=monitor, daemon=True)
    t.start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
