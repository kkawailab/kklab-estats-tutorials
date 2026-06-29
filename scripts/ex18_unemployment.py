# /// script
# requires-python = ">=3.11"
# dependencies = ["requests", "pandas", "matplotlib"]
# ///
"""例題18: 完全失業率の月次推移を描く。

労働力調査（統計表ID 0003005865）から、完全失業率（男女総数）の月次系列を
取得し、折れ線グラフにする（原数値）。

実行:
    set -a; source .env; set +a
    uv run scripts/ex18_unemployment.py
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import jpfont  # noqa: F401  matplotlib の日本語フォントを設定（jpfont.py）
import pandas as pd

import estat_api as e

SID = "0003005865"


def main() -> None:
    app_id = e.get_app_id()

    sdata = e.get_stats_data(
        app_id, SID,
        cdTab="02",        # 率(％)
        cdCat01="000",     # 全産業
        cdCat02="08",      # 就業状態: 完全失業者 → 完全失業率
        cdCat03="0",       # 性別: 総数
    )
    df = e.stats_data_to_frame(sdata).sort_values("time_code")
    # 月次コード YYYY00MMMM から年月を作る
    df["年月"] = pd.to_datetime(
        df["time_code"].str[:4] + "-" + df["time_code"].str[-2:], format="%Y-%m", errors="coerce"
    )
    df = df.dropna(subset=["年月"])

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(df["年月"], df["値"], color="#4C72B0", lw=1)
    ax.set_ylabel("完全失業率（％）")
    ax.set_title("完全失業率の推移（月次・原数値）")
    ax.grid(alpha=0.3)

    os.makedirs("figures", exist_ok=True)
    out = "figures/ex18_unemployment.pdf"
    fig.savefig(out, bbox_inches="tight")
    last = df.iloc[-1]
    print(f"取得期間: {df['年月'].min():%Y-%m} 〜 {df['年月'].max():%Y-%m}（{len(df)}か月）")
    print(f"直近の完全失業率: {last['値']}％（{last['年月']:%Y年%m月}）")
    print(f"→ 図を {out} に保存しました。")


if __name__ == "__main__":
    main()
