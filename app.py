import os
import time
import threading
import httpx
import random
from flask import Flask

# 監視するキーワードと価格
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
    except Exception as e:
        print(f"Discord送信エラー: {e}")

def get_items(keyword):
    print(f"--- 検索開始: {keyword} ---")
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
        with httpx.Client(headers=headers, timeout=5.0, verify=False) as client:
            r = client.post(url, json=payload)
            if r.status_code == 200:
                items = r.json().get("items", [])
                print(f"結果: {len(items)}件発見")
                return items
            print(f"APIエラー: {r.status_code}")
    except Exception as e:
        print(f"通信失敗: {e}")
    return []

def monitor_loop():
    """バックグラウンドで回るループ"""
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
                            send_discord(f"🎯 【{target['name']}】\n{price}円\n{url}")
                            checked_ids.add(item_id)
                time.sleep(10) # 1単語ごとに10秒あける（BAN防止）
        except Exception as e:
            print(f"ループエラー: {e}")
        print("一巡しました。30秒待機します。")
        time.sleep(30)

@app.route("/")
def home():
    return "BOT RUNNING"

if __name__ == "__main__":
    # 1. 起動メッセージをDiscordに送る（疎通確認）
    send_discord("🚀 システムを再起動しました。監視を再開します。")
    
    # 2. 監視ループを別スレッドで開始
    t = threading.Thread(target=monitor_loop, daemon=True)
    t.start()
    
    # 3. ウェブサーバー起動
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
