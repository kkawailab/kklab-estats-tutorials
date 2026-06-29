# /// script
# requires-python = ">=3.11"
# dependencies = ["requests"]
# ///
"""例題6: getStatsData の生 JSON 構造を観察する。

少量（limit=3）だけ取得し、レスポンスの入れ子構造（RESULT / RESULT_INF /
CLASS_INF / DATA_INF）を実際に目で見て理解する。メタ情報（CLASS_OBJ）と
データ（VALUE）の対応を確かめるのが狙い。

実行:
    set -a; source .env; set +a
    uv run scripts/ex06_inspect_json.py
"""
import json
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


def as_list(x) -> list:
    return x if isinstance(x, list) else [x]


def main() -> None:
    app_id = get_app_id()

    # 消費者物価指数の表を1件見つける
    p = {"appId": app_id, "statsCode": "00200573", "limit": 1}
    lst = requests.get(f"{BASE}/getStatsList", params=p, timeout=60).json()["GET_STATS_LIST"]
    table = as_list(lst["DATALIST_INF"]["TABLE_INF"])[0]
    sid = table["@id"]
    print(f"対象の統計表: [ID:{sid}] {text(table.get('TITLE'))}\n")

    # 先頭3件だけ取得
    params = {"appId": app_id, "statsDataId": sid, "limit": 3}
    sdata = requests.get(f"{BASE}/getStatsData", params=params, timeout=60).json()
    sdata = sdata["GET_STATS_DATA"]["STATISTICAL_DATA"]

    print("■ RESULT_INF（件数情報）")
    print(json.dumps(sdata["RESULT_INF"], ensure_ascii=False, indent=2))

    print("\n■ CLASS_INF の最初の次元（CLASS_OBJ[0]）の冒頭")
    obj0 = as_list(sdata["CLASS_INF"]["CLASS_OBJ"])[0]
    classes = as_list(obj0["CLASS"])
    preview = {"@id": obj0["@id"], "@name": obj0["@name"], "CLASS(先頭2件)": classes[:2]}
    print(json.dumps(preview, ensure_ascii=False, indent=2))

    print("\n■ DATA_INF の VALUE（数値セル）先頭3件")
    values = as_list(sdata["DATA_INF"]["VALUE"])
    print(json.dumps(values[:3], ensure_ascii=False, indent=2))
    print("\n→ VALUE の @cat01 等のコードを、CLASS_OBJ の同じ @id から名称に引ける（例題12）。")


if __name__ == "__main__":
    main()
