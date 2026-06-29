"""e-Stat API 用の小さな共通モジュール（例題7以降で再利用する）。

このファイルは他のスクリプトから import して使う。import 専用のため PEP 723 の
メタデータは持たない（利用側スクリプトの dependencies に requests, pandas を書く）。

主な関数:
  get_app_id()                       環境変数 ESTAT_APPID を取得
  get_stats_list(app_id, **params)   getStatsList → TABLE_INF のリスト
  get_meta_info(app_id, sid)         getMetaInfo  → CLASS_OBJ のリスト
  get_stats_data(app_id, sid, ...)   getStatsData → STATISTICAL_DATA（fetch_all で全件）
  stats_data_to_frame(stat_data)     コードを名称に変換した tidy な DataFrame
"""
from __future__ import annotations

import os
import sys

import pandas as pd
import requests

BASE = "https://api.e-stat.go.jp/rest/3.0/app/json"


def get_app_id() -> str:
    """環境変数 ESTAT_APPID を取得する（未設定なら終了）。"""
    app_id = os.environ.get("ESTAT_APPID")
    if not app_id:
        sys.exit(
            "環境変数 ESTAT_APPID が未設定です。'.env' を用意し、"
            "'set -a; source .env; set +a' を実行してください。"
        )
    return app_id


def as_list(x) -> list:
    """単一オブジェクトのときはリストに包む（要素数1だと配列にならないAPI仕様への対策）。"""
    return x if isinstance(x, list) else ([] if x is None else [x])


def text(x) -> str:
    """{'@..':.., '$':'本文'} 形式の値を文字列に正規化する。"""
    return x["$"] if isinstance(x, dict) else ("" if x is None else str(x))


def _get(func: str, params: dict) -> dict:
    res = requests.get(f"{BASE}/{func}", params=params, timeout=120)
    res.raise_for_status()
    return res.json()


def get_stats_list(app_id: str, **params) -> list[dict]:
    body = _get("getStatsList", {"appId": app_id, **params})["GET_STATS_LIST"]
    if body["RESULT"]["STATUS"] != 0:
        sys.exit(f"getStatsList エラー: {body['RESULT']['ERROR_MSG']}")
    return as_list(body["DATALIST_INF"].get("TABLE_INF", []))


def get_meta_info(app_id: str, stats_data_id: str) -> list[dict]:
    body = _get("getMetaInfo", {"appId": app_id, "statsDataId": stats_data_id})["GET_META_INFO"]
    if body["RESULT"]["STATUS"] != 0:
        sys.exit(f"getMetaInfo エラー: {body['RESULT']['ERROR_MSG']}")
    return as_list(body["METADATA_INF"]["CLASS_INF"]["CLASS_OBJ"])


def get_stats_data(app_id: str, stats_data_id: str, *, fetch_all: bool = False, **params) -> dict:
    """getStatsData を呼ぶ。fetch_all=True なら NEXT_KEY を辿って全件を結合する。"""
    base = {"appId": app_id, "statsDataId": stats_data_id, **params}
    body = _get("getStatsData", base)["GET_STATS_DATA"]
    if body["RESULT"]["STATUS"] != 0:
        sys.exit(f"getStatsData エラー: {body['RESULT']['ERROR_MSG']}")
    sdata = body["STATISTICAL_DATA"]
    values = as_list(sdata.get("DATA_INF", {}).get("VALUE"))
    next_key = sdata["RESULT_INF"].get("NEXT_KEY")
    while fetch_all and next_key:
        body = _get("getStatsData", {**base, "startPosition": next_key})["GET_STATS_DATA"]
        if body["RESULT"]["STATUS"] != 0:
            sys.exit(f"getStatsData エラー: {body['RESULT']['ERROR_MSG']}")
        sd2 = body["STATISTICAL_DATA"]
        values += as_list(sd2.get("DATA_INF", {}).get("VALUE"))
        next_key = sd2["RESULT_INF"].get("NEXT_KEY")
    sdata.setdefault("DATA_INF", {})["VALUE"] = values
    return sdata


def stats_data_to_frame(sdata: dict) -> pd.DataFrame:
    """STATISTICAL_DATA を tidy な DataFrame にする。

    返る列は予測可能な名前にそろえる:
      - 各次元 id（tab, cat01, area, time …）には「名称」が入る
      - 同名 + '_code' 列に元のコードが入る
      - '値' に数値、'単位' に単位
    """
    objs = as_list(sdata["CLASS_INF"]["CLASS_OBJ"])
    code2name = {o["@id"]: {c["@code"]: c["@name"] for c in as_list(o["CLASS"])} for o in objs}

    raw = pd.DataFrame(as_list(sdata["DATA_INF"]["VALUE"]))
    out = {}
    for col in raw.columns:
        if col == "$":
            out["値"] = pd.to_numeric(raw[col], errors="coerce")
        elif col == "@unit":
            out["単位"] = raw[col]
        elif col == "@annotation":
            out["annotation"] = raw[col]
        elif col.startswith("@"):
            key = col[1:]                       # 例: '@cat01' → 'cat01'
            out[f"{key}_code"] = raw[col]
            if key in code2name:
                out[key] = raw[col].map(code2name[key])
    return pd.DataFrame(out)
