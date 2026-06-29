# /// script
# requires-python = ">=3.11"
# dependencies = ["requests", "pandas", "matplotlib"]
# ///
"""例題14: 国勢調査ベースの人口推計から「人口ピラミッド」を描く。

人口推計（令和2年国勢調査基準, 統計表ID 0003443840）から、男女・年齢5歳階級別の
総人口を取得し、左右対称の人口ピラミッド（横棒グラフ）を作図する。

実行:
    set -a; source .env; set +a
    uv run scripts/ex14_population_pyramid.py
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import jpfont  # noqa: F401  matplotlib の日本語フォントを設定（jpfont.py）

import estat_api as e

SID = "0003443840"  # 人口推計 年齢（5歳階級），男女別人口


def main() -> None:
    app_id = e.get_app_id()

    sdata = e.get_stats_data(
        app_id, SID,
        cdTab="001",           # 人口
        cdCat01="01",          # 確定値
        cdCat02="001,002",     # 男女別: 001=男, 002=女
        cdCat04="001",         # 総人口
    )
    df = e.stats_data_to_frame(sdata)

    # 最新時点・5歳階級だけに絞る（「総数」や「（再掲）…」は二重計上になるので除外）
    df = df[df["time_code"] == df["time_code"].max()]
    df = df[~df["cat03"].str.contains("総数|再掲")].sort_values("cat03_code")
    period = df["time"].iloc[0]

    men = df[df["cat02"] == "男"]
    women = df[df["cat02"] == "女"]
    ages = men["cat03"].tolist()
    y = range(len(ages))

    fig, ax = plt.subplots(figsize=(7, 6))
    ax.barh(y, -men["値"].to_numpy(), color="#4C72B0", label="男")
    ax.barh(y, women["値"].to_numpy(), color="#C44E52", label="女")
    ax.set_yticks(list(y))
    ax.set_yticklabels(ages, fontsize=7)
    ax.set_xlabel("人口（千人）")
    ax.set_title(f"日本の人口ピラミッド（{period}）")
    # x軸の負値を絶対値表示に（男側の符号を隠す）
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{abs(int(x)):,}"))
    ax.legend()
    ax.grid(axis="x", alpha=0.3)

    os.makedirs("figures", exist_ok=True)
    out = "figures/ex14_population_pyramid.pdf"
    fig.savefig(out, bbox_inches="tight")
    total = df["値"].sum()
    print(f"{period} 時点の総人口（男女計）: {total:,.0f} 千人")
    print(f"→ 人口ピラミッドを {out} に保存しました。")


if __name__ == "__main__":
    main()
