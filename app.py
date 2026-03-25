import time
import re
import threading
import requests
import random
import json
import urllib.parse
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

# Discord webhook
WEBHOOK_URL = "https://discordapp.com/api/webhooks/1476433652094341267/UVroNGFXVuigrRSmbFwebk0zCqNMC7XJJqh3obWt0MYXCk2s7qMhpG1ErqbjSfcitjoD"

# 除外ワード
ng_words = ["ジャンク","壊れ","説明必読","オークション"]

# 重複チェック保存ファイル
CHECK_FILE = "checked.json"

app = Flask("__main__")

# ===== 重複URL読み込み =====
def load_checked():
    try:
        with open(CHECK_FILE,"r") as f:
            return set(json.load(f))
    except:
        return set()

# ===== 保存 =====
def save_checked():
    with open(CHECK_FILE,"w") as f:
        json.dump(list(checked_urls),f)

checked_urls = load_checked()

# ===== Discord通知 =====
def send_discord(keyword,title,price,url):

    data = {
        "content":
        f"🔥 {keyword}\n"
        f"{price}円\n"
        f"{title}\n"
        f"{url}"
    }

    requests.post(WEBHOOK_URL,json=data)

# ===== メルカリ取得 =====
def get_items(keyword):

    url = f"https://jp.mercari.com/search?keyword={urllib.parse.quote(keyword)}&sort=created_time&order=desc"

    headers = {
        "User-Agent":"Mozilla/5.0"
    }

    r = requests.get(url,headers=headers)

    links = re.findall(r'href="(/item/.*?)"',r.text)

    items = []

    for link in links:

        full_url = "https://jp.mercari.com"+link

        if full_url in checked_urls:
            continue

        # 価格とタイトル取得
        block = re.search(link+r'.*?¥([\d,]+).*?>(.*?)<',r.text,re.S)

        if not block:
            continue

        price = int(block.group(1).replace(",",""))

        title = re.sub("<.*?>","",block.group(2))

        # NGワード除外
        if any(w in title for w in ng_words):
            continue

        items.append((title,price,full_url))

    return items

# ===== 監視ループ =====
def monitor():

    while True:

        try:

            for keyword,max_price in SEARCH_SETTINGS.items():

                items = get_items(keyword)

                for title,price,url in items:

                    if price <= max_price:

                        print(keyword,price)

                        send_discord(keyword,title,price,url)

                        checked_urls.add(url)

                        save_checked()

        except Exception as e:
            print("error",e)

        # 5〜15秒待機
        wait = random.randint(5,15)

        print("wait",wait)

        time.sleep(wait)

# ===== Renderが起動確認に使うページ =====
@app.route("/")
def home():
    return "bot running"

# 起動
threading.Thread(target=monitor,daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=10000)