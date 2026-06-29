# /// script
# requires-python = ">=3.11"
# dependencies = ["requests", "pandas"]
# ///
"""例題2: 政府統計コードで絞って検索し、一覧を pandas で整形して CSV 保存する。

statsCode=00200521（国勢調査）の統計表を検索し、主要な項目を DataFrame にして
output/ex02_statslist_census.csv に保存する。Excel で開けるよう BOM 付き UTF-8 とする。

実行:
    set -a; source .env; set +a
    uv run scripts/ex02_search_by_statscode.py
"""
import os
import sys

import pandas as pd
import requests

BASE = "https://api.e-stat.go.jp/rest/3.0/app/json"


def get_app_id() -> str:
    app_id = os.environ.get("ESTAT_APPID")
    if not app_id:
        sys.exit("環境変数 ESTAT_APPID が未設定です。'.env' を設定してください。")
    return app_id


def text(x) -> str:
    return x["$"] if isinstance(x, dict) else ("" if x is None else str(x))


def main() -> None:
    app_id = get_app_id()

    params = {
        "appId": app_id,
        "statsCode": "00200521",   # 国勢調査（政府統計コード）
        "limit": 100,
    }
    res = requests.get(f"{BASE}/getStatsList", params=params, timeout=60)
    res.raise_for_status()
    body = res.json()["GET_STATS_LIST"]
    if body["RESULT"]["STATUS"] != 0:
        sys.exit(f"APIエラー: {body['RESULT']['ERROR_MSG']}")

    tables = body["DATALIST_INF"]["TABLE_INF"]
    tables = tables if isinstance(tables, list) else [tables]

    # 必要な列だけ取り出して表（DataFrame）にする
    rows = []
    for t in tables:
        rows.append(
            {
                "統計表ID": t["@id"],
                "政府統計名": text(t.get("STAT_NAME")),
                "提供統計名": text(t.get("STATISTICS_NAME")),
                "表題": text(t.get("TITLE")),
                "周期": text(t.get("CYCLE")),
                "調査年月": text(t.get("SURVEY_DATE")),
                "公開日": text(t.get("OPEN_DATE")),
            }
        )
    df = pd.DataFrame(rows)

    os.makedirs("output", exist_ok=True)
    out = "output/ex02_statslist_census.csv"
    df.to_csv(out, index=False, encoding="utf-8-sig")  # BOM付きで Excel 対応

    print(f"国勢調査の統計表: {len(df)} 件取得")
    print(df[["統計表ID", "表題", "調査年月"]].head(10).to_string(index=False))
    print(f"\n→ 全件を {out} に保存しました。")


if __name__ == "__main__":
    main()
