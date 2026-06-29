# /// script
# requires-python = ">=3.11"
# dependencies = ["requests"]
# ///
"""例題3: 統計分野（statsField）と複合キーワードで横断検索する。

statsField は統計分野コード（2桁=大分類）。ここでは「03 労働・賃金」分野から、
キーワードを AND 結合（空白区切り）して検索する例を示す。
searchKind / collectArea の使い方もコメントで示す。

実行:
    set -a; source .env; set +a
    uv run scripts/ex03_search_by_field.py
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


def search(app_id: str, **extra) -> dict:
    """getStatsList を呼んで DATALIST_INF を返す共通関数。"""
    params = {"appId": app_id, "limit": 10, **extra}
    res = requests.get(f"{BASE}/getStatsList", params=params, timeout=60)
    res.raise_for_status()
    body = res.json()["GET_STATS_LIST"]
    if body["RESULT"]["STATUS"] != 0:
        sys.exit(f"APIエラー: {body['RESULT']['ERROR_MSG']}")
    return body["DATALIST_INF"]


def show(info: dict, header: str) -> None:
    print(f"\n=== {header} ===")
    print(f"ヒット総数: {info.get('NUMBER', '不明')} 件")
    tables = info.get("TABLE_INF", [])
    tables = tables if isinstance(tables, list) else [tables]
    for t in tables[:5]:
        print(f"  [ID:{t['@id']}] {text(t.get('STATISTICS_NAME'))} / {text(t.get('TITLE'))}")


def main() -> None:
    app_id = get_app_id()

    # (1) 分野「03 労働・賃金」× キーワード AND（空白区切り）
    show(
        search(app_id, statsField="03", searchWord="賃金 産業"),
        "分野=労働・賃金, 「賃金」AND「産業」",
    )

    # (2) OR 検索（"|" でなく OR と書く）
    show(
        search(app_id, searchWord="完全失業率 OR 有効求人倍率"),
        "「完全失業率」OR「有効求人倍率」",
    )

    # (3) 市区町村別データに限定（collectArea=3）。searchKind=2 は小地域・地域メッシュ。
    show(
        search(app_id, searchWord="人口", collectArea="3"),
        "「人口」かつ 市区町村別集計（collectArea=3）",
    )


if __name__ == "__main__":
    main()
