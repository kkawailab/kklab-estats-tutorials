# /// script
# requires-python = ">=3.11"
# dependencies = ["requests"]
# ///
"""例題4: getMetaInfo で統計表のメタ情報（分類の定義）を取得する。

まず getStatsList で対象の統計表IDを1件見つけ、その表の「どんな項目があり、
どんなコードを指定できるか」を getMetaInfo で取得して表示する。
各分類の階層レベル（@level）も確認する。

実行:
    set -a; source .env; set +a
    uv run scripts/ex04_getmetainfo.py
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


def as_list(x) -> list:
    """単一オブジェクトのときはリストに包む。"""
    return x if isinstance(x, list) else [x]


def find_one_table(app_id: str, stats_code: str) -> tuple[str, str]:
    """statsCode に該当する統計表を1件見つけ、(ID, 表題) を返す。"""
    params = {"appId": app_id, "statsCode": stats_code, "limit": 1}
    body = requests.get(f"{BASE}/getStatsList", params=params, timeout=60).json()["GET_STATS_LIST"]
    if body["RESULT"]["STATUS"] != 0:
        sys.exit(f"検索エラー: {body['RESULT']['ERROR_MSG']}")
    t = as_list(body["DATALIST_INF"]["TABLE_INF"])[0]
    return t["@id"], text(t.get("TITLE"))


def main() -> None:
    app_id = get_app_id()

    # 消費者物価指数（00200573）の統計表を1件見つける
    stats_data_id, title = find_one_table(app_id, "00200573")
    print(f"対象の統計表: [ID:{stats_data_id}] {title}\n")

    # その表のメタ情報を取得
    params = {"appId": app_id, "statsDataId": stats_data_id}
    body = requests.get(f"{BASE}/getMetaInfo", params=params, timeout=60).json()["GET_META_INFO"]
    if body["RESULT"]["STATUS"] != 0:
        sys.exit(f"メタ取得エラー: {body['RESULT']['ERROR_MSG']}")

    class_objs = as_list(body["METADATA_INF"]["CLASS_INF"]["CLASS_OBJ"])
    print(f"この表は {len(class_objs)} 個の分類軸（次元）を持つ：\n")
    for obj in class_objs:
        classes = as_list(obj["CLASS"])
        print(f"● {obj['@id']:6s} = {obj['@name']}  （選択肢 {len(classes)} 件）")
        for c in classes[:3]:  # 先頭3件だけ例示
            lv = c.get("@level") or "-"
            print(f"     code={c['@code']:>10s}  level={lv}  {c['@name']}")
        if len(classes) > 3:
            print("     …")


if __name__ == "__main__":
    main()
