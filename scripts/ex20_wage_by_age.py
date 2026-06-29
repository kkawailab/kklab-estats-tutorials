# /// script
# requires-python = ">=3.11"
# dependencies = ["requests", "pandas", "matplotlib"]
# ///
"""例題20: 賃金構造基本統計調査から年齢階級別の賃金プロファイルを描く。

統計表ID 0003029886（一般労働者・産業計）から、男女別・年齢階級別の
「きまって支給する現金給与額」を取得し、年齢に対する賃金カーブを作図する。

実行:
    set -a; source .env; set +a
    uv run scripts/ex20_wage_by_age.py
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import jpfont  # noqa: F401  matplotlib の日本語フォントを設定（jpfont.py）

import estat_api as e

SID = "0003029886"  # 賃金構造基本統計調査 年齢階級別


def main() -> None:
    app_id = e.get_app_id()

    sdata = e.get_stats_data(
        app_id, SID,
        cdTab="40",        # きまって支給する現金給与額（千円）
        cdCat01="01",      # 企業規模計（10人以上）
        cdCat02="02,03",   # 性別: 男, 女
        cdCat03="01",      # 学歴計
        cdCat05="01",      # 産業分類: 産業計
        cdCat06="01",      # 民・公区分: 民営＋公営
    )
    df = e.stats_data_to_frame(sdata)
    if "time_code" in df:  # 年次があれば最新年に
        df = df[df["time_code"] == df["time_code"].max()]
    df = df[df["cat04"] != "年齢計"].sort_values("cat04_code")

    fig, ax = plt.subplots(figsize=(8, 4.5))
    for sex, sub in df.groupby("cat02"):
        ax.plot(sub["cat04"], sub["値"], marker="o", ms=3, label=sex)
    ax.set_ylabel("きまって支給する現金給与額（千円）")
    ax.set_title("年齢階級別の賃金プロファイル（一般労働者・産業計）")
    ax.tick_params(axis="x", labelrotation=60, labelsize=7)
    ax.legend()
    ax.grid(alpha=0.3)

    os.makedirs("figures", exist_ok=True)
    out = "figures/ex20_wage_by_age.pdf"
    fig.savefig(out, bbox_inches="tight")
    peak = df.loc[df["値"].idxmax()]
    print(f"最も賃金が高い区分: {peak['cat02']}・{peak['cat04']} = {peak['値']} 千円")
    print(f"→ 図を {out} に保存しました。")


if __name__ == "__main__":
    main()
