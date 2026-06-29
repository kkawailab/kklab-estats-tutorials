# /// script
# requires-python = ">=3.11"
# dependencies = ["requests", "pandas", "matplotlib"]
# ///
# 【超入門4】取得したデータをグラフにする、最小のスクリプト。
#   消費者物価指数（総合・全国）の月次推移を折れ線にして figures/ に保存する。
#   実行: set -a; source .env; set +a
#         uv run scripts/min4_quick_plot.py
import io
import os
import requests
import pandas as pd
import matplotlib
matplotlib.use("Agg")                 # 画面を使わず画像ファイルに保存するための設定
import matplotlib.pyplot as plt

# 日本語が□（豆腐）になる場合は、環境にあるフォント名に変えてください
plt.rcParams["font.family"] = "Noto Sans CJK JP"

app_id = os.environ["ESTAT_APPID"]

url = "https://api.e-stat.go.jp/rest/3.0/app/getSimpleStatsData"
params = {
    "appId": app_id, "statsDataId": "0003427113",
    "cdCat01": "0001", "cdArea": "00000", "cdTab": "1",
    "lvTime": "4", "cdTimeFrom": "2024000101",  # 2024年1月以降の月次
    "sectionHeaderFlg": "2",
}
df = pd.read_csv(io.StringIO(requests.get(url, params=params).text))
df = df.sort_values("time_code")      # 時点コードの昇順に並べ替え

plt.plot(range(len(df)), df["value"], marker="o")
plt.title("消費者物価指数（総合・全国）の推移")
plt.ylabel("指数（2020年平均=100）")
plt.xlabel("月（古い→新しい）")

os.makedirs("figures", exist_ok=True)
plt.savefig("figures/min4_cpi.pdf", bbox_inches="tight")
print("グラフを figures/min4_cpi.pdf に保存しました。")
