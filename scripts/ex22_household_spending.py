# /// script
# requires-python = ">=3.11"
# dependencies = ["requests", "pandas", "matplotlib"]
# ///
"""例題22: 家計調査から費目別消費支出の構成を描く。

家計調査（家計収支編・二人以上の世帯, 品目分類2020年改定, 統計表ID 0003348239）から、
10大費目別の消費支出（最新月）を取得し、構成比を円グラフにする。

実行:
    set -a; source .env; set +a
    uv run scripts/ex22_household_spending.py
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import jpfont  # noqa: F401  matplotlib の日本語フォントを設定（jpfont.py）

import estat_api as e

SID = "0003348239"
# 10大費目の品目コード（1 食料 〜 10 その他の消費支出）
HIMOKU = ["010000000", "020000000", "030000000", "040000000", "050000000",
          "060000000", "070000000", "080000000", "090000000", "100000000"]


def main() -> None:
    app_id = e.get_app_id()

    sdata = e.get_stats_data(
        app_id, SID,
        cdCat01=",".join(HIMOKU),
        cdCat02="03",      # 世帯区分: 二人以上の世帯（2000年～）
        cdArea="00000",    # 全国
    )
    df = e.stats_data_to_frame(sdata)

    # 最新年に絞る
    df = df[df["time_code"] == df["time_code"].max()]
    period = df["time"].iloc[0]
    df = df.sort_values("値", ascending=False)

    # 費目名の先頭の番号を取り、見やすいラベルに
    labels = [name.split(maxsplit=1)[-1] for name in df["cat01"]]

    fig, ax = plt.subplots(figsize=(7, 6))
    ax.pie(df["値"], labels=labels, autopct="%1.0f%%",
           pctdistance=0.8, textprops={"fontsize": 8})
    ax.set_title(f"二人以上の世帯の費目別消費支出の構成（{period}）")

    os.makedirs("figures", exist_ok=True)
    out = "figures/ex22_household_spending.pdf"
    fig.savefig(out, bbox_inches="tight")
    print(f"対象: {period}（二人以上の世帯・全国）／ 10費目計: {df['値'].sum():,.0f} 円")
    print(df[["cat01", "値"]].to_string(index=False))
    print(f"→ 円グラフを {out} に保存しました。")


if __name__ == "__main__":
    main()
