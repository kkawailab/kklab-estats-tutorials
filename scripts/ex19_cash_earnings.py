# /// script
# requires-python = ">=3.11"
# dependencies = ["requests", "pandas", "matplotlib"]
# ///
"""例題19: 毎月勤労統計から現金給与総額の推移を描く。

毎月勤労統計調査（全国調査・実数原表, 統計表ID 0003138108）から、
事業所規模5人以上・調査産業計・就業形態計の現金給与総額（月次）を取得し、
水準と前年同月比を作図する。
※この原表は旧産業分類（2007年改定）に基づくため2010年1月〜2015年11月をカバーする。
  産業分類の改定で系列が分割される実例。最新値は新分類の別表を参照する。

実行:
    set -a; source .env; set +a
    uv run scripts/ex19_cash_earnings.py
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import jpfont  # noqa: F401  matplotlib の日本語フォントを設定（jpfont.py）
import pandas as pd

import estat_api as e

SID = "0003138108"


def main() -> None:
    app_id = e.get_app_id()

    sdata = e.get_stats_data(
        app_id, SID,
        cdTab="741",       # 現金給与総額（円）
        cdCat01="001",     # 性別: 計
        cdCat02="00",      # 就業形態: 計
        cdCat03="T",       # 事業所規模: 5人以上
        cdCat04="TL",      # 産業: 調査産業計
    )
    df = e.stats_data_to_frame(sdata).sort_values("time_code")
    df["年月"] = pd.to_datetime(
        df["time_code"].str[:4] + "-" + df["time_code"].str[-2:], format="%Y-%m", errors="coerce"
    )
    df = df.dropna(subset=["年月"]).reset_index(drop=True)
    df["前年同月比"] = df["値"].pct_change(12) * 100

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
    ax1.plot(df["年月"], df["値"] / 10000, color="#4C72B0", lw=1)
    ax1.set_ylabel("現金給与総額（万円）")
    ax1.set_title("現金給与総額（5人以上・調査産業計）")
    ax1.grid(alpha=0.3)
    ax2.plot(df["年月"], df["前年同月比"], color="#C44E52", lw=1)
    ax2.axhline(0, color="gray", lw=0.8)
    ax2.set_ylabel("前年同月比（％）")
    ax2.grid(alpha=0.3)

    os.makedirs("figures", exist_ok=True)
    out = "figures/ex19_cash_earnings.pdf"
    fig.savefig(out, bbox_inches="tight")
    last = df.iloc[-1]
    print(f"直近 {last['年月']:%Y年%m月}: 現金給与総額 {last['値']:,.0f} 円, "
          f"前年同月比 {last['前年同月比']:+.1f}％")
    print(f"→ 図を {out} に保存しました。")


if __name__ == "__main__":
    main()
