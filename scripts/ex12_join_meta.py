# /// script
# requires-python = ">=3.11"
# dependencies = ["requests", "pandas"]
# ///
"""例題12: データとメタ情報を別々に取得して結合する（metaGetFlg=N）。

同じ表から条件を変えて何度もデータを取る場合、毎回メタ情報まで受け取るのは無駄。
metaGetFlg=N でデータ（コードのみ）を取得し、メタ情報は getMetaInfo で1回だけ取って
コード→名称の対応表を作り、後で結合する。estat_api モジュールの仕組みを分解して示す。

実行:
    set -a; source .env; set +a
    uv run scripts/ex12_join_meta.py
"""
import pandas as pd

import estat_api as e

SID = "0003427113"  # 消費者物価指数（2020年基準）


def main() -> None:
    app_id = e.get_app_id()

    # (1) メタ情報を1回だけ取得し、コード→名称の辞書を作る
    class_objs = e.get_meta_info(app_id, SID)
    code2name = {o["@id"]: {c["@code"]: c["@name"] for c in e.as_list(o["CLASS"])} for o in class_objs}
    print("メタ情報の次元:", [o["@id"] for o in class_objs])

    # (2) データはメタ抜き（metaGetFlg=N）で取得 → VALUE はコードだけ
    sdata = e.get_stats_data(
        app_id, SID, metaGetFlg="N",
        cdCat01="0001", cdArea="00000", cdTab="1",
        lvTime="4", cdTimeFrom="2025000101",
    )
    raw = pd.DataFrame(e.as_list(sdata["DATA_INF"]["VALUE"]))
    print("\nメタ抜きの生データ（コードのみ）の先頭：")
    print(raw.head(3).to_string(index=False))

    # (3) 自前で結合：@time コードを (1) の辞書で名称に変換
    raw["時点"] = raw["@time"].map(code2name["time"])
    raw["品目"] = raw["@cat01"].map(code2name["cat01"])
    raw["値"] = pd.to_numeric(raw["$"], errors="coerce")
    print("\nコードを名称に結合した結果（直近5件）：")
    print(raw.sort_values("@time")[["時点", "品目", "値"]].tail(5).to_string(index=False))


if __name__ == "__main__":
    main()
