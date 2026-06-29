# /// script
# requires-python = ">=3.11"
# dependencies = ["requests"]
# ///
# 【超入門1】e-Stat API で統計表を検索する、最小のスクリプト。
#   実行: set -a; source .env; set +a   （で ESTAT_APPID を読み込む）
#         uv run scripts/min1_hello_search.py
import os
import requests

app_id = os.environ["ESTAT_APPID"]            # appId を環境変数から取得

# 「人口」というキーワードで統計表を検索する（JSON形式で受け取る）
url = "https://api.e-stat.go.jp/rest/3.0/app/json/getStatsList"
params = {"appId": app_id, "searchWord": "人口", "limit": 3}
data = requests.get(url, params=params).json()

# ヒット件数と、先頭3件の表題を表示する
info = data["GET_STATS_LIST"]["DATALIST_INF"]
print(info["NUMBER"], "件ヒットしました。先頭3件：")
for table in info["TABLE_INF"]:
    print(" -", table["TITLE"]["$"] if isinstance(table["TITLE"], dict) else table["TITLE"])
