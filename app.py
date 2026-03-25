import os
import time
import threading
import requests
import random
import json
from flask import Flask

# ===== キーワードと上限価格 =====
SEARCH_SETTINGS = {
    "妖怪ウォッチ 真打": 2000,
    "妖怪ウォッチ スキヤキ": 3000,
    "妖怪ウォッチ スシ": 1000,
    "妖怪ウォッチ テンプラ": 1000,
    "妖怪ウォッチ 白犬隊": 1200,
    "妖怪ウォッチ 赤猫団": 2200
}

WEBHOOK_URL = "https://discordapp.com/api/webhooks/1476433652094341267/UVroNGFXVuigrRSmbFwebk0zCqNMC7XJJqh3obWt0MYXCk2s7qMhpG1ErqbjSfcitjoD"
NG_WORDS = ["ジャンク","壊れ","説明必読"]

app = Flask(__name__)
checked_ids = set() # Renderではファイル保存が消えるためメモリで管理

def send_discord(msg):
    try:
        requests.post(WEBHOOK_URL, json={"content": msg}, timeout=10)
    except Exception as e:
        print("Discord送信失敗:", e)

def get_items(keyword):
    # メルカリ内部APIの正しいエンドポイント
    url = "https://api.mercari.jp/v2/entities:search"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "DNT": "1"
    }

    # ここが重要：メルカリAPIが受け付ける正しいJSON形式
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
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        print(f"検索実行: {keyword} / Status: {r.status_code}")
        
        if r.status_code != 200:
            return []

        data = r.json()
        return data.get("items", [])
    except Exception as e:
        print(f"リクエストエラー ({keyword}):", e)
        return []

def monitor():
    print("--- 監視スレッド開始 ---")
    send_discord("🚀 監視Botが正常に起動しました")

    while True:
        try:
            for keyword, max_price in SEARCH_SETTINGS.items():
                items = get_items(keyword)
                
                for item in items:
                    item_id = item.get("id")
                    title = item.get("name")
                    price = int(item.get("price", 0))
                    item_url = f"https://jp.mercari.com/item/{item_id}"

                    # 重複・価格・NGワードの判定
                    if item_id in checked_ids:
                        continue
                    if price > max_price:
                        continue
                    if any(w in title for w in NG_WORDS):
                        continue

                    # 条件合致！通知
                    print(f"【HIT】{keyword}: {price}円 / {title}")
                    msg = f"🔥 **新着発見**\nキーワード: {keyword}\n価格: {price}円\n商品名: {title}\nURL: {item_url}"
                    send_discord(msg)
                    
                    checked_ids.add(item_id)
                
                # キーワードごとに少し待機（負荷軽減）
                time.sleep(2)

            # リストが肥大化しすぎないようリセット（1000件超えたら）
            if len(checked_ids) > 1000:
                checked_ids.clear()

        except Exception as e:
            print("ループ内エラー:", e)

        wait_time = random.randint(10, 20) # BAN防止のため少し長めに設定
        print(f"次回の巡回まで {wait_time} 秒待機...")
        time.sleep(wait_time)

@app.route("/")
def home():
    return "Bot is alive"

# Render起動用
if __name__ == "__main__":
    # 監視スレッドを起動
    threading.Thread(target=monitor, daemon=True).start()
    
    # サーバー起動
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
