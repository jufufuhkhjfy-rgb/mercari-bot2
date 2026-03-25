import os
import time
import threading
import requests
import random
from flask import Flask

# 警告を非表示にする
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
        requests.post(WEBHOOK_URL, json={"content": text}, timeout=5)
    except:
        pass

def get_items(keyword):
    print(f"DEBUG: {keyword} のAPI接続を試行します...")
    url = "https://api.mercari.jp/v2/entities:search"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
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
        # verify=False と timeout=5 でフリーズを物理的に防ぐ
        r = requests.post(url, headers=headers, json=payload, timeout=5, verify=False)
        print(f"DEBUG: 応答あり (Status: {r.status_code})")
        if r.status_code == 200:
            return r.json().get("items", [])
        return []
    except Exception as e:
        print(f"DEBUG: 通信エラー発生: {e}")
        return []

def monitor():
    print("LOG: 監視スレッド、本格始動します！")
    send_discord("📢 接続設定を修正しました。巡回を開始します。")
    
    while True:
        try:
            for target in SEARCH_LIST:
                keyword = target["name"]
                print(f"LOG: 検索実行 -> {keyword}")
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
                
                time.sleep(5)

        except Exception as e:
            print(f"CRITICAL: {e}")
        
        print("LOG: 一巡完了。30秒待機。")
        time.sleep(30)

@app.route("/")
def home():
    return "Bot is active"

if __name__ == "__main__":
    t = threading.Thread(target=monitor, daemon=True)
    t.start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
