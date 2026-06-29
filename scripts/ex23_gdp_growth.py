# /// script
# requires-python = ">=3.11"
# dependencies = ["requests", "pandas", "matplotlib"]
# ///
"""例題23: 実質GDP（季節調整系列）から年率換算の成長率を計算する。

四半期別GDP速報の「実質季節調整系列・実額」（統計表ID 0003376098）から
国内総生産（支出側）の四半期系列を取得し、前期比を年率換算して作図する。
　年率換算成長率 = ((GDP_t / GDP_{t-1})^4 - 1) * 100
※この表は公表時点アーカイブ（過去の値）であり、系列の基準年・期間に注意。

実行:
    set -a; source .env; set +a
    uv run scripts/ex23_gdp_growth.py
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import jpfont  # noqa: F401

import estat_api as e

SID = "0003376098"  # 四半期別GDP速報 実質季節調整系列 実額


def main() -> None:
    app_id = e.get_app_id()

    sdata = e.get_stats_data(app_id, SID, fetch_all=True)
    df = e.stats_data_to_frame(sdata)

    # 需要項目（cat01）から「国内総生産(支出側)」の系列だけを取り出す
    g = df[df["cat01"] == "国内総生産(支出側)"].sort_values("time_code").reset_index(drop=True)
    g["年率(%)"] = ((g["値"] / g["値"].shift(1)) ** 4 - 1) * 100

    recent = g.dropna().tail(40)
    fig, ax = plt.subplots(figsize=(9, 4))
    colors = ["#C44E52" if v < 0 else "#4C72B0" for v in recent["年率(%)"]]
    ax.bar(range(len(recent)), recent["年率(%)"], color=colors)
    step = max(1, len(recent) // 10)
    ax.set_xticks(range(0, len(recent), step))
    ax.set_xticklabels(recent["time"].iloc[::step], rotation=60, fontsize=7)
    ax.axhline(0, color="gray", lw=0.8)
    ax.set_ylabel("実質GDP成長率（前期比年率, ％）")
    ax.set_title("実質GDP成長率（季節調整済・前期比年率）")
    ax.grid(axis="y", alpha=0.3)

    os.makedirs("figures", exist_ok=True)
    out = "figures/ex23_gdp_growth.pdf"
    fig.savefig(out, bbox_inches="tight")
    last = g.dropna().iloc[-1]
    print(f"最新 {last['time']}: 実質GDP {last['値']:,.0f} 10億円, 前期比年率 {last['年率(%)']:+.1f}％")
    print(f"→ 図を {out} に保存しました。")


if __name__ == "__main__":
    main()
