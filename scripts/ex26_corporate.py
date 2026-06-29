# /// script
# requires-python = ">=3.11"
# dependencies = ["requests", "pandas", "matplotlib"]
# ///
"""例題26: 法人企業統計から経常利益と設備投資の推移を描く。

法人企業統計調査（時系列データ・全産業, 統計表ID 0003061946）から、
全規模・全産業の経常利益と設備投資（四半期）を取得して二軸で作図する。

実行:
    set -a; source .env; set +a
    uv run scripts/ex26_corporate.py
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import jpfont  # noqa: F401

import estat_api as e

SID = "0003061946"


def main() -> None:
    app_id = e.get_app_id()

    sdata = e.get_stats_data(
        app_id, SID,
        cdCat01="086,040",   # 086=経常利益(当期末), 040=設備投資
        cdCat03="26",        # 規模: 全規模
        fetch_all=True,
    )
    df = e.stats_data_to_frame(sdata).sort_values("time_code")
    keiri = df[df["cat01"].str.contains("経常利益")]
    setubi = df[df["cat01"].str.contains("設備投資")]

    x = range(len(keiri))
    fig, ax1 = plt.subplots(figsize=(9, 4.5))
    ax1.bar(x, keiri["値"] / 1e6, color="#8C9EC4", label="経常利益")
    ax1.set_ylabel("経常利益（兆円）")
    ax2 = ax1.twinx()
    ax2.plot(x, setubi["値"].to_numpy() / 1e6, color="#C44E52", label="設備投資")
    ax2.set_ylabel("設備投資（兆円）")
    step = max(1, len(keiri) // 10)
    ax1.set_xticks(list(x)[::step])
    ax1.set_xticklabels(keiri["time"].iloc[::step], rotation=60, fontsize=7)
    ax1.set_title("法人企業統計：経常利益と設備投資（全産業・全規模）")
    fig.legend(loc="upper left", bbox_to_anchor=(0.12, 0.88))

    os.makedirs("figures", exist_ok=True)
    out = "figures/ex26_corporate.pdf"
    fig.savefig(out, bbox_inches="tight")
    last = keiri.iloc[-1]
    print(f"最新 {last['time']}: 経常利益 {last['値'] / 1e6:.1f} 兆円")
    print(f"→ 図を {out} に保存しました。")


if __name__ == "__main__":
    main()
