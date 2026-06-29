# /// script
# requires-python = ">=3.11"
# dependencies = ["requests", "pandas"]
# ///
# 【超入門3】CSV形式で取得して pandas の表として読む、最小のスクリプト。
#   getSimpleStatsData は CSV を返すので、そのまま read_csv に渡せる。
#   実行: set -a; source .env; set +a
#         uv run scripts/min3_csv_to_pandas.py
import io
import os
import requests
import pandas as pd

app_id = os.environ["ESTAT_APPID"]

url = "https://api.e-stat.go.jp/rest/3.0/app/getSimpleStatsData"   # ← CSV版
params = {
    "appId": app_id,
    "statsDataId": "0003427113",  # 消費者物価指数（2020年基準）
    "cdCat01": "0001",            # 総合
    "cdArea": "00000",            # 全国
    "cdTab": "1",                 # 指数
    "sectionHeaderFlg": "2",      # 説明ヘッダ行を省く
    "limit": 5,
}
csv_text = requests.get(url, params=params).text
df = pd.read_csv(io.StringIO(csv_text))       # 文字列を pandas の表に

print(df[["時間軸（年・月）", "value"]])         # 時点と値だけ表示
