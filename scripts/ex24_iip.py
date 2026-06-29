# /// script
# requires-python = ">=3.11"
# dependencies = ["requests", "pandas", "matplotlib"]
# ///
"""例題24: 鉱工業生産指数（IIP）の推移を描く。

鉱工業生産・出荷・在庫指数（2020年基準, 統計表ID 0004052177「業種別季節調整済指数・
付加価値額生産」）から、鉱工業（総合）の生産指数を取得して折れ線にする。

実行:
    set -a; source .env; set +a
    uv run scripts/ex24_iip.py
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import jpfont  # noqa: F401
import pandas as pd

import estat_api as e

SID = "0004052177"


def main() -> None:
    app_id = e.get_app_id()

    sdata = e.get_stats_data(app_id, SID, cdCat01="0001000", fetch_all=True)  # 鉱工業
    df = e.stats_data_to_frame(sdata)

    # この表の「時間軸」は YYYYMM の月次ラベル（「付加生産ウエイト」等の非日付行を除く）
    df = df[df["time"].str.match(r"^\d{6}$")].copy()
    df["年月"] = pd.to_datetime(df["time"], format="%Y%m")
    df = df.sort_values("年月")

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(df["年月"], df["値"], color="#4C72B0", lw=1.2)
    ax.axhline(100, color="gray", lw=0.8, ls="--", label="2020年=100")
    ax.set_ylabel("生産指数（2020年=100, 季節調整済）")
    ax.set_title("鉱工業生産指数の推移")
    ax.legend()
    ax.grid(alpha=0.3)

    os.makedirs("figures", exist_ok=True)
    out = "figures/ex24_iip.pdf"
    fig.savefig(out, bbox_inches="tight")
    last = df.iloc[-1]
    print(f"取得期間: {df['年月'].min():%Y-%m} 〜 {df['年月'].max():%Y-%m}")
    print(f"直近 {last['年月']:%Y年%m月} の鉱工業生産指数: {last['値']}")
    print(f"→ 図を {out} に保存しました。")


if __name__ == "__main__":
    main()
