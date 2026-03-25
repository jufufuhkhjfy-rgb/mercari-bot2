import os
import time
import threading
import requests
import random
from flask import Flask

# --- 設定 ---
SEARCH_SETTINGS = {
    "妖怪ウォッチ 真打": 99999,  # これでテスト！
    "妖怪ウォッチ スキヤキ": 3000,
    "妖怪ウォッチ スシ": 1000,
    "妖怪ウォッチ テンプラ": 1000,
    "妖怪ウォッチ 白犬隊": 1200,
    "妖怪ウォッチ 赤猫団": 2200
}

WEBHOOK_URL = "https://discordapp.com/api/webhooks/1476433652094341267/UVroNGFXVuigrRSmbFwebk0zCqNMC7XJJqh3obWt0MYXCk2s7qMhpG1ErqbjSfcitjoD"

app = Flask(__name__)
checked_ids = set()

def send_discord(text):
    try:
        requests.post(WEBHOOK_URL, json={"content": text}, timeout=10)
    except:
        pass

def get_items(keyword):
    # ログに出して進捗を確認
    print(f"🧐 {keyword} を検索中...")
    
    url = "https://api.mercari.jp/v2/entities:search"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Mer-Os": "web",
        "X-Mer-Device": "pc",
        "DNT": "1"
    }

    # メルカリ最新仕様のPayload
    payload = {
        "pageSize": 20,
        "searchSessionId": "test_" + str(int(time.time())),
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
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        if r.status_code != 200:
            print(f"❌ APIエラー: {r.status_code}")
            return []
        
        data = r.json()
        items = data.get("items", [])
        print(f"✨ 検索結果: {len(items)}件見つかりました") # ここが重要！
        return items
    except Exception as e:
        print(f"❌ 通信エラー: {e}")
        return []

def monitor():
    print("=== 🤖 監視スレッド：本格稼働開始 ===")
    send_discord("📢 監視を開始しました。真打99999円設定でテスト中...")
    
    while True:
        try:
            for keyword, max_price in SEARCH_SETTINGS.items():
                items = get_items(keyword)
                
                for item in items:
                    item_id = item.get("id")
                    if not item_id or item_id in checked_ids:
                        continue
                        
                    price = int(item.get("price", 0))
                    if price <= max_price:
                        title = item.get("name")
                        url = f"https://jp.mercari.com/item/{item_id}"
                        send_discord(f"🎯 **【{keyword}】**\n価格: {price}円\n商品名: {title}\n{url}")
                        checked_ids.add(item_id)
                
                time.sleep(3) # キーワード間の休憩

            if len(checked_ids) > 1000:
                checked_ids.clear()

        except Exception as e:
            print(f"💥 ループエラー: {e}")
        
        wait = random.randint(15, 30)
        print(f"☕ 巡回完了。{wait}秒待機します...")
        time.sleep(wait)

@app.route("/")
def home():
    return "Bot is running!"

if __name__ == "__main__":
    # スレッド起動
    threading.Thread(target=monitor, daemon=True).start()
    
    # ポート設定
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
