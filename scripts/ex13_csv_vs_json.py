# /// script
# requires-python = ">=3.11"
# dependencies = ["requests", "pandas"]
# ///
"""例題13: CSV(getSimpleStatsData) と JSON の取得を比べる。

同じ条件（消費者物価指数 総合・全国・月次）を、CSV簡易版とJSONの両方で取得して、
得られる数値が一致することを確認する。CSVは pandas.read_csv に直接渡せて手軽。

実行:
    set -a; source .env; set +a
    uv run scripts/ex13_csv_vs_json.py
"""
import io

import pandas as pd
import requests

import estat_api as e

CSV_URL = "https://api.e-stat.go.jp/rest/3.0/app/getSimpleStatsData"
SID = "0003427113"
COND = dict(cdCat01="0001", cdArea="00000", cdTab="1", lvTime="4", cdTimeFrom="2025000101")


def main() -> None:
    app_id = e.get_app_id()

    # --- CSV（簡易版）。sectionHeaderFlg=2 で説明ヘッダ行を省く ---
    params = {"appId": app_id, "statsDataId": SID, "sectionHeaderFlg": "2", **COND}
    text = requests.get(CSV_URL, params=params, timeout=120).text
    csv_df = pd.read_csv(io.StringIO(text)).sort_values("time_code")
    print("■ CSV(getSimpleStatsData) の列:", list(csv_df.columns))
    print(csv_df[["time_code", "時間軸（年・月）", "value"]].tail(3).to_string(index=False))

    # --- JSON（estat_api 経由） ---
    sdata = e.get_stats_data(app_id, SID, **COND)
    json_df = e.stats_data_to_frame(sdata).sort_values("time_code")
    print("\n■ JSON の直近3件:")
    print(json_df[["time", "値"]].tail(3).to_string(index=False))

    # --- 値の一致を確認（同じ最新月どうし） ---
    csv_last = float(csv_df.iloc[-1]["value"])
    json_last = float(json_df.iloc[-1]["値"])
    print(f"\n最新値の一致確認: CSV={csv_last} / JSON={json_last} → "
          f"{'一致' if csv_last == json_last else '不一致'}")


if __name__ == "__main__":
    main()
