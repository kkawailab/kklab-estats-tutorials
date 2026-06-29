# /// script
# requires-python = ">=3.11"
# dependencies = ["requests"]
# ///
"""（開発用・チュートリアル本体には含めない）統計表IDと分類コードを探す補助ツール。

  uv run scripts/_discover.py search <キーワード> [limit]
  uv run scripts/_discover.py list   <statsCode> [keyword] [limit]
  uv run scripts/_discover.py meta   <statsDataId> [maxcodes]
"""
import os
import sys

import requests

BASE = "https://api.e-stat.go.jp/rest/3.0/app/json"
APP = os.environ["ESTAT_APPID"]


def text(x):
    return x["$"] if isinstance(x, dict) else ("" if x is None else str(x))


def as_list(x):
    return x if isinstance(x, list) else [x]


def cmd_list(stats_code=None, keyword=None, limit="20", search_word=None):
    params = {"appId": APP, "limit": int(limit)}
    if stats_code:
        params["statsCode"] = stats_code
    if search_word:
        params["searchWord"] = search_word
    if keyword:
        params["searchWord"] = keyword
    body = requests.get(f"{BASE}/getStatsList", params=params, timeout=60).json()["GET_STATS_LIST"]
    if body["RESULT"]["STATUS"] != 0:
        print("ERR", body["RESULT"]["ERROR_MSG"]); return
    info = body["DATALIST_INF"]
    print(f"# total={info.get('NUMBER')}")
    for t in as_list(info.get("TABLE_INF", [])):
        print(f"{t['@id']}\t{text(t.get('STATISTICS_NAME'))[:30]}\t{text(t.get('TITLE'))[:70]}\t{text(t.get('SURVEY_DATE'))}")


def cmd_meta(sid, maxcodes="8"):
    body = requests.get(f"{BASE}/getMetaInfo", params={"appId": APP, "statsDataId": sid}, timeout=60).json()["GET_META_INFO"]
    if body["RESULT"]["STATUS"] != 0:
        print("ERR", body["RESULT"]["ERROR_MSG"]); return
    print(f"# {text(body['METADATA_INF']['TABLE_INF'].get('TITLE'))}")
    for obj in as_list(body["METADATA_INF"]["CLASS_INF"]["CLASS_OBJ"]):
        cl = as_list(obj["CLASS"])
        print(f"\n== {obj['@id']} = {obj['@name']}  (n={len(cl)})")
        for c in cl[: int(maxcodes)]:
            print(f"   {c['@code']:>12s}  lv={c.get('@level') or '-':<3} {c['@name']}  [{c.get('@unit','')}]")


if __name__ == "__main__":
    cmd = sys.argv[1]
    args = sys.argv[2:]
    if cmd == "search":
        cmd_list(search_word=args[0], limit=args[1] if len(args) > 1 else "20")
    elif cmd == "list":
        cmd_list(stats_code=args[0],
                 keyword=args[1] if len(args) > 1 else None,
                 limit=args[2] if len(args) > 2 else "20")
    elif cmd == "meta":
        cmd_meta(args[0], args[1] if len(args) > 1 else "8")
