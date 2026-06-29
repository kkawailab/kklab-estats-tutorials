# /// script
# requires-python = ">=3.11"
# dependencies = ["requests"]
# ///
# 【超入門2】統計データから「数値を1つ」取り出す、最小のスクリプト。
#   消費者物価指数（総合・全国）の最新の指数を表示する。
#   実行: set -a; source .env; set +a
#         uv run scripts/min2_get_one_value.py
import os
import requests

app_id = os.environ["ESTAT_APPID"]

url = "https://api.e-stat.go.jp/rest/3.0/app/json/getStatsData"
params = {
    "appId": app_id,
    "statsDataId": "0003427113",  # 消費者物価指数（2020年基準）
    "cdCat01": "0001",            # 品目: 総合
    "cdArea": "00000",            # 地域: 全国
    "cdTab": "1",                 # 表章項目: 指数
    "limit": 10,                  # 新しい順に10件取得
}
data = requests.get(url, params=params).json()

# VALUE は数値セルのリスト。この表は新しい順なので [0] が最新。"$" がその数値。
value = data["GET_STATS_DATA"]["STATISTICAL_DATA"]["DATA_INF"]["VALUE"][0]
print("消費者物価指数（総合・全国）の最新値:", value["$"], "（2020年平均=100）")
