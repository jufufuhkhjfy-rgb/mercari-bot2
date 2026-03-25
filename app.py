import os
import time
import threading
import requests
import random
from flask import Flask

# 辞書を一度シンプルな変数にします
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
        requests.post(WEBHOOK_URL, json={"content": text}, timeout=10)
    except:
        pass

def get_items(keyword):
    print(f"DEBUG: {keyword} をAPIで検索開始...")
    url = "https://api.mercari.jp/v2/entities:search"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Mer-Os": "web",
        "X-Mer-Device": "pc"
    }
    payload = {
        "pageSize": 5,
        "searchCondition": {"keyword": keyword, "status": ["ITEM_STATUS_ON_SALE"]},
        "serviceName": "mercari",
        "indexName": "main"
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        if r.status_code == 200:
            items = r.json().get("items", [])
            print(f"DEBUG: {len(items)}件見つかりました")
            return items
        print(f"DEBUG: エラー応答 {r.status_code}")
        return []
    except Exception as e:
        print(f"DEBUG: 通信失敗 {e}")
        return []

def monitor():
    print("LOG: 監視スレッド、ループ開始します！")
    send_discord("📢 システム巡回を開始しました。")
    
    while True:
        try:
            # 辞書ではなくリストで確実に回す
            for target in SEARCH_LIST:
                keyword = target["name"]
                max_p = target["price"]
                
                print(f"LOG: 検索中 -> {keyword}")
                items = get_items(keyword)
                
                for item in items:
                    item_id = item.get("id")
                    if not item_id or item_id in checked_ids:
                        continue
                    
                    price = int(item.get("price", 0))
                    if price <= max_p:
                        url = f"https://jp.mercari.com/item/{item_id}"
                        send_discord(f"🎯 【{keyword}】\n{price}円\n{url}")
                        checked_ids.add(item_id)
                
                time.sleep(3)

        except Exception as e:
            print(f"CRITICAL: ループ内でエラーが発生しました: {e}")
        
        print("LOG: 一巡しました。30秒休みます。")
        time.sleep(30)

@app.route("/")
def home():
    return "WORKING"

if __name__ == "__main__":
    # スレッド起動
    t = threading.Thread(target=monitor, daemon=True)
    t.start()
    
    # サーバー起動
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
