# /// script
# requires-python = ">=3.11"
# dependencies = ["requests"]
# ///
"""例題11: ページネーション（NEXT_KEY と startPosition）。

1回のリクエストで返る件数には上限がある（既定10万件）。上限を超える表は、
応答の RESULT_INF.NEXT_KEY を次の startPosition に渡して繰り返し取得する。
ここでは巨大な表（消費者物価指数）に対し、limit=1000 で3ページだけ取得して
ページ送りの仕組みを確認する。

実行:
    set -a; source .env; set +a
    uv run scripts/ex11_pagination.py
"""
import os
import sys

import requests

URL = "https://api.e-stat.go.jp/rest/3.0/app/json/getStatsData"
SID = "0003427113"  # 消費者物価指数（2020年基準, 非常に大きい表）


def main() -> None:
    app_id = os.environ.get("ESTAT_APPID")
    if not app_id:
        sys.exit("環境変数 ESTAT_APPID が未設定です。'.env' を設定してください。")

    start = 1
    page = 0
    collected = 0
    while True:
        params = {"appId": app_id, "statsDataId": SID, "limit": 1000, "startPosition": start}
        body = requests.get(URL, params=params, timeout=120).json()["GET_STATS_DATA"]
        if body["RESULT"]["STATUS"] != 0:
            sys.exit(f"APIエラー: {body['RESULT']['ERROR_MSG']}")

        info = body["STATISTICAL_DATA"]["RESULT_INF"]
        values = body["STATISTICAL_DATA"]["DATA_INF"]["VALUE"]
        collected += len(values)
        page += 1
        print(
            f"ページ{page}: TOTAL={int(info['TOTAL_NUMBER']):,} 件中 "
            f"{info['FROM_NUMBER']}〜{info['TO_NUMBER']} を取得 "
            f"(NEXT_KEY={info.get('NEXT_KEY')})"
        )

        next_key = info.get("NEXT_KEY")
        if not next_key or page >= 3:   # NEXT_KEY が無ければ完了。ここではデモのため3ページで打ち切り
            break
        start = next_key

    print(f"\nこのデモでは {collected:,} 件を取得した（全件取得するには打ち切りを外す）。")


if __name__ == "__main__":
    main()
