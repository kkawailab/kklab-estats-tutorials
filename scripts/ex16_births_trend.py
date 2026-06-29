# /// script
# requires-python = ">=3.11"
# dependencies = ["requests", "pandas", "matplotlib"]
# ///
"""例題16: 出生数と合計特殊出生率の年次推移を描く。

人口動態調査（確定数・出生, 統計表ID 0003411595）から、出生数と合計特殊出生率を
取得し、棒グラフ（出生数）と折れ線（合計特殊出生率）を二軸で重ねて作図する。

実行:
    set -a; source .env; set +a
    uv run scripts/ex16_births_trend.py
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import jpfont  # noqa: F401  matplotlib の日本語フォントを設定（jpfont.py）

import estat_api as e

SID = "0003411595"  # 人口動態調査 出生（年次別）


def main() -> None:
    app_id = e.get_app_id()

    sdata = e.get_stats_data(app_id, SID, cdCat01="00100,00150",
                             cdTimeFrom="1980000000")  # 1980年以降
    df = e.stats_data_to_frame(sdata)
    df["年"] = df["time"].str.replace("年", "").astype(int)

    births = df[df["cat01"] == "出生数_総数"].sort_values("年")
    tfr = df[df["cat01"] == "合計特殊出生率"].sort_values("年")

    fig, ax1 = plt.subplots(figsize=(8, 4.5))
    ax1.bar(births["年"], births["値"] / 10000, color="#8C9EC4", label="出生数")
    ax1.set_ylabel("出生数（万人）")
    ax1.set_xlabel("年")

    ax2 = ax1.twinx()
    ax2.plot(tfr["年"], tfr["値"], color="#C44E52", marker="o", ms=3, label="合計特殊出生率")
    ax2.set_ylabel("合計特殊出生率")

    ax1.set_title("出生数と合計特殊出生率の推移")
    fig.legend(loc="upper right", bbox_to_anchor=(0.9, 0.88))

    os.makedirs("figures", exist_ok=True)
    out = "figures/ex16_births_trend.pdf"
    fig.savefig(out, bbox_inches="tight")
    latest = births.iloc[-1]
    print(f"最新 {latest['年']}年: 出生数 {latest['値']:,.0f} 人, "
          f"合計特殊出生率 {tfr.iloc[-1]['値']}")
    print(f"→ 図を {out} に保存しました。")


if __name__ == "__main__":
    main()
