# /// script
# requires-python = ">=3.11"
# dependencies = ["requests", "pandas"]
# ///
"""例題7: 時間軸で絞り込む（cdTimeFrom）。

消費者物価指数（2020年基準, 統計表ID 0003427113）から、「総合」「全国」の
月次指数を 2023年1月以降だけ取得する。時間軸コードの範囲指定（cdTimeFrom）と
階層レベル指定（lvTime=4 で月次のみ）を使う。

実行:
    set -a; source .env; set +a
    uv run scripts/ex07_filter_time.py
"""
import estat_api as e

SID = "0003427113"  # 消費者物価指数（2020年基準）


def main() -> None:
    app_id = e.get_app_id()

    sdata = e.get_stats_data(
        app_id, SID,
        cdCat01="0001",          # 品目: 総合
        cdArea="00000",          # 地域: 全国
        cdTab="1",               # 表章項目: 指数
        lvTime="4",              # 時間軸の階層レベル4 = 月次のみ
        cdTimeFrom="2023000101",  # 2023年1月以降（月次コードは YYYY00MMMM 形式）
    )
    df = e.stats_data_to_frame(sdata).sort_values("time_code")

    print(f"取得した月数: {len(df)} か月")
    print("（消費者物価指数 総合・全国・2020年平均=100, 直近12か月）")
    print(df[["time", "値"]].tail(12).to_string(index=False))


if __name__ == "__main__":
    main()
