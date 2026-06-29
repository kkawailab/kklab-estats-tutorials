# /// script
# requires-python = ">=3.11"
# dependencies = ["requests", "pandas", "matplotlib"]
# ///
"""例題25: 商業動態統計の業種別商業販売額指数を描く。

商業動態統計調査（確報, 統計表ID 0004026181「業種別商業販売額指数」）から、
商業計・卸売業・小売業の季節調整済指数（月次）を取得して比較する。

実行:
    set -a; source .env; set +a
    uv run scripts/ex25_retail_sales.py
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import jpfont  # noqa: F401
import pandas as pd

import estat_api as e

SID = "0004026181"
WANT = ["商業計", "卸売業計", "小売業計"]


def main() -> None:
    app_id = e.get_app_id()

    sdata = e.get_stats_data(
        app_id, SID,
        cdCat02="01080300",   # 季節調整済指数
        fetch_all=True,
    )
    df = e.stats_data_to_frame(sdata)
    df = df[df["cat01"].isin(WANT)]
    # 月次（YYYY年M月）だけに絞る
    df = df[df["time"].str.contains(r"\d+年\d+月", regex=True)].copy()
    df["年月"] = pd.to_datetime(
        df["time"].str.replace("年", "-").str.replace("月", ""), format="%Y-%m", errors="coerce"
    )
    df = df.dropna(subset=["年月"]).sort_values("年月")

    fig, ax = plt.subplots(figsize=(9, 4))
    for name, sub in df.groupby("cat01"):
        ax.plot(sub["年月"], sub["値"], marker="", label=name)
    ax.set_ylabel("商業販売額指数（2020年=100, 季節調整済）")
    ax.set_title("業種別 商業販売額指数の推移")
    ax.legend()
    ax.grid(alpha=0.3)

    os.makedirs("figures", exist_ok=True)
    out = "figures/ex25_retail_sales.pdf"
    fig.savefig(out, bbox_inches="tight")
    print(f"取得業種: {sorted(df['cat01'].unique())}")
    print(f"期間: {df['年月'].min():%Y-%m} 〜 {df['年月'].max():%Y-%m}")
    print(f"→ 図を {out} に保存しました。")


if __name__ == "__main__":
    main()
