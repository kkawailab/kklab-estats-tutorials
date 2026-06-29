# /// script
# requires-python = ">=3.11"
# dependencies = ["requests"]
# ///
"""例題1: getStatsList でキーワード検索し、統計表の一覧を表示する。

e-Stat API の最初の一歩。キーワード「人口」を含む統計表を検索し、
各表に付く統計表ID（@id = statsDataId）と表題を表示する。

実行:
    set -a; source .env; set +a            # ESTAT_APPID を環境変数に展開
    uv run scripts/ex01_search_statslist.py
"""
import os
import sys

import requests

BASE = "https://api.e-stat.go.jp/rest/3.0/app/json"


def get_app_id() -> str:
    """環境変数 ESTAT_APPID を取得する（未設定なら終了）。"""
    app_id = os.environ.get("ESTAT_APPID")
    if not app_id:
        sys.exit(
            "環境変数 ESTAT_APPID が未設定です。'.env' を用意し、"
            "'set -a; source .env; set +a' を実行してから再度実行してください。"
        )
    return app_id


def text(x) -> str:
    """値が {'@...':.., '$': '本文'} の辞書のことがあるので文字列に正規化する。"""
    return x["$"] if isinstance(x, dict) else ("" if x is None else str(x))


def main() -> None:
    app_id = get_app_id()

    # --- リクエストのパラメータ ---
    params = {
        "appId": app_id,
        "searchWord": "人口",   # 「人口」を含む統計表を検索
        "limit": 10,            # 先頭10件だけ取得
    }
    res = requests.get(f"{BASE}/getStatsList", params=params, timeout=60)
    res.raise_for_status()
    body = res.json()["GET_STATS_LIST"]

    # --- STATUS が 0 以外ならエラー ---
    status = body["RESULT"]["STATUS"]
    if status != 0:
        sys.exit(f"APIエラー (STATUS={status}): {body['RESULT']['ERROR_MSG']}")

    info = body["DATALIST_INF"]
    print(f"ヒット総数: {info.get('NUMBER', '不明')} 件（先頭 {params['limit']} 件を表示）\n")

    # 1件だけのときは配列にならないのでリストに包む
    tables = info["TABLE_INF"]
    tables = tables if isinstance(tables, list) else [tables]

    for t in tables:
        stat_name = text(t.get("STAT_NAME"))      # 政府統計名
        title = text(t.get("TITLE"))              # 統計表の表題
        survey = text(t.get("SURVEY_DATE"))       # 調査年月
        print(f"[ID:{t['@id']}] {stat_name}")
        print(f"        表題: {title}  (調査:{survey})")


if __name__ == "__main__":
    main()
