# /// script
# requires-python = ">=3.11"
# dependencies = ["requests"]
# ///
"""例題5: cntGetFlg=Y で「取得件数」だけを先に確認する。

巨大な統計表をいきなり全件取得すると時間も通信量もかかる。getStatsData に
cntGetFlg=Y を付けると、データ本体を返さずに該当件数（TOTAL_NUMBER）だけを返す。
これで規模を把握し、limit やページングの方針を決められる。

実行:
    set -a; source .env; set +a
    uv run scripts/ex05_count_records.py
"""
import os
import sys

import requests

BASE = "https://api.e-stat.go.jp/rest/3.0/app/json"


def get_app_id() -> str:
    app_id = os.environ.get("ESTAT_APPID")
    if not app_id:
        sys.exit("環境変数 ESTAT_APPID が未設定です。'.env' を設定してください。")
    return app_id


def text(x) -> str:
    return x["$"] if isinstance(x, dict) else ("" if x is None else str(x))


def find_one_table(app_id: str, stats_code: str) -> tuple[str, str]:
    params = {"appId": app_id, "statsCode": stats_code, "limit": 1}
    body = requests.get(f"{BASE}/getStatsList", params=params, timeout=60).json()["GET_STATS_LIST"]
    t = body["DATALIST_INF"]["TABLE_INF"]
    t = t[0] if isinstance(t, list) else t
    return t["@id"], text(t.get("TITLE"))


def main() -> None:
    app_id = get_app_id()

    # 労働力調査（00200531）の表を1件見つける
    stats_data_id, title = find_one_table(app_id, "00200531")
    print(f"対象の統計表: [ID:{stats_data_id}] {title}\n")

    # cntGetFlg=Y：件数だけを問い合わせる（データ本体は返らない）
    params = {
        "appId": app_id,
        "statsDataId": stats_data_id,
        "cntGetFlg": "Y",
        "metaGetFlg": "N",
    }
    body = requests.get(f"{BASE}/getStatsData", params=params, timeout=60).json()["GET_STATS_DATA"]
    if body["RESULT"]["STATUS"] != 0:
        sys.exit(f"APIエラー: {body['RESULT']['ERROR_MSG']}")

    total = int(body["STATISTICAL_DATA"]["RESULT_INF"]["TOTAL_NUMBER"])
    print(f"この表の総データ件数（セル数）: {total:,} 件")

    limit = 100_000  # 1回あたりの既定上限
    pages = -(-total // limit)  # 切り上げ
    print(f"1回 {limit:,} 件取得とすると、全件には約 {pages} 回のリクエストが必要。")
    if total <= limit:
        print("→ 1回のリクエストで全件取得できる規模です。")
    else:
        print("→ NEXT_KEY を使ったページネーションが必要です（例題11参照）。")


if __name__ == "__main__":
    main()
