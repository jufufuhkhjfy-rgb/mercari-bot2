import os
import time
import threading
import requests
import random
import json
from flask import Flask

# ===== キーワードと上限価格 =====
SEARCH_SETTINGS = {
    "妖怪ウォッチ 真打": 99999,
    "妖怪ウォッチ スキヤキ": 3000,
    "妖怪ウォッチ スシ": 1000,
    "妖怪ウォッチ テンプラ": 1000,
    "妖怪ウォッチ 白犬隊": 1200,
    "妖怪ウォッチ 赤猫団": 2200
}

# ===== Discord webhook =====
WEBHOOK_URL = "https://discordapp.com/api/webhooks/1476433652094341267/UVroNGFXVuigrRSmbFwebk0zCqNMC7XJJqh3obWt0MYXCk2s7qMhpG1ErqbjSfcitjoD"

# ===== 除外ワード =====
NG_WORDS = ["ジャンク","壊れ","説明必読","オークション"]

# ===== 重複チェックファイル =====
CHECK_FILE = "checked.json"

app = Flask(__name__)

# ===== 重複URL読み込み =====
def load_checked():
    try:
        with open(CHECK_FILE,"r") as f:
            return set(json.load(f))
    except:
        return set()

checked_urls = load_checked()

def save_checked():
    with open(CHECK_FILE,"w") as f:
        json.dump(list(checked_urls),f)

# ===== Discord通知 =====
def send_discord(keyword, title, price, url):
    msg = (
        f"🔥 {keyword}\n"
        f"{price}円\n"
        f"{title}\n"
        f"{url}"
    )
    try:
        requests.post(WEBHOOK_URL, json={"content": msg}, timeout=10)
    except Exception as e:
        print("discord error", e)

# ===== メルカリ商品取得 =====
def get_items(keyword):
    url = "https://api.mercari.jp/v2/entities:search"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "ja-JP"
    }
    payload = {
        "keyword": keyword,
        "sort": "created_time",
        "order": "desc",
        "limit": 20,
        "status": "on_sale"
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
    except Exception as e:
        print("request error", e)
        return []

    print("取得:", keyword, "status", r.status_code)

    if r.status_code != 200:
        return []

    try:
        data = r.json()["items"]
    except Exception as e:
        print("json decode error", e)
        return []

    results = []
    for item in data:
        title = item["name"]
        price = item["price"]
        item_id = item["id"]
        item_url = f"https://jp.mercari.com/item/{item_id}"

        if item_url in checked_urls:
            continue
        if any(w in title for w in NG_WORDS):
            continue
        results.append((title, price, item_url))

    return results

# ===== 監視ループ =====
def monitor():
    print("monitor start")
    send_discord("起動確認", "bot started", 0, "")

    time.sleep(3)  # 初回遅延

    while True:
        try:
            for keyword, max_price in SEARCH_SETTINGS.items():
                items = get_items(keyword)
                for title, price, url in items:
                    if price <= max_price:
                        print("HIT", keyword, price)
                        send_discord(keyword, title, price, url)
                        checked_urls.add(url)
                        save_checked()
        except Exception as e:
            print("loop error", e)

        wait = random.randint(5, 15)  # 5〜15秒ランダム
        print("wait", wait)
        time.sleep(wait)

# ===== Flask確認ページ =====
@app.route("/")
def home():
    return "bot running"

# ===== Render起動時にスレッド開始 =====
def start_bot():
    t = threading.Thread(target=monitor)
    t.daemon = True
    t.start()

start_bot()

# ===== ローカルテスト用 =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
