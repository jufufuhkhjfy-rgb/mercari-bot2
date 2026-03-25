import os
import time
import threading
import requests
import random
from flask import Flask

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

def send_discord(text):
    try:
        requests.post(WEBHOOK_URL, json={"content": text}, timeout=10)
    except:
        pass

def get_items(keyword):
    # ここがログに出れば「関数は呼ばれている」
    print(f"DEBUG: {keyword} のリクエストを送信します...")
    
    url = "https://api.mercari.jp/v2/entities:search"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Mer-Os": "web",
        "X-Mer-Device": "pc"
    }
    payload = {
        "pageSize": 10,
        "searchSessionId": "test",
        "searchCondition": {"keyword": keyword, "status": ["ITEM_STATUS_ON_SALE"]},
        "serviceName": "mercari",
        "indexName": "main"
    }

    try:
        # timeoutを5秒に短縮して「沈黙」を防ぐ
        r = requests.post(url, headers=headers, json=payload, timeout=5)
        print(f"DEBUG: サーバー応答受信 (Status: {r.status_code})")
        if r.status_code == 200:
            items = r.json().get("items", [])
            print(f"DEBUG: {len(items)}件のデータを取得しました")
            return items
        return []
    except Exception as e:
        print(f"DEBUG: リクエスト失敗! 理由: {e}")
        return []

def monitor():
    print("=== 🤖 監視スレッド：ループ突入前 ===")
    send_discord("📢 最終デバッグ開始：今度こそ動かします")
    
    while True:
        try:
            for keyword, max_price in SEARCH_SETTINGS.items():
                print(f"--- 巡回ターゲット: {keyword} ---")
                items = get_items(keyword)
                
                for item in items:
                    item_id = item.get("id")
                    if not item_id or item_id in checked_ids:
                        continue
                    
                    price = int(item.get("price", 0))
                    if price <= max_price:
                        title = item.get("name")
                        url = f"https://jp.mercari.com/item/{item_id}"
                        send_discord(f"🎯 【{keyword}】\n{price}円\n{url}")
                        checked_ids.add(item_id)
                
                # キーワード間の待機をしっかり入れる
                time.sleep(2)

        except Exception as e:
            print(f"!!! ループ内でエラー発生: {e}")
        
        wait = 15
        print(f"=== 全キーワード完了。{wait}秒待機 === ")
        time.sleep(wait)

@app.route("/")
def home():
    return "ONLINE"

if __name__ == "__main__":
    t = threading.Thread(target=monitor, daemon=True)
    t.start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
