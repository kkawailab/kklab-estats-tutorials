# /// script
# requires-python = ">=3.11"
# dependencies = ["requests"]
# ///
"""例題28: getDataCatalog で公開ファイル（CSV/Excel等）を探す。

getStatsData が統計数値そのものを返すのに対し、getDataCatalog は e-Stat 上で
公開されているファイル資源（CSV・Excel・PDF・DB等）のカタログ情報を返す。
ここでは「家計調査」のCSV資源を検索し、ダウンロード用URLを一覧する。

実行:
    set -a; source .env; set +a
    uv run scripts/ex28_datacatalog.py
"""
import os
import sys

import requests

URL = "https://api.e-stat.go.jp/rest/3.0/app/json/getDataCatalog"


def as_list(x):
    return x if isinstance(x, list) else [x]


def text(x):
    return x["$"] if isinstance(x, dict) else ("" if x is None else str(x))


def main() -> None:
    app_id = os.environ.get("ESTAT_APPID") or sys.exit("ESTAT_APPID 未設定")

    params = {
        "appId": app_id,
        "searchWord": "家計調査",
        "dataType": "CSV",   # CSV形式の資源に限定
        "limit": 5,
    }
    body = requests.get(URL, params=params, timeout=60).json()["GET_DATA_CATALOG"]
    if body["RESULT"]["STATUS"] != 0:
        sys.exit(f"APIエラー: {body['RESULT']['ERROR_MSG']}")

    info = body["DATA_CATALOG_LIST_INF"]
    print(f"カタログのヒット数: {info.get('NUMBER')}（先頭{params['limit']}件）\n")

    for cat in as_list(info["DATA_CATALOG_INF"]):
        dataset = cat.get("DATASET", {})
        title = dataset.get("TITLE", {}).get("NAME", "")   # TITLE は辞書（NAME を取る）
        stat = text(dataset.get("STAT_NAME"))
        print(f"■ [{cat['@id']}] {stat} / {title[:50]}")
        # 各カタログに紐づくダウンロード資源（CSV等）の名称とURL
        resources = as_list(cat.get("RESOURCES", {}).get("RESOURCE", []))
        for r in resources[:3]:
            rname = r.get("TITLE", {}).get("NAME", "")
            url = r.get("URL", "")
            print(f"    - {rname[:40]}\n      {url}")


if __name__ == "__main__":
    main()
