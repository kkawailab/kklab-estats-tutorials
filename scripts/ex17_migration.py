# /// script
# requires-python = ">=3.11"
# dependencies = ["requests", "pandas", "matplotlib"]
# ///
"""例題17: 3大都市圏の転入超過数の推移を描く。

住民基本台帳人口移動報告（統計表ID 0003404102）から、東京圏・名古屋圏・大阪圏の
転入超過数の年次推移を取得し、折れ線グラフで比較する（東京一極集中の可視化）。

実行:
    set -a; source .env; set +a
    uv run scripts/ex17_migration.py
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import jpfont  # noqa: F401  matplotlib の日本語フォントを設定（jpfont.py）

import estat_api as e

SID = "0003404102"  # 住民基本台帳人口移動報告 3大都市圏


def main() -> None:
    app_id = e.get_app_id()

    sdata = e.get_stats_data(
        app_id, SID,
        cdCat01="002,003,004",   # 東京圏・名古屋圏・大阪圏
        cdCat02="003",           # 転入超過数
    )
    df = e.stats_data_to_frame(sdata)
    df["年"] = df["time"].str.extract(r"(\d+)").astype(int)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    for area, sub in df.groupby("cat01"):
        sub = sub.sort_values("年")
        ax.plot(sub["年"], sub["値"] / 10000, marker="", label=area)
    ax.axhline(0, color="gray", lw=0.8)
    ax.set_xlabel("年")
    ax.set_ylabel("転入超過数（万人）")
    ax.set_title("3大都市圏の転入超過数の推移")
    ax.legend()
    ax.grid(alpha=0.3)

    os.makedirs("figures", exist_ok=True)
    out = "figures/ex17_migration.pdf"
    fig.savefig(out, bbox_inches="tight")
    tokyo = df[df["cat01"] == "東京圏"].sort_values("年").iloc[-1]
    print(f"最新 {tokyo['年']}年 東京圏の転入超過数: {tokyo['値']:,.0f} 人")
    print(f"→ 図を {out} に保存しました。")


if __name__ == "__main__":
    main()
