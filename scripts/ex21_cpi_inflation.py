# /// script
# requires-python = ">=3.11"
# dependencies = ["requests", "pandas", "matplotlib"]
# ///
"""例題21: 消費者物価指数の前年同月比（インフレ率）を描く。

消費者物価指数（2020年基準, 統計表ID 0003427113）の「前年同月比」を、
総合と「生鮮食品を除く総合（コア）」の2系列について取得し、折れ線で比較する。

実行:
    set -a; source .env; set +a
    uv run scripts/ex21_cpi_inflation.py
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import jpfont  # noqa: F401  matplotlib の日本語フォントを設定（jpfont.py）
import pandas as pd

import estat_api as e

SID = "0003427113"


def main() -> None:
    app_id = e.get_app_id()

    sdata = e.get_stats_data(
        app_id, SID,
        cdTab="3",             # 前年同月比
        cdCat01="0001,0161",   # 総合 / 生鮮食品を除く総合
        cdArea="00000",        # 全国
        lvTime="4",            # 月次
        cdTimeFrom="2021000101",
    )
    df = e.stats_data_to_frame(sdata).sort_values("time_code")
    df["年月"] = pd.to_datetime(
        df["time_code"].str[:4] + "-" + df["time_code"].str[8:10], format="%Y-%m", errors="coerce"
    )

    fig, ax = plt.subplots(figsize=(8, 4.5))
    for item, sub in df.groupby("cat01"):
        ax.plot(sub["年月"], sub["値"], marker="", label=item)
    ax.axhline(0, color="gray", lw=0.8)
    ax.axhline(2, color="orange", lw=0.8, ls="--", label="2%目標")
    ax.set_ylabel("前年同月比（％）")
    ax.set_title("消費者物価指数 前年同月比（全国）")
    ax.legend()
    ax.grid(alpha=0.3)

    os.makedirs("figures", exist_ok=True)
    out = "figures/ex21_cpi_inflation.pdf"
    fig.savefig(out, bbox_inches="tight")
    latest = df.sort_values("年月").groupby("cat01").tail(1)
    print("直近の前年同月比：")
    print(latest[["年月", "cat01", "値"]].to_string(index=False))
    print(f"→ 図を {out} に保存しました。")


if __name__ == "__main__":
    main()
