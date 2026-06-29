# /// script
# requires-python = ">=3.11"
# dependencies = ["requests", "pandas"]
# ///
"""例題29: getStatsDatas で複数の統計表を一度に取得する。

statsDatasSpec に複数の取得条件（JSON配列）を渡すと、1回のリクエストで
複数表のデータをまとめて取得できる。ここでは消費者物価指数（総合・前年同月比）と
完全失業率の最新値を同時に取得する。

実行:
    set -a; source .env; set +a
    uv run scripts/ex29_bulk_stats.py
"""
import json
import os
import sys

import requests

import estat_api as e

URL = "https://api.e-stat.go.jp/rest/3.0/app/json/getStatsDatas"


def main() -> None:
    app_id = os.environ.get("ESTAT_APPID") or sys.exit("ESTAT_APPID 未設定")

    spec = [
        {"statsDataId": "0003427113", "cdTab": "3", "cdCat01": "0001",
         "cdArea": "00000", "lvTime": "4", "cdTimeFrom": "2026000101"},   # CPI総合・前年同月比
        {"statsDataId": "0003005865", "cdTab": "02", "cdCat01": "000",
         "cdCat02": "08", "cdCat03": "0", "cdTimeFrom": "2026000101"},    # 完全失業率
    ]
    # getStatsDatas は POST で呼ぶ（statsDatasSpec を本文に渡す）
    params = {"appId": app_id, "statsDatasSpec": json.dumps(spec, ensure_ascii=False)}
    body = requests.post(URL, data=params, timeout=120).json()["GET_STATS_DATAS"]
    if body["RESULT"]["STATUS"] != 0:
        sys.exit(f"APIエラー: {body['RESULT']['ERROR_MSG']}")

    # getStatsDatas は @requestNo で対応づく平坦な構造で返る
    sdl = body["STATISTICAL_DATA_LIST"]
    titles = {t["@requestNo"]: e.text(t.get("TITLE")) for t in e.as_list(sdl["TABLE_INF_LIST"]["TABLE_INF"])}

    print(f"一度のリクエストで {len(titles)} 表を取得しました。\n")
    for di in e.as_list(sdl["DATA_INF_LIST"]["DATA_INF"]):
        rno = di["@requestNo"]
        values = e.as_list(di["VALUE"])
        latest = max(values, key=lambda v: v["@time"])
        t = latest["@time"]
        period = f"{t[:4]}年{t[8:10]}月"   # 月次コード YYYY00MMMM
        print(f"■ {titles[rno][:40]}")
        print(f"    最新 {period}: {latest['$']}{latest.get('@unit', '')}")


if __name__ == "__main__":
    main()
