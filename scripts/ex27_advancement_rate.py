# /// script
# requires-python = ">=3.11"
# dependencies = ["requests", "pandas", "matplotlib"]
# ///
"""例題27: 学校基本調査から進学率の長期推移を描く。

学校基本調査（年次統計, 統計表ID 0003147040「進学率（1948年～）」）から、
高等学校等への進学率と大学・短大等への進学率の長期時系列を取得して作図する。

実行:
    set -a; source .env; set +a
    uv run scripts/ex27_advancement_rate.py
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import jpfont  # noqa: F401

import estat_api as e

SID = "0003147040"


def main() -> None:
    app_id = e.get_app_id()

    sdata = e.get_stats_data(
        app_id, SID,
        cdCat01="0000000010",            # 性別: 計
        cdCat02="0000000020,0000000040",  # 高校等進学率, 大学・短大等への現役進学率
        fetch_all=True,
    )
    df = e.stats_data_to_frame(sdata)
    df["年"] = df["time"].str.extract(r"(\d+)").astype(int)
    df = df.sort_values("年")

    fig, ax = plt.subplots(figsize=(9, 4.5))
    for name, sub in df.groupby("cat02"):
        label = "高校等進学率" if "高等学校" in name else "大学・短大等進学率"
        ax.plot(sub["年"], sub["値"], marker="", label=label)
    ax.set_ylabel("進学率（％）")
    ax.set_xlabel("年")
    ax.set_title("進学率の長期推移")
    ax.legend()
    ax.grid(alpha=0.3)

    os.makedirs("figures", exist_ok=True)
    out = "figures/ex27_advancement_rate.pdf"
    fig.savefig(out, bbox_inches="tight")
    print(f"期間: {df['年'].min()}年 〜 {df['年'].max()}年")
    latest_year = df["年"].max()
    for name, sub in df.groupby("cat02"):
        print(f"  {name[:20]}…: {latest_year}年 = {sub[sub['年'] == latest_year]['値'].iloc[0]}％")
    print(f"→ 図を {out} に保存しました。")


if __name__ == "__main__":
    main()
