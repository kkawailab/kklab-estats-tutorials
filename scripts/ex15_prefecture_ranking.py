# /// script
# requires-python = ">=3.11"
# dependencies = ["requests", "pandas", "matplotlib"]
# ///
"""例題15: 都道府県別人口のランキングを棒グラフにする。

人口推計（統計表ID 0003448232）から最新年の都道府県別総人口を取得し、
上位15都道府県を横棒グラフで表示する。

実行:
    set -a; source .env; set +a
    uv run scripts/ex15_prefecture_ranking.py
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import jpfont  # noqa: F401  matplotlib の日本語フォントを設定（jpfont.py）

import estat_api as e

SID = "0003448232"  # 人口推計 都道府県，男女別人口


def main() -> None:
    app_id = e.get_app_id()

    sdata = e.get_stats_data(app_id, SID,
                             cdTab="001", cdCat01="000", cdCat02="001", lvArea="2")
    df = e.stats_data_to_frame(sdata)
    df = df[df["time_code"] == df["time_code"].max()]
    period = df["time"].iloc[0]

    top = df.sort_values("値", ascending=False).head(15).iloc[::-1]

    fig, ax = plt.subplots(figsize=(7, 6))
    ax.barh(top["area"], top["値"], color="#55A868")
    ax.set_xlabel("人口（千人）")
    ax.set_title(f"都道府県別人口 上位15（{period}）")
    for yi, v in enumerate(top["値"]):
        ax.text(v, yi, f" {v:,.0f}", va="center", fontsize=8)
    ax.grid(axis="x", alpha=0.3)

    os.makedirs("figures", exist_ok=True)
    out = "figures/ex15_prefecture_ranking.pdf"
    fig.savefig(out, bbox_inches="tight")
    print(f"対象年: {period}")
    print(top.sort_values("値", ascending=False)[["area", "値"]].head(5).to_string(index=False))
    print(f"→ ランキング図を {out} に保存しました。")


if __name__ == "__main__":
    main()
